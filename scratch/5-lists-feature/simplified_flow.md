# Simplified List Feature Flow

## User Experience

### Creating a List

1. **User clicks "+ New List" button**

2. **Bot responds:**
   ```
   What will we call this list?
   ```

3. **User types:**
   ```
   Daily generator inspection
   ```

4. **Bot responds:**
   ```
   Creating list: 'Daily generator inspection'
   
   What items would you like to add to this list?
   (separate each with a period)
   ```

5. **User types:**
   ```
   Check oil. Check coolant. Inspect belts. Check filters. Test shutdown
   ```
   
   Or:
   ```
   Check oil.Check coolant.Inspect belts.Check filters.Test shutdown
   ```

6. **Bot creates list and shows:**
   ```
   ✅ List created!
   
   📋 Daily generator inspection
   
   1. Check oil
   2. Check coolant
   3. Inspect belts
   4. Check filters
   5. Test shutdown
   
   What would you like to do?
   [▶️ Start] [📝 Edit] [🔄 Convert to Tasks] [🗑️ Delete]
   ```

### Executing a List

1. **User clicks [▶️ Start]**

2. **Bot shows:**
   ```
   📋 Daily generator inspection (0/5)
   
   Current item:
   ▶️ Check oil
   
   What would you like to do?
   [✅ Done] [⏭️ Skip] [📝 Note] [❌ Cancel]
   ```

3. **User clicks [✅ Done]**

4. **Bot advances to next item:**
   ```
   📋 Daily generator inspection (1/5)
   
   Current item:
   ▶️ Check coolant
   
   What would you like to do?
   [✅ Done] [⏭️ Skip] [📝 Note] [❌ Cancel]
   ```

5. **Continue until complete:**
   ```
   ✅ List complete!
   
   📋 Daily generator inspection
   Completed: 5/5 items
   
   What would you like to do?
   [➕ New Task] [➕ New List] [📋 My Lists] [📋 My Tasks]
   ```

## Key Implementation Points

1. **Period Parsing**
   - Handle ". " (period + space)
   - Handle "." (just period)
   - Trim whitespace
   - Remove trailing periods

2. **Simple Storage**
   - List name
   - Array of items (just strings)
   - Created by user
   - Created timestamp

3. **Execution State**
   - Current item index
   - Completed items array
   - Start/end timestamps

4. **No Complex Features (Yet)**
   - No item dependencies
   - No time estimates
   - No conditional logic
   - No templates
   - Just simple checklists

## Database Schema (Simplified)

```sql
-- Minimal lists table
CREATE TABLE lists (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_by_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Minimal list items
CREATE TABLE list_items (
    id UUID PRIMARY KEY,
    list_id UUID REFERENCES lists(id),
    title VARCHAR(500) NOT NULL,
    position INTEGER NOT NULL
);

-- Track executions
CREATE TABLE list_executions (
    id UUID PRIMARY KEY,
    list_id UUID REFERENCES lists(id),
    user_id UUID REFERENCES users(id),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    items_completed INTEGER DEFAULT 0,
    items_total INTEGER
);
```

This keeps it simple and focused on the core checklist functionality!