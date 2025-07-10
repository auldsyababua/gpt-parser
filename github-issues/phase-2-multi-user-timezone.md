# Phase 2: Multi-User & Timezone Support

## Overview
This phase adds support for multiple users with different timezones and roles, ensuring tasks are processed correctly regardless of who creates them or when.

## Status: NOT STARTED

### Prerequisites
- Phase 1 must be complete with 90%+ test accuracy
- Temporal expression parsing must be reliable

### 🎯 Target Features

1. **User Profile System**
   - Store user preferences (timezone, default site, role)
   - Map Telegram users to system users
   - Support for adding new users without code changes
   - Files: Create `user_manager.py`, update database schema

2. **Timezone-Aware Processing**
   - Reference: [Timezone Adjustment.md](./Timezone%20Adjustment.md)
   - Current issue: All times interpreted in Colin's timezone (PDT)
   - Solution: Parse in assigner TZ → store in UTC → display in assignee TZ
   - Known timezones:
     - Colin: PDT (UTC-7)
     - Joel: CST (UTC-5)
     - Bryan: TBD
   - Files: Create `timezone_handler.py`

3. **Multiple Assigners Support**
   - Remove hardcoded "Colin" as assigner
   - Detect assigner from Telegram user
   - Support delegation chains (Colin → Bryan → Joel)
   - Files: Update `system_prompt.txt`, `assistants_api_runner.py`

4. **Structured Options Implementation**
   - Reference: [Better Parsing Options.md](./Better%20Parsing%20Options.md)
   - Replace free-form fields with structured options:
     - Repeat intervals: ["never", "daily", "weekly", "weekdays", "monthly"]
     - Priority levels: ["low", "normal", "high", "urgent"]
     - Task status: ["pending", "in_progress", "completed", "cancelled"]
   - Files: Update `task_schema.json`, create `schema_validator.py`

5. **Enhanced Validation**
   - Validate all LLM outputs against schema
   - Reject invalid JSON before showing to user
   - Provide specific error messages
   - Files: Enhance validation in `assistants_api_runner.py`

### 📊 Database Schema Updates
```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id VARCHAR(50) UNIQUE,
    name VARCHAR(100),
    timezone VARCHAR(50),
    role VARCHAR(50),
    default_site VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Update tasks table
ALTER TABLE tasks ADD COLUMN assigner_id INTEGER REFERENCES users(id);
ALTER TABLE tasks ADD COLUMN created_in_tz VARCHAR(50);
ALTER TABLE tasks ADD COLUMN display_in_tz VARCHAR(50);
```

### 🧪 Test Cases
1. Task created by Colin for Joel shows correct time in CST
2. Task created by Bryan for Colin shows correct time in PDT
3. Recurring tasks respect assignee timezone for each occurrence
4. Ambiguous timezone references are clarified
5. Users can update their timezone preferences

### 🔧 Technical Implementation

1. **Timezone Processing Pipeline**
   ```python
   # 1. Detect user timezone from profile
   user_tz = get_user_timezone(telegram_user_id)
   
   # 2. Parse time in user's timezone
   local_time = parse_time_in_tz(time_string, user_tz)
   
   # 3. Convert to UTC for storage
   utc_time = local_time.astimezone(pytz.UTC)
   
   # 4. Convert to assignee timezone for display
   assignee_tz = get_user_timezone(assignee_id)
   display_time = utc_time.astimezone(assignee_tz)
   ```

2. **User Detection Flow**
   ```python
   # From Telegram message
   telegram_user = update.message.from_user
   system_user = user_manager.get_or_create_user(telegram_user)
   
   # Include in parsing context
   context = {
       'assigner': system_user.name,
       'assigner_timezone': system_user.timezone,
       'current_time': datetime.now(system_user.timezone)
   }
   ```

### 🎯 Success Metrics
- [ ] Support for 5+ concurrent users
- [ ] 100% accuracy on timezone conversions
- [ ] No hardcoded user references in code
- [ ] All times stored in UTC
- [ ] Structured options used consistently

### 🚀 Migration Plan
1. Create user profiles for existing users (Colin, Bryan, Joel)
2. Update all existing tasks with assigner_id
3. Convert all stored times to UTC
4. Update system prompt with user context
5. Deploy with backwards compatibility

## Next Phase Dependencies
Phase 3 (Database Backend) requires:
- Working user profile system
- Reliable timezone handling
- Structured data validation
- Multi-user support tested