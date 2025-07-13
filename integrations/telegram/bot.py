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
FILTER_TODAY = "filter_today"
FILTER_WEEK = "filter_week"
FILTER_ALL = "filter_all"
TOGGLE_TASK_PREFIX = "toggle_task_"
COMPLETE_SELECTED = "complete_selected"
CLEAR_SELECTION = "clear_selection"


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


def filter_tasks_by_date(tasks, filter_type):
    """Filter tasks by date range."""
    from datetime import datetime, date, timedelta
    
    if filter_type == "all":
        return tasks
    
    today = date.today()
    filtered_tasks = []
    
    for task in tasks:
        due_date_str = task.get("due_date")
        if not due_date_str:
            # Tasks without due date only appear in "all" filter
            continue
            
        try:
            # Parse date string (format: "MM/DD/YYYY")
            due_date = datetime.strptime(due_date_str, "%m/%d/%Y").date()
            
            if filter_type == "today":
                if due_date == today:
                    filtered_tasks.append(task)
            elif filter_type == "week":
                # Include tasks from today through next 7 days
                week_end = today + timedelta(days=7)
                if today <= due_date <= week_end:
                    filtered_tasks.append(task)
                    
        except (ValueError, TypeError):
            # Skip tasks with invalid date format
            logger.warning(f"Skipping task with invalid due_date: {due_date_str}")
            continue
    
    return filtered_tasks


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


def get_filter_keyboard(current_filter="all"):
    """Create inline keyboard for date range filtering."""
    # Highlight active filter
    today_text = "📅 Today" if current_filter != "today" else "✅ Today"
    week_text = "📆 This Week" if current_filter != "week" else "✅ This Week"
    all_text = "📋 All Tasks" if current_filter != "all" else "✅ All Tasks"
    
    keyboard = [
        [
            InlineKeyboardButton(today_text, callback_data=FILTER_TODAY),
            InlineKeyboardButton(week_text, callback_data=FILTER_WEEK),
            InlineKeyboardButton(all_text, callback_data=FILTER_ALL),
        ],
        [InlineKeyboardButton("↩️ Back to Tasks", callback_data=LIST_TASKS)]
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


def get_task_list_keyboard_with_checkboxes(tasks, selected_tasks=None):
    """Create inline keyboard for task list with checkbox-style selection."""
    if selected_tasks is None:
        selected_tasks = set()
    
    keyboard = []

    # Create simple checkbox buttons for each task
    for i, task in enumerate(tasks, 1):
        task_id = task.get('id', '')
        is_selected = task_id in selected_tasks
        
        # Checkbox emoji based on selection state
        checkbox = "✅" if is_selected else "⬜"
        
        # Simple button text with task number
        button_text = f"{checkbox} Task {i}"
        
        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f"{TOGGLE_TASK_PREFIX}{task_id}"
            )
        ])

    # Always show action buttons (with count and disabled state handling)
    selected_count = len(selected_tasks)
    keyboard.append([
        InlineKeyboardButton(
            f"✅ Complete Selected ({selected_count})",
            callback_data=COMPLETE_SELECTED if selected_count > 0 else "no_selection"
        ),
        InlineKeyboardButton(
            "❌ Clear",
            callback_data=CLEAR_SELECTION if selected_count > 0 else "no_selection"
        )
    ])

    # Add navigation buttons at the bottom
    keyboard.append(
        [
            InlineKeyboardButton("➕ New Task", callback_data=NEW_TASK),
            InlineKeyboardButton("🔄 Refresh", callback_data=REFRESH_TASKS),
        ]
    )
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data=MAIN_MENU)])

    return InlineKeyboardMarkup(keyboard)


async def show_task_list(query, context=None, filter_type=None):
    """Display the user's task list with complete buttons and date filtering."""
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

    # Store filter preference in context
    if filter_type is None:
        filter_type = context.user_data.get("task_filter", "all")
    else:
        context.user_data["task_filter"] = filter_type
    
    # Filter only active/pending tasks
    active_tasks = [
        task for task in tasks if task.get("status") in ["pending", "active"]
    ]
    
    # Apply date filtering
    logger.info(f"Applying filter: {filter_type}")
    logger.info(f"Active tasks before filtering: {len(active_tasks)}")
    filtered_tasks = filter_tasks_by_date(active_tasks, filter_type)
    logger.info(f"Filtered tasks after filtering: {len(filtered_tasks)}")
    
    # Build header based on filter
    if filter_type == "today":
        header = f"📅 Today's Tasks ({len(filtered_tasks)})"
    elif filter_type == "week":
        header = f"📆 This Week's Tasks ({len(filtered_tasks)})"
    else:
        header = f"📋 All Active Tasks ({len(filtered_tasks)})"

    if not filtered_tasks:
        # Generate appropriate message based on filter
        if filter_type == "today":
            no_tasks_msg = f"🎉 Great job {user_name}! No tasks due today."
        elif filter_type == "week":
            no_tasks_msg = f"🎉 Great job {user_name}! No tasks due this week."
        else:
            no_tasks_msg = f"🎉 Great job {user_name}! All tasks completed."
        
        task_text = f"{no_tasks_msg}\n\nWhat would you like to do?"
        
        # Send the message with main menu
        await query.message.reply_text(
            task_text,
            reply_markup=get_main_menu_keyboard(0),
        )
        
        # Then send filter options
        filter_text = "📊 Or try a different filter:"
        await query.message.reply_text(
            filter_text,
            reply_markup=get_filter_keyboard(filter_type),
        )
        return
    else:
        task_text = f"{header}:\n\n"

        for i, task in enumerate(filtered_tasks, 1):
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
        
        # Initialize selected tasks if not exists
        if "selected_tasks" not in context.user_data:
            context.user_data["selected_tasks"] = set()
        
        selected_tasks = context.user_data["selected_tasks"]
        
        # Send the task list with checkbox-style selection
        await query.message.reply_text(
            task_text,
            reply_markup=get_task_list_keyboard_with_checkboxes(filtered_tasks, selected_tasks),
        )
        
        # Then send the filter options
        filter_text = "📊 Filter by:"
        await query.message.reply_text(
            filter_text,
            reply_markup=get_filter_keyboard(filter_type),
        )
        return


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

    elif query.data == FILTER_TODAY:
        await show_task_list(query, context, filter_type="today")
        return ConversationHandler.END

    elif query.data == FILTER_WEEK:
        await show_task_list(query, context, filter_type="week")
        return ConversationHandler.END

    elif query.data == FILTER_ALL:
        await show_task_list(query, context, filter_type="all")
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

    elif query.data.startswith(TOGGLE_TASK_PREFIX):
        # Toggle task selection state
        task_id = query.data.replace(TOGGLE_TASK_PREFIX, "")
        
        # Get or initialize selected tasks
        selected_tasks = context.user_data.get("selected_tasks", set())
        
        # Toggle selection
        if task_id in selected_tasks:
            selected_tasks.remove(task_id)
        else:
            selected_tasks.add(task_id)
        
        # Store updated selection
        context.user_data["selected_tasks"] = selected_tasks
        
        # Get current task list from context
        tasks = context.user_data.get("user_tasks", [])
        
        # Filter active tasks based on current filter
        filter_type = context.user_data.get("task_filter", "all")
        active_tasks = [t for t in tasks if t.get("status") in ["pending", "active"]]
        filtered_tasks = filter_tasks_by_date(active_tasks, filter_type)
        
        # Edit the message with updated keyboard
        await query.edit_message_reply_markup(
            reply_markup=get_task_list_keyboard_with_checkboxes(filtered_tasks, selected_tasks)
        )
        return ConversationHandler.END

    elif query.data == COMPLETE_SELECTED:
        # Complete all selected tasks
        selected_tasks = context.user_data.get("selected_tasks", set())
        if not selected_tasks:
            await query.answer("No tasks selected")
            return ConversationHandler.END
        
        system_user = get_system_user_from_telegram(query.from_user)
        tasks = context.user_data.get("user_tasks", [])
        
        completed_count = 0
        completed_names = []
        
        # Complete each selected task
        for task in tasks:
            task_id = task.get('id')
            if task_id in selected_tasks:
                try:
                    success = complete_task_in_sheets(task_id, system_user, "telegram_button")
                    if success:
                        task["status"] = "completed"
                        completed_count += 1
                        completed_names.append(task.get("task", "Task"))
                except Exception as e:
                    logger.error(f"Error completing task {task_id}: {e}")
        
        # Clear selection
        context.user_data["selected_tasks"] = set()
        
        # Show success message
        if completed_count > 0:
            task_list = "\n".join([f"✅ {name}" for name in completed_names[:3]])
            if completed_count > 3:
                task_list += f"\n... and {completed_count - 3} more"
            
            confirmation_text = f"Completed {completed_count} task(s):\n\n{task_list}"
        else:
            confirmation_text = "❌ Failed to complete selected tasks"
        
        # Create keyboard to return to task list
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Back to Tasks", callback_data=LIST_TASKS)],
            [InlineKeyboardButton("🏠 Main Menu", callback_data=MAIN_MENU)]
        ])
        
        await query.edit_message_text(
            confirmation_text,
            reply_markup=keyboard
        )
        return ConversationHandler.END

    elif query.data == CLEAR_SELECTION:
        # Clear all selections
        context.user_data["selected_tasks"] = set()
        
        # Refresh task list with empty selection
        tasks = context.user_data.get("user_tasks", [])
        filter_type = context.user_data.get("task_filter", "all")
        active_tasks = [t for t in tasks if t.get("status") in ["pending", "active"]]
        filtered_tasks = filter_tasks_by_date(active_tasks, filter_type)
        
        await query.edit_message_reply_markup(
            reply_markup=get_task_list_keyboard_with_checkboxes(filtered_tasks, set())
        )
        return ConversationHandler.END

    elif query.data == "no_selection":
        # Handle clicks on disabled buttons
        await query.answer("No tasks selected")
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
