# User Authentication & Preferences System

This feature adds a robust authentication layer and user preference management to the Telegram bot.

## Features

### 1. Authentication
- Only allows access to users with configured Telegram usernames
- Checks `@username` against whitelist
- Logs all access attempts
- Graceful denial messages for unauthorized users

### 2. User Preferences
- Timezone configuration per user
- Custom "morning/evening" time interpretations
- Default reminder settings
- Working hours preferences
- Notification preferences
- Role-based access (operator, admin, viewer)

### 3. Admin Commands
- `/adduser @username Name Timezone` - Add new users
- `/listusers` - Show all active users
- `/removeuser @username` - Remove a user
- `/settings` - Show current user's settings

## Implementation

### Core Components

1. **user_config.py**
   - `UserPreferences` dataclass with all user settings
   - `UserConfigManager` for loading/saving user data
   - JSON persistence for configuration

2. **auth_decorator.py**
   - `@require_auth` decorator for protected commands
   - `@admin_only` decorator for admin commands
   - `check_callback_auth()` for button click validation

3. **telegram_bot_with_auth.py**
   - Integrated auth checks on all handlers
   - User context passed to all functions
   - Enhanced messages with user preferences

## Usage Examples

### Unauthorized User
```
User: /start
Bot: ❌ Access denied. You are not authorized to use this bot.
     Please contact an administrator if you need access.
```

### Authorized User
```
User: /start
Bot: Welcome back, Colin! 👋
     Your timezone: America/Los_Angeles
     What would you like to do?
     [New Task] [List Tasks]
```

### Admin Adding User
```
Admin: /adduser @newuser Bob America/Denver
Bot: ✅ User @newuser (Bob) added successfully!
     Timezone: America/Denver
```

## Configuration File Format

**users.json**
```json
{
  "colinaulds": {
    "username": "colinaulds",
    "display_name": "Colin",
    "timezone": "America/Los_Angeles",
    "default_reminder_minutes": 30,
    "morning_time": "07:00",
    "evening_time": "18:00",
    "working_hours_start": "08:00",
    "working_hours_end": "18:00",
    "is_active": true,
    "role": "admin",
    "notification_preferences": {
      "task_assigned": true,
      "task_due_soon": true,
      "task_overdue": true,
      "daily_summary": false
    }
  }
}
```

## Integration Benefits

1. **Security**: Only authorized users can create tasks
2. **Personalization**: Tasks use correct timezone automatically
3. **Accountability**: All actions logged with username
4. **Flexibility**: Easy to add/remove users without code changes
5. **Scalability**: Role system allows different permission levels

## Migration Steps

1. **Update imports**
   ```python
   from auth_decorator import require_auth, admin_only
   from user_config import UserConfigManager
   ```

2. **Add decorators to handlers**
   ```python
   @require_auth
   async def start(update, context):
       # Handler code
   ```

3. **Create initial user config**
   - Update USERS dict with actual Telegram usernames
   - Set appropriate timezones for each user

4. **Test auth flow**
   - Try with unauthorized username
   - Verify authorized users work
   - Test admin commands

## Future Enhancements

1. **Self-service preferences**: Users update their own settings
2. **OAuth integration**: Link to external auth systems  
3. **Temporary access**: Time-limited user permissions
4. **Audit logs**: Detailed activity tracking
5. **2FA**: Additional security for sensitive operations