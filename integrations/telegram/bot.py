import os
import logging
import asyncio
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)
from dotenv import load_dotenv

# Import the assistant runner functions
from parsers.unified import (
    parse_task,
    format_task_for_confirmation,
)
from integrations.google_sheets import (
    send_task_to_sheets as send_to_google_sheets,
    get_tasks_from_sheets,
    complete_task_in_sheets,
    restore_task_in_sheets,
)

# --- Configuration ---
load_dotenv()
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN not found in .env file or environment.")
    exit()

# Enable logging - both console and file
LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "telegram_bot.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# --- Bot State ---
# No longer need assistant - using unified parser

# Conversation states
AWAITING_TASK_DESCRIPTION = 1
AWAITING_CLARIFICATION = 2

# Callback data constants
NEW_TASK = "new_task"
LIST_TASKS = "list_tasks"
SUBMIT_TASK = "submit_task"
CLARIFY_TASK = "clarify_task"
CANCEL_TASK = "cancel_task"
COMPLETE_TASK_PREFIX = "complete_task_"
REFRESH_TASKS = "refresh_tasks"
UNDO_LAST = "undo_last"
MAIN_MENU = "main_menu"


# --- User Management ---
def get_system_user_from_telegram(telegram_user):
    """Map Telegram user to system user name."""
    # Map based on Telegram username or user ID
    # This is a simple mapping - in production you'd use a database
    user_mapping = {
        "colinaulds": "Colin",
        "Colin_10NetZero": "Colin",  # Add the actual username
        "bryanaulds": "Bryan",
        "joelfulford": "Joel",
        # Add first name mappings as fallbacks
        "colin": "Colin",
        "bryan": "Bryan",
        "joel": "Joel",
        # Add display name variations
        "colin aulds": "Colin",
        "bryan aulds": "Bryan",
        "joel fulford": "Joel",
        # Handle full display names with company info
        "colin aulds | 10netzero.com": "Colin",
    }

    # Try username first
    if telegram_user.username:
        username_lower = telegram_user.username.lower()
        if username_lower in user_mapping:
            return user_mapping[username_lower]
        # Check exact match (case-sensitive)
        if telegram_user.username in user_mapping:
            return user_mapping[telegram_user.username]

    # Then try first name (might include company info)
    if telegram_user.first_name:
        first_name_lower = telegram_user.first_name.lower()
        if first_name_lower in user_mapping:
            return user_mapping[first_name_lower]

        # Try just the first word of the first name
        first_word = first_name_lower.split()[0] if first_name_lower else ""
        if first_word in user_mapping:
            return user_mapping[first_word]

    # Fallback to first name if no mapping found, capitalize for consistency
    first_name = telegram_user.first_name or "unknown"
    # If first name has company info, extract just the name
    first_name = first_name.split("|")[0].strip()
    first_word = first_name.split()[0] if first_name else "unknown"
    return first_word.capitalize()


# --- Keyboard Helpers ---
def get_user_task_count(user_id, context=None):
    """Get the number of active tasks for a user."""
    # If we have tasks in context, count the active ones
    if context and "user_tasks" in context.user_data:
        tasks = context.user_data["user_tasks"]
        return len(
            [task for task in tasks if task.get("status") in ["pending", "active"]]
        )

    # Get real count from Google Sheets
    try:
        telegram_user = context.user_data.get("telegram_user") if context else None
        if telegram_user:
            system_user = get_system_user_from_telegram(telegram_user)
            tasks = get_tasks_from_sheets(assignee=system_user)
            return len(tasks)
    except Exception as e:
        logger.error(f"Error getting task count: {e}")

    return 0


def get_main_menu_keyboard(task_count=None):
    """Create the main menu inline keyboard."""
    # Format the List Tasks button with count if provided
    if task_count is not None and task_count > 0:
        list_button_text = f"📋 List Tasks ({task_count})"
    else:
        list_button_text = "📋 List Tasks"

    keyboard = [
        [
            InlineKeyboardButton("➕ New Task", callback_data=NEW_TASK),
            InlineKeyboardButton(list_button_text, callback_data=LIST_TASKS),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_task_confirmation_keyboard():
    """Create the task confirmation inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Submit", callback_data=SUBMIT_TASK),
            InlineKeyboardButton("✏️ Clarify", callback_data=CLARIFY_TASK),
            InlineKeyboardButton("❌ Cancel", callback_data=CANCEL_TASK),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_task_list_keyboard(tasks):
    """Create inline keyboard for task list with complete buttons."""
    keyboard = []

    # Add a complete button for each task
    for i, task in enumerate(tasks, 1):
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"✅ Complete Task {i}",
                    callback_data=f"{COMPLETE_TASK_PREFIX}{task.get('id', i)}",
                )
            ]
        )

    # Add navigation buttons at the bottom
    keyboard.append(
        [
            InlineKeyboardButton("➕ New Task", callback_data=NEW_TASK),
            InlineKeyboardButton("🔄 Refresh", callback_data=REFRESH_TASKS),
        ]
    )
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data=MAIN_MENU)])

    return InlineKeyboardMarkup(keyboard)


async def show_task_list(query, context=None):
    """Display the user's task list with complete buttons."""
    # Extract just the first name for display (in case of "Colin Aulds | Company")
    full_name = query.from_user.first_name or ""
    user_name = full_name.split()[0] if full_name else "User"

    # Debug logging
    logger.info("[DEBUG] show_task_list - telegram user info:")
    logger.info(f"  username: {query.from_user.username}")
    logger.info(f"  first_name: {query.from_user.first_name}")
    logger.info(f"  full_name: {full_name}")

    system_user = get_system_user_from_telegram(query.from_user)
    logger.info(f"  mapped to system_user: {system_user}")

    try:
        # Fetch real tasks from Google Sheets for this user
        tasks = get_tasks_from_sheets(assignee=system_user)

        # Store tasks in context for button functionality
        if context:
            context.user_data["user_tasks"] = tasks
            context.user_data["telegram_user"] = query.from_user

    except Exception as e:
        logger.error(f"Error fetching tasks from sheets: {e}")
        tasks = []

    # Filter only active/pending tasks
    active_tasks = [
        task for task in tasks if task.get("status") in ["pending", "active"]
    ]

    if not active_tasks:
        task_text = (
            f"🎉 Great job {user_name}! No active tasks.\n\nWhat would you like to do?"
        )
        keyboard = get_main_menu_keyboard(0)
    else:
        task_text = f"📋 Your Active Tasks ({len(active_tasks)}):\n\n"

        for i, task in enumerate(active_tasks, 1):
            task_desc = task.get("task", "No description")
            due_date = task.get("due_date", "No date")
            due_time = task.get("due_time", "")
            assigner = task.get("assigner", "Unknown")
            site = task.get("site", "")

            # Format due time
            due_str = due_date
            if due_time:
                due_str += f" at {due_time}"

            task_text += f"{i}. {task_desc}\n"
            task_text += f"   🕐 {due_str} | Assigned by: {assigner}"
            if site:
                task_text += f" | 📍 {site}"
            task_text += "\n\n"

        task_text += f"\nShowing tasks for: {system_user}"
        keyboard = get_task_list_keyboard(active_tasks)

    # Send new message instead of editing to preserve context
    await query.message.reply_text(
        task_text,
        reply_markup=keyboard,
    )


# --- Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user_id = update.effective_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    logger.info(f"User {user_id} ({username}) started the bot")

    # Store user info in context
    context.user_data["telegram_user"] = update.message.from_user

    # Get user's task count for the main menu
    task_count = get_user_task_count(user_id, context)

    await update.message.reply_text(
        "Welcome to TaskBot! I help you manage tasks for your team.\n\n"
        "What would you like to do?",
        reply_markup=get_main_menu_keyboard(task_count),
    )


async def handle_task_description(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handles incoming task descriptions and parses them."""
    user_message = update.message.text
    username = update.message.from_user.username or update.message.from_user.first_name
    logger.info(f"Received task description from {username}: {user_message}")

    await update.message.reply_text(f"Processing your request: '{user_message}'...")

    try:
        # Run the parsing function in a separate thread to avoid blocking the bot
        logger.info("Starting parse_task in executor...")
        loop = asyncio.get_running_loop()

        # Add timeout to prevent hanging
        # Get the assigner from telegram user
        assigner = get_system_user_from_telegram(update.message.from_user)
        logger.info(
            f"Calling parse_task with message='{user_message}', assigner='{assigner}'"
        )
        parsed_json = await asyncio.wait_for(
            loop.run_in_executor(None, parse_task, user_message, assigner),
            timeout=30.0,  # 30 second timeout
        )
        logger.info(f"parse_task completed successfully: {parsed_json}")

        # Store the parsed JSON in context for later use
        context.user_data["parsed_json"] = parsed_json
        context.user_data["original_message"] = user_message

        # Format the task for confirmation
        formatted_task = format_task_for_confirmation(parsed_json)

        # Ask for confirmation with buttons
        confirmation_message = (
            f"I've parsed your task:\n\n{formatted_task}\n\nWhat would you like to do?"
        )
        await update.message.reply_text(
            confirmation_message, reply_markup=get_task_confirmation_keyboard()
        )

        return AWAITING_TASK_DESCRIPTION  # Stay in same state for button handling

    except asyncio.TimeoutError:
        logger.error("parse_task timed out after 30 seconds")
        await update.message.reply_text(
            "❌ Request timed out. The OpenAI API might be slow. Please try again."
        )
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error processing task: {e}", exc_info=True)
        await update.message.reply_text(f"❌ An error occurred: {e}")
        return ConversationHandler.END


async def handle_confirmation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handles the user's confirmation response."""
    response = update.message.text.lower().strip()
    logger.info(f"Received confirmation response: {response}")

    if response in ["yes", "y", "confirm", "ok", "correct"]:
        # User confirmed - send to Google Sheets
        parsed_json = context.user_data.get("parsed_json")
        if not parsed_json:
            await update.message.reply_text(
                "❌ Error: No task data found. Please try again."
            )
            return ConversationHandler.END

        try:
            await update.message.reply_text("📤 Sending task to Google Sheets...")
            loop = asyncio.get_running_loop()
            success = await loop.run_in_executor(
                None, send_to_google_sheets, parsed_json
            )

            if success:
                await update.message.reply_text("✅ Task created successfully!")
            else:
                await update.message.reply_text(
                    "❌ Failed to send task to Google Sheets. Please try again."
                )

        except Exception as e:
            logger.error(f"Error sending to Google Sheets: {e}", exc_info=True)
            await update.message.reply_text(f"❌ An error occurred: {e}")

        return ConversationHandler.END

    elif response in ["no", "n", "cancel", "stop"]:
        # User cancelled
        await update.message.reply_text(
            "❌ Task cancelled. Send me a new task when you're ready."
        )
        return ConversationHandler.END

    else:
        # User wants to clarify/modify
        clarification = update.message.text
        context.user_data["clarification"] = clarification
        await update.message.reply_text(
            "📝 I'll update the task based on your feedback. Processing..."
        )

        # Track correction history
        corrections_history = context.user_data.get("corrections_history", [])

        # Combine original message with clarification
        original = context.user_data.get("original_message", "")
        combined_message = f"{original}. User clarification: {clarification}"

        try:
            loop = asyncio.get_running_loop()
            assigner = get_system_user_from_telegram(update.message.from_user)
            parsed_json = await loop.run_in_executor(
                None, parse_task, combined_message, assigner
            )

            # Add to corrections history
            correction_entry = {
                "user_correction": clarification,
                "bot_response": format_task_for_confirmation(parsed_json),
                "timestamp": datetime.now().isoformat(),
            }
            corrections_history.append(correction_entry)

            # Store correction history in parsed JSON
            parsed_json["corrections_history"] = json.dumps(corrections_history)

            # Store the updated parsed JSON and history
            context.user_data["parsed_json"] = parsed_json
            context.user_data["corrections_history"] = corrections_history

            # Format and show the updated task with buttons
            formatted_task = format_task_for_confirmation(parsed_json)
            confirmation_message = f"I've updated the task:\n\n{formatted_task}\n\nWhat would you like to do?"
            await update.message.reply_text(
                confirmation_message, reply_markup=get_task_confirmation_keyboard()
            )

            return AWAITING_TASK_DESCRIPTION

        except Exception as e:
            logger.error(f"Error reprocessing task: {e}", exc_info=True)
            await update.message.reply_text(
                f"❌ An error occurred while updating the task: {e}"
            )
            return ConversationHandler.END


async def handle_button_click(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle inline keyboard button clicks."""
    query = update.callback_query
    await query.answer()

    logger.info(f"Button clicked: {query.data}")

    if query.data == NEW_TASK:
        await query.edit_message_text("Please describe the task:")
        return AWAITING_TASK_DESCRIPTION

    elif query.data == LIST_TASKS or query.data == REFRESH_TASKS:
        await show_task_list(query, context)
        return ConversationHandler.END

    elif query.data == SUBMIT_TASK:
        # User confirmed - send to Google Sheets
        parsed_json = context.user_data.get("parsed_json")
        if not parsed_json:
            await query.edit_message_text(
                "❌ Error: No task data found. Please try again."
            )
            return ConversationHandler.END

        try:
            await query.edit_message_text("📤 Sending task to Google Sheets...")
            loop = asyncio.get_running_loop()
            success = await loop.run_in_executor(
                None, send_to_google_sheets, parsed_json
            )

            if success:
                user_id = query.from_user.id
                task_count = get_user_task_count(user_id, context)

                await query.edit_message_text(
                    "✅ Task successfully created!\n\nWhat would you like to do?",
                    reply_markup=get_main_menu_keyboard(task_count),
                )
            else:
                await query.edit_message_text(
                    "❌ Failed to send task to Google Sheets. Please try again."
                )

        except Exception as e:
            logger.error(f"Error sending task to sheets: {e}", exc_info=True)
            await query.edit_message_text(
                f"❌ An error occurred while saving the task: {e}"
            )

        return ConversationHandler.END

    elif query.data == CLARIFY_TASK:
        # Create clarification keyboard with cancel option
        clarification_keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Cancel", callback_data=CANCEL_TASK)]]
        )

        # Send new message instead of editing to preserve confirmation
        await query.message.reply_text(
            "Please describe what needs to be changed:",
            reply_markup=clarification_keyboard,
        )
        return AWAITING_CLARIFICATION

    elif query.data == CANCEL_TASK:
        user_id = query.from_user.id
        task_count = get_user_task_count(user_id, context)

        await query.edit_message_text(
            "❌ Task cancelled.\n\nWhat would you like to do?",
            reply_markup=get_main_menu_keyboard(task_count),
        )
        return ConversationHandler.END

    elif query.data.startswith(COMPLETE_TASK_PREFIX):
        # Extract task ID from callback data
        task_id = query.data.replace(COMPLETE_TASK_PREFIX, "")

        # Get the completing user
        system_user = get_system_user_from_telegram(query.from_user)

        # Find the task being completed
        completed_task_name = "Task"
        if "user_tasks" in context.user_data:
            tasks = context.user_data["user_tasks"]
            for task in tasks:
                if task["id"] == task_id:
                    completed_task_name = task.get("task", "Task")
                    # Update local status for immediate UI feedback
                    task["status"] = "completed"
                    # Store the completed task for undo
                    context.user_data["last_completed_task"] = {
                        "task": task,
                        "timestamp": update.callback_query.message.date,
                    }
                    break

        # Update task status in Google Sheets
        try:
            success = complete_task_in_sheets(task_id, system_user, "telegram_button")
            if not success:
                logger.error(f"Failed to complete task {task_id} in sheets")
        except Exception as e:
            logger.error(f"Error completing task in sheets: {e}")

        confirmation_text = f"✅ '{completed_task_name}' marked as complete!"

        # Create undo keyboard
        undo_keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "↩️ Undo", callback_data=f"{UNDO_LAST}_{task_id}"
                    ),
                    InlineKeyboardButton("📋 Back to Tasks", callback_data=LIST_TASKS),
                ]
            ]
        )

        await query.edit_message_text(
            confirmation_text,
            reply_markup=undo_keyboard,
        )
        return ConversationHandler.END

    elif query.data.startswith(UNDO_LAST):
        # Extract task ID from undo callback
        task_id = query.data.split("_")[-1]

        # Get the restoring user
        system_user = get_system_user_from_telegram(query.from_user)

        # Restore the task locally for immediate UI feedback
        if "user_tasks" in context.user_data:
            tasks = context.user_data["user_tasks"]
            for task in tasks:
                if task["id"] == task_id:
                    task["status"] = "pending"  # Restore to pending status
                    break

        # Restore task status in Google Sheets
        try:
            success = restore_task_in_sheets(task_id, system_user)
            if not success:
                logger.error(f"Failed to restore task {task_id} in sheets")
        except Exception as e:
            logger.error(f"Error restoring task in sheets: {e}")

        await query.answer("↩️ Task restored!")

        # Show the updated task list
        await show_task_list(query, context)
        return ConversationHandler.END

    elif query.data == "main_menu" or query.data == MAIN_MENU:
        user_id = query.from_user.id
        task_count = get_user_task_count(user_id, context)

        await query.edit_message_text(
            "What would you like to do?",
            reply_markup=get_main_menu_keyboard(task_count),
        )
        return ConversationHandler.END

    # Unknown callback data
    await query.edit_message_text("Unknown action. Returning to main menu.")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the current conversation."""
    await update.message.reply_text(
        "❌ Task cancelled. Send me a new task when you're ready."
    )
    return ConversationHandler.END


def main() -> None:
    """Start the bot."""

    logger.info("Starting Telegram bot...")
    logger.info(
        f"Bot token: {TELEGRAM_BOT_TOKEN[:10]}...{TELEGRAM_BOT_TOKEN[-10:]}"
    )  # Log partial token for debugging

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # No need to initialize assistant anymore - using unified parser
    logger.info("Using unified parser with OpenAI Chat Completions API")

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # Add callback query handler for button clicks
    application.add_handler(CallbackQueryHandler(handle_button_click))

    # Create conversation handler for task processing
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task_description)
        ],
        states={
            AWAITING_TASK_DESCRIPTION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, handle_task_description
                ),
                CallbackQueryHandler(handle_button_click),
            ],
            AWAITING_CLARIFICATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_confirmation),
                CallbackQueryHandler(handle_button_click),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    logger.info("Starting bot polling...")
    try:
        application.run_polling()
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
