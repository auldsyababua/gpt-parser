import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from dotenv import load_dotenv

# Import the assistant runner functions
from assistants_api_runner import (
    get_or_create_assistant,
    parse_task,
    format_task_for_confirmation,
    send_to_google_sheets,
)

# --- Configuration ---
load_dotenv()
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN not found in .env file or environment.")
    exit()

# Enable logging
LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "telegram_bot.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# --- Bot State ---
assistant = None

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


def get_user_task_count(user_id, context=None):
    """Get the number of active tasks for a user."""
    # If we have tasks in context, count the active ones
    if context and "user_tasks" in context.user_data:
        tasks = context.user_data["user_tasks"]
        return len([task for task in tasks if task.get("status") == "active"])

    # TODO: Query actual database/sheets for real count
    # For now, return example count
    return 3  # This would be a real query in production


async def show_task_list(query, context=None):
    """Display the user's task list with complete buttons."""
    # TODO: Fetch real tasks from database/sheets where assignee = current user
    # For now, using example tasks

    user_name = query.from_user.first_name
    user_id = query.from_user.id

    # Get tasks from context if available (for undo functionality)
    if context and "user_tasks" in context.user_data:
        tasks = context.user_data["user_tasks"]
    else:
        # Example tasks - in production, these would come from the database
        tasks = [
            {
                "id": "task_001",
                "description": "Check oil at Site B",
                "due": "Tomorrow 4:00 PM",
                "assigner": "Colin",
                "status": "active",
            },
            {
                "id": "task_002",
                "description": "Inspect generator coolant",
                "due": "Today 5:00 PM",
                "assigner": "yourself",
                "status": "active",
            },
            {
                "id": "task_003",
                "description": "Review maintenance logs",
                "due": "Friday 6:00 PM",
                "assigner": "Bryan",
                "status": "active",
            },
        ]
        # Store tasks in context for undo functionality
        if context:
            context.user_data["user_tasks"] = tasks

    # Filter only active tasks
    active_tasks = [task for task in tasks if task.get("status") == "active"]

    if not active_tasks:
        task_text = (
            f"🎉 Great job {user_name}! No active tasks.\n\nWhat would you like to do?"
        )
        keyboard = get_main_menu_keyboard(0)
    else:
        task_text = f"📋 Your Active Tasks ({len(active_tasks)}):\n\n"

        for i, task in enumerate(active_tasks, 1):
            task_text += f"{i}. {task['description']}\n"
            task_text += f"   🕐 {task['due']} | Assigned by: {task['assigner']}\n\n"

        task_text += f"\nShowing tasks for: {user_name}"
        keyboard = get_task_list_keyboard(active_tasks)

    await query.edit_message_text(
        task_text,
        reply_markup=keyboard,
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user_id = update.effective_user.id
    logger.info(f"User {user_id} started the bot")

    # Get user's task count for the main menu
    task_count = get_user_task_count(user_id, context)

    await update.message.reply_text(
        "Welcome to TaskBot! I help you manage tasks for your team.\n\n"
        "What would you like to do?",
        reply_markup=get_main_menu_keyboard(task_count),
    )


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

    elif query.data.startswith(COMPLETE_TASK_PREFIX):
        # Extract task ID from callback data
        task_id = query.data.replace(COMPLETE_TASK_PREFIX, "")

        # Get current tasks and mark the specified one as complete
        if "user_tasks" in context.user_data:
            tasks = context.user_data["user_tasks"]
            for task in tasks:
                if task["id"] == task_id:
                    task["status"] = "completed"
                    # Store the completed task for undo
                    context.user_data["last_completed_task"] = {
                        "task": task,
                        "timestamp": update.callback_query.message.date,
                    }
                    break

        # TODO: Update task status in database/sheets

        # Show completion confirmation with undo option
        completed_task_name = next(
            (
                task["description"]
                for task in context.user_data.get("user_tasks", [])
                if task["id"] == task_id
            ),
            "Task",
        )

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

        # Restore the task from completed back to active
        if "user_tasks" in context.user_data:
            tasks = context.user_data["user_tasks"]
            for task in tasks:
                if task["id"] == task_id:
                    task["status"] = "active"
                    break

        # TODO: Update task status in database/sheets

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

    elif query.data == SUBMIT_TASK:
        # Submit the task
        task_data = context.user_data.get("pending_task")
        if task_data:
            try:
                # Send to Google Sheets
                result = send_to_google_sheets(task_data)
                if result["success"]:
                    await query.edit_message_text(
                        "✅ Task created successfully!\n\nWhat would you like to do?",
                        reply_markup=get_main_menu_keyboard(),
                    )
                else:
                    await query.edit_message_text(
                        f"❌ Error creating task: {result.get('error', 'Unknown error')}\n\n"
                        "What would you like to do?",
                        reply_markup=get_main_menu_keyboard(),
                    )
            except Exception as e:
                logger.error(f"Error submitting task: {e}")
                await query.edit_message_text(
                    "❌ An error occurred while creating the task.\n\n"
                    "What would you like to do?",
                    reply_markup=get_main_menu_keyboard(),
                )
        return ConversationHandler.END

    elif query.data == CLARIFY_TASK:
        await query.edit_message_text("Please tell me what should be changed:")
        return AWAITING_CLARIFICATION

    elif query.data == CANCEL_TASK:
        await query.edit_message_text(
            "❌ Task cancelled.\n\nWhat would you like to do?",
            reply_markup=get_main_menu_keyboard(),
        )
        return ConversationHandler.END


async def handle_task_description(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle the task description from the user."""
    user_input = update.message.text
    logger.info(f"Received task description: {user_input}")

    try:
        # Initialize assistant if needed
        global assistant
        if not assistant:
            assistant = await get_or_create_assistant()
            logger.info("Assistant initialized successfully")

        # Parse the task
        await update.message.reply_text("Processing your request...")
        parsed_task = await parse_task(user_input, assistant.id)

        if parsed_task:
            # Store the parsed task in context
            context.user_data["pending_task"] = parsed_task
            context.user_data["original_input"] = user_input

            # Format and show confirmation
            confirmation_text = format_task_for_confirmation(parsed_task)
            await update.message.reply_text(
                confirmation_text,
                reply_markup=get_task_confirmation_keyboard(),
            )
        else:
            await update.message.reply_text(
                "❌ I couldn't understand that task. Please try again.\n\n"
                "What would you like to do?",
                reply_markup=get_main_menu_keyboard(),
            )
            return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error processing task: {e}")
        await update.message.reply_text(
            "❌ An error occurred while processing your request.\n\n"
            "What would you like to do?",
            reply_markup=get_main_menu_keyboard(),
        )
        return ConversationHandler.END

    # Wait for button click - no state change needed
    return ConversationHandler.END


async def handle_clarification(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle clarification input from the user."""
    clarification = update.message.text
    original_input = context.user_data.get("original_input", "")

    # Combine original input with clarification
    updated_input = f"{original_input}. {clarification}"
    logger.info(f"Processing clarification: {updated_input}")

    try:
        # Re-parse with clarification
        await update.message.reply_text("Processing your updated request...")
        parsed_task = await parse_task(updated_input, assistant.id)

        if parsed_task:
            # Update stored task
            context.user_data["pending_task"] = parsed_task
            context.user_data["original_input"] = updated_input

            # Show updated confirmation
            confirmation_text = format_task_for_confirmation(parsed_task)
            await update.message.reply_text(
                confirmation_text,
                reply_markup=get_task_confirmation_keyboard(),
            )
        else:
            await update.message.reply_text(
                "❌ I still couldn't understand the task. Let's start over.\n\n"
                "What would you like to do?",
                reply_markup=get_main_menu_keyboard(),
            )
            return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error processing clarification: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Let's start over.\n\n" "What would you like to do?",
            reply_markup=get_main_menu_keyboard(),
        )
        return ConversationHandler.END

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current conversation."""
    await update.message.reply_text(
        "Operation cancelled.\n\nWhat would you like to do?",
        reply_markup=get_main_menu_keyboard(),
    )
    return ConversationHandler.END


async def handle_text_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle text messages outside of conversation."""
    # Treat any text message as a task description
    context.user_data["direct_message"] = True
    return await handle_task_description(update, context)


def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handler
    application.add_handler(CommandHandler("start", start))

    # Add conversation handler for task creation
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(handle_button_click, pattern=f"^{NEW_TASK}$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message),
        ],
        states={
            AWAITING_TASK_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task_description)
            ],
            AWAITING_CLARIFICATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_clarification)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    application.add_handler(conv_handler)

    # Add callback query handler for all buttons
    application.add_handler(CallbackQueryHandler(handle_button_click))

    # Run the bot
    logger.info("Starting bot...")
    application.run_polling()


if __name__ == "__main__":
    main()
