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


def get_main_menu_keyboard():
    """Create the main menu inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("➕ New Task", callback_data=NEW_TASK),
            InlineKeyboardButton("📋 List Tasks", callback_data=LIST_TASKS),
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    logger.info(f"User {update.effective_user.id} started the bot")

    await update.message.reply_text(
        "Welcome to TaskBot! I help you manage tasks for your team.\n\n"
        "What would you like to do?",
        reply_markup=get_main_menu_keyboard(),
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

    elif query.data == LIST_TASKS:
        # TODO: Implement task listing from database/sheets
        task_list = """📋 Your Active Tasks (3):

1. Check oil at Site B - Joel
   🕐 Tomorrow 4:00 PM

2. Meet contractor - Bryan
   🕐 Today 5:00 PM

3. Submit weekly report - Colin
   🕐 Friday 6:00 PM

What would you like to do?"""

        await query.edit_message_text(
            task_list,
            reply_markup=get_main_menu_keyboard(),
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
