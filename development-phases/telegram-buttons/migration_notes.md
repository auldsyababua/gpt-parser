# Migration Notes for Button Implementation

## Files to Modify

1. **scripts/telegram_bot.py** - Main bot file
   - Add inline keyboard imports
   - Replace text-based prompts with button interfaces
   - Update conversation flow

## Required Changes

### 1. Update Requirements
```bash
# Current python-telegram-bot version should already support inline keyboards
# No new dependencies needed
```

### 2. Import Changes
```python
# Add to existing imports
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
```

### 3. State Management Changes

Old states:
- AWAITING_CONFIRMATION = 1
- AWAITING_CLARIFICATION = 2

New states:
- AWAITING_TASK_DESCRIPTION = 1
- AWAITING_CLARIFICATION = 2

### 4. Key Integration Points

#### In `start()` function:
- Replace welcome text with button menu
- Use `reply_markup=get_main_menu_keyboard()`

#### In `handle_message()` (now `handle_task_description()`):
- Show buttons instead of asking for "yes/no/clarify"
- Use `reply_markup=get_task_confirmation_keyboard()`

#### New callback handler:
```python
application.add_handler(CallbackQueryHandler(handle_button_click))
```

### 5. Testing Checklist

- [ ] /start command shows main menu buttons
- [ ] "New Task" button initiates task creation
- [ ] "List Tasks" button shows task list
- [ ] Task confirmation shows Submit/Clarify/Cancel buttons
- [ ] Submit button creates task and returns to menu
- [ ] Clarify button allows task modification
- [ ] Cancel button returns to main menu
- [ ] Direct text messages still create tasks
- [ ] Error handling returns to main menu

## Rollback Plan

If issues arise:
1. Keep original `telegram_bot.py` as backup
2. Can disable buttons by removing `reply_markup` parameters
3. Conversation flow still works with text input

## Future Enhancements

1. **Edit existing tasks** - Add edit buttons to task list
2. **Quick templates** - Add common task buttons
3. **Pagination** - For long task lists
4. **Rich formatting** - Task cards with more details
5. **Notification settings** - Inline buttons for preferences