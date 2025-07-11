import os
import logging
import asyncio
import json
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
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
# We will store the assistant object globally since bot_data usage has changed
assistant = None

# Conversation states
AWAITING_CONFIRMATION = 1
AWAITING_CLARIFICATION = 2


# --- Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    logger.info(f"Start command received from user {update.message.from_user.username}")
    await update.message.reply_text(
        "Hi! I'm the Task Parser bot. Send me a task and I'll add it to the list."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles incoming text messages and passes them to the task parser."""
    user_message = update.message.text
    logger.info(
        f"Received message from {update.message.from_user.username}: {user_message}"
    )

    global assistant
    logger.info(f"Assistant object: {assistant}")  # Debug log
    if not assistant:
        logger.error("Assistant is None!")
        await update.message.reply_text(
            "Assistant is not initialized. Please wait a moment and try again."
        )
        return ConversationHandler.END

    await update.message.reply_text(f"Processing your request: '{user_message}'...")

    try:
        # Run the parsing function in a separate thread to avoid blocking the bot
        logger.info("Starting parse_task in executor...")
        loop = asyncio.get_running_loop()

        # Add timeout to prevent hanging
        logger.info(
            f"Calling parse_task with assistant={assistant.get('id') if assistant else 'None'}, message='{user_message}'"
        )
        parsed_json = await asyncio.wait_for(
            loop.run_in_executor(None, parse_task, assistant, user_message),
            timeout=30.0,  # 30 second timeout
        )
        logger.info(f"parse_task completed successfully: {parsed_json}")

        # Store the parsed JSON in context for later use
        context.user_data["parsed_json"] = parsed_json
        context.user_data["original_message"] = user_message

        # Format the task for confirmation
        formatted_task = format_task_for_confirmation(parsed_json)

        # Ask for confirmation
        confirmation_message = f"I've parsed your task:\n\n{formatted_task}\n\n✅ Reply 'yes' to confirm\n❌ Reply 'no' to cancel\n✏️ Or describe what needs to be changed"
        await update.message.reply_text(confirmation_message)

        return AWAITING_CONFIRMATION

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
            parsed_json = await loop.run_in_executor(
                None, parse_task, assistant, combined_message
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

            # Format and show the updated task
            formatted_task = format_task_for_confirmation(parsed_json)
            confirmation_message = f"I've updated the task:\n\n{formatted_task}\n\n✅ Reply 'yes' to confirm\n❌ Reply 'no' to cancel\n✏️ Or describe what needs to be changed"
            await update.message.reply_text(confirmation_message)

            return AWAITING_CONFIRMATION

        except Exception as e:
            logger.error(f"Error reprocessing task: {e}", exc_info=True)
            await update.message.reply_text(
                f"❌ An error occurred while updating the task: {e}"
            )
            return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the current conversation."""
    await update.message.reply_text(
        "❌ Task cancelled. Send me a new task when you're ready."
    )
    return ConversationHandler.END


def main() -> None:
    """Start the bot."""
    global assistant

    logger.info("Starting Telegram bot...")
    logger.info(
        f"Bot token: {TELEGRAM_BOT_TOKEN[:10]}...{TELEGRAM_BOT_TOKEN[-10:]}"
    )  # Log partial token for debugging

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Initialize the assistant
    logger.info("Initializing OpenAI Assistant...")
    try:
        assistant = get_or_create_assistant()
        if assistant:
            logger.info(f"Assistant initialized successfully: {assistant.get('id')}")
        else:
            logger.error(
                "Failed to initialize assistant. The bot may not function correctly."
            )
    except Exception as e:
        logger.error(f"Exception initializing assistant: {e}", exc_info=True)
        raise

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # Create conversation handler for task processing
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
        states={
            AWAITING_CONFIRMATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_confirmation)
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
