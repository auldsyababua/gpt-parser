"""Enhanced Telegram bot with authentication and user preferences."""

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
)
from dotenv import load_dotenv

# Import auth and user config
from auth_decorator import require_auth, admin_only, check_callback_auth
from user_config import UserConfigManager, UserPreferences

# Import the assistant runner functions
from assistants_api_runner import (
    get_or_create_assistant,
    parse_task,
    format_task_for_confirmation,
)

# --- Configuration ---
load_dotenv()
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN not found in .env file or environment.")
    exit()

# Logging setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize user config manager
user_config = UserConfigManager()

# Bot state
assistant = None


def get_main_menu_keyboard():
    """Create the main menu inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("➕ New Task", callback_data="new_task"),
            InlineKeyboardButton("📋 List Tasks", callback_data="list_tasks"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


@require_auth
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user_prefs = context.user_data.get("user_prefs")

    await update.message.reply_text(
        f"Welcome back, {user_prefs.display_name}! 👋\n\n"
        f"Your timezone: {user_prefs.timezone}\n"
        "What would you like to do?",
        reply_markup=get_main_menu_keyboard(),
    )


@require_auth
async def handle_button_click(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle inline keyboard button clicks."""
    query = update.callback_query

    # Check auth for callback
    if not await check_callback_auth(update, context):
        return

    await query.answer()
    user_prefs = context.user_data.get("user_prefs")

    if query.data == "new_task":
        await query.edit_message_text(
            f"Hi {user_prefs.display_name}, please describe the task:"
        )
        context.user_data["awaiting_task"] = True

    elif query.data == "list_tasks":
        # Filter tasks by user's role/permissions
        task_list = f"""📋 Tasks visible to {user_prefs.display_name}:

1. Check oil at Site B - Joel
   🕐 Tomorrow 4:00 PM CST

2. Meet contractor - Bryan
   🕐 Today 5:00 PM CST

3. Submit weekly report - {user_prefs.display_name}
   🕐 Friday 6:00 PM {user_prefs.timezone}

What would you like to do?"""

        await query.edit_message_text(
            task_list,
            reply_markup=get_main_menu_keyboard(),
        )


@require_auth
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages."""
    user_prefs = context.user_data.get("user_prefs")
    user_input = update.message.text

    # Process as task
    logger.info(f"Task from {user_prefs.display_name}: {user_input}")

    try:
        # Initialize assistant if needed
        global assistant
        if not assistant:
            assistant = await get_or_create_assistant()

        # Add user context to the parsing
        enhanced_input = f"User: {user_prefs.display_name} (Timezone: {user_prefs.timezone})\n{user_input}"

        await update.message.reply_text("Processing your request...")
        parsed_task = await parse_task(enhanced_input, assistant.id)

        if parsed_task:
            # Apply user preferences
            if "reminder_minutes" not in parsed_task:
                parsed_task["reminder_minutes"] = user_prefs.default_reminder_minutes

            # Show confirmation
            confirmation = format_task_for_confirmation(parsed_task)
            await update.message.reply_text(
                f"{confirmation}\n\nSubmit this task?",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "✅ Submit", callback_data="submit_task"
                            ),
                            InlineKeyboardButton(
                                "❌ Cancel", callback_data="cancel_task"
                            ),
                        ]
                    ]
                ),
            )
            context.user_data["pending_task"] = parsed_task
        else:
            await update.message.reply_text(
                "❌ I couldn't understand that task. Please try again.\n\n"
                "What would you like to do?",
                reply_markup=get_main_menu_keyboard(),
            )

    except Exception as e:
        logger.error(f"Error processing task: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again.\n\n" "What would you like to do?",
            reply_markup=get_main_menu_keyboard(),
        )


@admin_only
async def add_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a new user (admin only)."""
    if not context.args or len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /adduser @username display_name timezone\n"
            "Example: /adduser @johndoe John America/Chicago"
        )
        return

    username = context.args[0].replace("@", "")
    display_name = context.args[1]
    timezone = context.args[2]

    try:
        new_user = UserPreferences(
            username=username,
            display_name=display_name,
            timezone=timezone,
        )
        user_config.add_user(new_user)

        await update.message.reply_text(
            f"✅ User @{username} ({display_name}) added successfully!\n"
            f"Timezone: {timezone}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error adding user: {e}")


@admin_only
async def list_users_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """List all users (admin only)."""
    users = user_config.list_active_users()

    if not users:
        await update.message.reply_text("No active users found.")
        return

    user_list = "👥 **Active Users:**\n\n"
    for username, prefs in users.items():
        user_list += f"• @{username} ({prefs.display_name})\n"
        user_list += f"  Timezone: {prefs.timezone}\n"
        user_list += f"  Role: {prefs.role}\n\n"

    await update.message.reply_text(user_list)


@require_auth
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user settings."""
    user_prefs = context.user_data.get("user_prefs")

    settings_text = f"""⚙️ **Your Settings**

👤 Display Name: {user_prefs.display_name}
🌍 Timezone: {user_prefs.timezone}
⏰ Default Reminder: {user_prefs.default_reminder_minutes} min before
🌅 Morning Time: {user_prefs.morning_time.strftime('%H:%M')}
🌆 Evening Time: {user_prefs.evening_time.strftime('%H:%M')}
🔨 Role: {user_prefs.role}

🔔 Notifications:
"""

    for notif_type, enabled in user_prefs.notification_preferences.items():
        emoji = "✅" if enabled else "❌"
        settings_text += f"  {emoji} {notif_type.replace('_', ' ').title()}\n"

    await update.message.reply_text(settings_text)


def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("adduser", add_user_command))
    application.add_handler(CommandHandler("listusers", list_users_command))

    # Message handler
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Callback handler for buttons
    application.add_handler(CallbackQueryHandler(handle_button_click))

    # Run the bot
    logger.info("Starting bot with authentication...")
    application.run_polling()


if __name__ == "__main__":
    main()
