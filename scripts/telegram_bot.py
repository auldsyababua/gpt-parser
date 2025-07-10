import os
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv

# Import the assistant runner functions
from assistants_api_runner import get_or_create_assistant, parse_and_send

# --- Configuration ---
load_dotenv()
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN not found in .env file or environment.")
    exit()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Bot State ---
# We will store the assistant object globally since bot_data usage has changed
assistant = None


# --- Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    await update.message.reply_text(
        "Hi! I'm the Task Parser bot. Send me a task and I'll add it to the list."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles incoming text messages and passes them to the task parser."""
    user_message = update.message.text
    logger.info(
        f"Received message from {update.message.from_user.username}: {user_message}"
    )

    global assistant
    if not assistant:
        await update.message.reply_text(
            "Assistant is not initialized. Please wait a moment and try again."
        )
        return

    await update.message.reply_text(f"Processing your request: '{user_message}'...")

    try:
        # Run the parsing function in a separate thread to avoid blocking the bot
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, parse_and_send, assistant, user_message)
        await update.message.reply_text("✅ Task created successfully!")
        logger.info("Task processing completed successfully")
    except Exception as e:
        logger.error(f"Error processing task: {e}", exc_info=True)
        await update.message.reply_text(f"❌ An error occurred: {e}")


def main() -> None:
    """Start the bot."""
    global assistant

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Initialize the assistant
    logger.info("Initializing OpenAI Assistant...")
    assistant = get_or_create_assistant()
    if assistant:
        logger.info("Assistant initialized successfully.")
    else:
        logger.error(
            "Failed to initialize assistant. The bot may not function correctly."
        )

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # on non command i.e message - handle the message from Telegram
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Run the bot until the user presses Ctrl-C
    logger.info("Starting bot polling...")
    application.run_polling()


if __name__ == "__main__":
    main()
