"""Simple list implementation for Telegram bot."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from typing import List

# Conversation states
AWAITING_LIST_NAME = 1
AWAITING_LIST_ITEMS = 2
EXECUTING_LIST = 3


async def new_list_button_clicked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle when user clicks '+ New List' button."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text("What will we call this list?")

    return AWAITING_LIST_NAME


async def handle_list_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the list name input."""
    list_name = update.message.text.strip()

    # Store in context
    context.user_data["new_list_name"] = list_name

    await update.message.reply_text(
        f"Creating list: '{list_name}'\n\n"
        "What items would you like to add to this list?\n"
        "(separate each with a period)"
    )

    return AWAITING_LIST_ITEMS


async def handle_list_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the list items input."""
    items_text = update.message.text
    list_name = context.user_data.get("new_list_name", "Untitled List")

    # Parse items - handle both ". " and "." as separators
    items = parse_list_items(items_text)

    if not items:
        await update.message.reply_text(
            "I couldn't find any items. Please try again, separating each item with a period."
        )
        return AWAITING_LIST_ITEMS

    # Store the list (in real implementation, save to database)
    list_id = save_list(list_name, items, update.effective_user.id)

    # Show the created list with action buttons
    list_display = format_list_display(list_name, items)

    keyboard = [
        [
            InlineKeyboardButton("▶️ Start", callback_data=f"start_list_{list_id}"),
            InlineKeyboardButton("📝 Edit", callback_data=f"edit_list_{list_id}"),
        ],
        [
            InlineKeyboardButton(
                "🔄 Convert to Tasks", callback_data=f"convert_list_{list_id}"
            ),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_list_{list_id}"),
        ],
    ]

    await update.message.reply_text(
        f"✅ List created!\n\n{list_display}\n\nWhat would you like to do?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    # Return to main menu state
    return ConversationHandler.END


def parse_list_items(text: str) -> List[str]:
    """Parse items from text, handling various separators."""
    # First try splitting by ". " (period followed by space)
    if ". " in text:
        items = text.split(". ")
    # Then try just period
    elif "." in text:
        items = text.split(".")
    else:
        # No periods found, treat as single item
        return [text.strip()] if text.strip() else []

    # Clean up items
    cleaned_items = []
    for item in items:
        item = item.strip()
        # Remove trailing period if exists
        if item.endswith("."):
            item = item[:-1].strip()
        if item:  # Only add non-empty items
            cleaned_items.append(item)

    return cleaned_items


def format_list_display(name: str, items: List[str]) -> str:
    """Format a list for display."""
    display = f"📋 {name}\n\n"
    for i, item in enumerate(items, 1):
        display += f"{i}. {item}\n"
    return display


def save_list(name: str, items: List[str], user_id: str) -> str:
    """Save list to database (placeholder for now)."""
    # In real implementation, save to database
    # Return a unique list ID
    import time

    return f"list_{int(time.time())}"


# Handler for starting list execution
async def start_list_execution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start executing a list (checking off items)."""
    query = update.callback_query
    await query.answer()

    # Extract list_id from callback data
    list_id = query.data.replace("start_list_", "")

    # In real implementation, load list from database
    # For now, use dummy data
    list_name = context.user_data.get("new_list_name", "My List")
    items = ["Check oil", "Check coolant", "Inspect belts"]  # Would load from DB

    # Store execution state
    context.user_data["executing_list"] = {
        "id": list_id,
        "name": list_name,
        "items": items,
        "current_index": 0,
        "completed": [],
    }

    # Show first item
    await show_current_list_item(query, context)

    return EXECUTING_LIST


async def show_current_list_item(query_or_update, context: ContextTypes.DEFAULT_TYPE):
    """Show the current item in list execution."""
    execution = context.user_data.get("executing_list", {})
    items = execution.get("items", [])
    current_index = execution.get("current_index", 0)
    completed = execution.get("completed", [])

    if current_index >= len(items):
        # List complete
        await show_list_complete(query_or_update, context)
        return ConversationHandler.END

    current_item = items[current_index]
    progress = f"{len(completed)}/{len(items)}"

    keyboard = [
        [
            InlineKeyboardButton("✅ Done", callback_data="item_done"),
            InlineKeyboardButton("⏭️ Skip", callback_data="item_skip"),
        ],
        [
            InlineKeyboardButton("📝 Note", callback_data="item_note"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_list"),
        ],
    ]

    message = (
        f"📋 {execution.get('name', 'List')} ({progress})\n\n"
        f"Current item:\n"
        f"▶️ {current_item}\n\n"
        "What would you like to do?"
    )

    if hasattr(query_or_update, "edit_message_text"):
        await query_or_update.edit_message_text(
            message, reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query_or_update.message.reply_text(
            message, reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_item_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle actions on list items (done, skip, etc)."""
    query = update.callback_query
    await query.answer()

    execution = context.user_data.get("executing_list", {})
    action = query.data

    if action == "item_done":
        # Mark current item as done
        current_index = execution.get("current_index", 0)
        execution["completed"].append(current_index)
        execution["current_index"] = current_index + 1

    elif action == "item_skip":
        # Skip current item
        execution["current_index"] = execution.get("current_index", 0) + 1

    elif action == "cancel_list":
        await query.edit_message_text(
            "List execution cancelled.\n\n" "What would you like to do?",
            reply_markup=get_main_menu_keyboard(),
        )
        return ConversationHandler.END

    # Show next item
    await show_current_list_item(query, context)
    return EXECUTING_LIST


async def show_list_complete(query, context: ContextTypes.DEFAULT_TYPE):
    """Show list completion summary."""
    execution = context.user_data.get("executing_list", {})
    completed = len(execution.get("completed", []))
    total = len(execution.get("items", []))

    await query.edit_message_text(
        f"✅ List complete!\n\n"
        f"📋 {execution.get('name', 'List')}\n"
        f"Completed: {completed}/{total} items\n\n"
        "What would you like to do?",
        reply_markup=get_main_menu_keyboard(),
    )


def get_main_menu_keyboard():
    """Get the main menu keyboard."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("➕ New Task", callback_data="new_task"),
                InlineKeyboardButton("➕ New List", callback_data="new_list"),
            ],
            [
                InlineKeyboardButton("📋 My Lists", callback_data="my_lists"),
                InlineKeyboardButton("📋 My Tasks", callback_data="my_tasks"),
            ],
        ]
    )
