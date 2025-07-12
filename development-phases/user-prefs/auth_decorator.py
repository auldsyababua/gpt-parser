"""Authentication decorator for Telegram bot handlers."""

import functools
import logging
from typing import Callable
from telegram import Update
from telegram.ext import ContextTypes
from user_config import UserConfigManager

logger = logging.getLogger(__name__)

# Global user config manager
user_config = UserConfigManager()


def require_auth(func: Callable) -> Callable:
    """Decorator to require authentication for bot commands/handlers."""

    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        # Get username from update
        user = update.effective_user
        username = user.username if user else None

        # Check if user is authorized
        if not username:
            logger.warning(
                f"Unauthorized access attempt - no username: {user.id if user else 'Unknown'}"
            )
            await update.message.reply_text(
                "❌ Access denied. You need a Telegram username to use this bot.\n"
                "Please set a username in your Telegram settings."
            )
            return

        if not user_config.is_authorized(username):
            logger.warning(f"Unauthorized access attempt: @{username} (ID: {user.id})")
            await update.message.reply_text(
                "❌ Access denied. You are not authorized to use this bot.\n"
                "Please contact an administrator if you need access."
            )
            return

        # Get user preferences and add to context
        user_prefs = user_config.get_user(username)
        context.user_data["user_prefs"] = user_prefs
        context.user_data["username"] = username

        logger.info(f"Authorized access: @{username} ({user_prefs.display_name})")

        # Call the original function
        return await func(update, context, *args, **kwargs)

    return wrapper


def admin_only(func: Callable) -> Callable:
    """Decorator to require admin role for bot commands/handlers."""

    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        # First check basic auth
        user = update.effective_user
        username = user.username if user else None

        if not username or not user_config.is_authorized(username):
            await update.message.reply_text("❌ Access denied.")
            return

        # Check admin role
        user_prefs = user_config.get_user(username)
        if user_prefs.role != "admin":
            logger.warning(f"Admin access denied for: @{username}")
            await update.message.reply_text(
                "❌ This command requires administrator privileges."
            )
            return

        # Add user data to context
        context.user_data["user_prefs"] = user_prefs
        context.user_data["username"] = username

        return await func(update, context, *args, **kwargs)

    return wrapper


async def check_callback_auth(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    """Check authorization for callback queries (button clicks)."""
    user = update.effective_user
    username = user.username if user else None

    if not username or not user_config.is_authorized(username):
        await update.callback_query.answer(
            "❌ You are not authorized to use this bot.", show_alert=True
        )
        return False

    # Add user preferences to context
    user_prefs = user_config.get_user(username)
    context.user_data["user_prefs"] = user_prefs
    context.user_data["username"] = username

    return True
