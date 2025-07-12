# Integration Example

This shows how the auth system integrates with existing components without breaking them.

## How It Works With Existing Features

### 1. Temporal Preprocessing (No Conflict)

The temporal processor still works exactly the same, but now gets user timezone automatically:

```python
# Before (temporal processor guesses timezone)
parse_task("Tell Joel at 3pm to check oil")

# After (timezone provided from user prefs)
user_prefs = context.user_data['user_prefs']
enhanced_input = f"User: {user_prefs.display_name} (Timezone: {user_prefs.timezone})\n{user_input}"
parse_task(enhanced_input)
```

### 2. Button UI (Enhanced)

Buttons still work, but now with personalized greetings:

```python
# Before
await query.edit_message_text("Please describe the task:")

# After  
await query.edit_message_text(f"Hi {user_prefs.display_name}, please describe the task:")
```

### 3. Assistant API (Enriched Context)

The assistant gets better context for parsing:

```python
# The assistant now knows:
# - Who is creating the task (display_name)
# - Their timezone for better time parsing
# - Their preferences for defaults
```

## Backward Compatibility

### If you don't want auth yet:

1. **Option A**: Don't use the decorators
   ```python
   # Just don't add @require_auth
   async def start(update, context):
       # Works without auth
   ```

2. **Option B**: Set a permissive config
   ```python
   # In user_config.py, add a wildcard user
   "*": UserPreferences(
       username="*",
       display_name="Guest",
       timezone="America/Chicago",  # Default
       role="operator"
   )
   ```

## Testing Without Breaking Current Work

1. **Test in isolation**: Run the auth bot separately
   ```bash
   cd scratch/user-prefs
   python telegram_bot_with_auth.py
   ```

2. **Gradual integration**:
   - First: Just add user config file
   - Then: Add auth to one command
   - Finally: Full integration

3. **Feature flag approach**:
   ```python
   ENABLE_AUTH = os.getenv('ENABLE_AUTH', 'false').lower() == 'true'
   
   if ENABLE_AUTH:
       from auth_decorator import require_auth
   else:
       # Dummy decorator that does nothing
       def require_auth(func):
           return func
   ```

## Why This Won't Break Anything

1. **Separate concern**: Auth happens before any parsing/processing
2. **Additive only**: Adds context data, doesn't change existing data
3. **Isolated files**: New modules don't modify existing code
4. **Graceful defaults**: Missing users just get denied, nothing crashes
5. **Optional integration**: Can be added incrementally