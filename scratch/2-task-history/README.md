# Task History & Audit Trail

## Overview
Implement comprehensive task history tracking to maintain a complete audit trail of all task changes, providing accountability and insights into task lifecycle.

## Status: READY FOR IMPLEMENTATION

### Prerequisites
- Task creation working
- User identification in place
- Basic task schema established

### 🎯 Target Features

1. **Change Tracking**
   - Record all task modifications
   - Track who made changes and when
   - Store before/after values
   - Support for bulk operations

2. **History Types**
   - Task created
   - Status changed (pending → completed)
   - Assignee changed
   - Due date/time modified
   - Priority updated
   - Task edited/clarified
   - Task deleted/cancelled

3. **Storage Implementation**
   - JSON file-based initially (quick to implement)
   - Structured for easy migration to database
   - Separate file per day for performance
   - Automatic archival of old history

4. **Query Capabilities**
   - View history by task ID
   - View history by user
   - Filter by date range
   - Filter by action type

### 📊 Data Structure

```python
# Task History Entry
{
    "id": "hist_1234567890",
    "task_id": "task_abc123",
    "timestamp": "2024-01-11T14:30:00Z",
    "user": {
        "telegram_id": "123456789",
        "username": "colin_10netzero",
        "display_name": "Colin"
    },
    "action": "status_change",
    "changes": {
        "status": {
            "old": "pending",
            "new": "completed"
        }
    },
    "metadata": {
        "ip_address": "10.0.0.1",
        "client": "telegram_bot",
        "version": "1.0"
    }
}

# Task Creation Entry
{
    "id": "hist_1234567891",
    "task_id": "task_abc123",
    "timestamp": "2024-01-11T14:00:00Z",
    "user": {
        "telegram_id": "123456789",
        "username": "colin_10netzero",
        "display_name": "Colin"
    },
    "action": "created",
    "data": {
        "title": "Check oil at Site B",
        "assignee": "Joel",
        "due_date": "2024-01-12",
        "due_time": "15:00",
        "priority": "normal",
        "original_message": "Tell Joel to check oil at Site B tomorrow at 3pm"
    }
}
```

### 🔧 Technical Implementation

1. **History Manager Class**
   ```python
   # utils/history_manager.py
   import json
   import os
   from datetime import datetime
   from typing import Dict, List, Optional
   import uuid
   
   class TaskHistoryManager:
       def __init__(self, history_dir: str = "data/history"):
           self.history_dir = history_dir
           os.makedirs(history_dir, exist_ok=True)
       
       def record_creation(self, task_id: str, task_data: dict, user: dict) -> str:
           """Record task creation."""
           entry = {
               "id": f"hist_{uuid.uuid4().hex}",
               "task_id": task_id,
               "timestamp": datetime.utcnow().isoformat() + "Z",
               "user": user,
               "action": "created",
               "data": task_data
           }
           return self._save_entry(entry)
       
       def record_change(self, task_id: str, changes: dict, 
                        user: dict, action: str = "updated") -> str:
           """Record task changes."""
           entry = {
               "id": f"hist_{uuid.uuid4().hex}",
               "task_id": task_id,
               "timestamp": datetime.utcnow().isoformat() + "Z",
               "user": user,
               "action": action,
               "changes": changes
           }
           return self._save_entry(entry)
       
       def get_task_history(self, task_id: str) -> List[dict]:
           """Get all history for a specific task."""
           history = []
           for filename in self._get_history_files():
               with open(filename, 'r') as f:
                   for line in f:
                       entry = json.loads(line)
                       if entry["task_id"] == task_id:
                           history.append(entry)
           return sorted(history, key=lambda x: x["timestamp"])
   ```

2. **Integration with Task Operations**
   ```python
   # In task creation flow
   async def create_task(task_data: dict, user: dict):
       # Create task as normal
       task_id = generate_task_id()
       
       # Record in history
       history_manager.record_creation(task_id, task_data, user)
       
       # Send to storage (Sheets/DB)
       result = await send_to_storage(task_data)
       
       if not result["success"]:
           # Record failure
           history_manager.record_change(
               task_id, 
               {"error": result["error"]},
               user,
               "creation_failed"
           )
       
       return result
   ```

3. **History Viewer Command**
   ```python
   @require_auth
   async def task_history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
       """Show task history via /history <task_id>."""
       if not context.args:
           await update.message.reply_text("Usage: /history <task_id>")
           return
       
       task_id = context.args[0]
       history = history_manager.get_task_history(task_id)
       
       if not history:
           await update.message.reply_text("No history found for this task.")
           return
       
       # Format history for display
       history_text = f"📆 History for Task {task_id}:\n\n"
       
       for entry in history:
           timestamp = entry["timestamp"][:19].replace("T", " ")
           user = entry["user"]["display_name"]
           action = entry["action"].replace("_", " ").title()
           
           history_text += f"• {timestamp} - {user}\n"
           history_text += f"  {action}\n"
           
           if "changes" in entry:
               for field, change in entry["changes"].items():
                   history_text += f"  {field}: {change['old']} → {change['new']}\n"
           
           history_text += "\n"
       
       await update.message.reply_text(history_text)
   ```

### 📊 Storage Strategy

1. **File Organization**
   ```
   data/history/
   ├── 2024-01-11.jsonl    # One file per day
   ├── 2024-01-10.jsonl
   ├── 2024-01-09.jsonl
   └── archive/
       └── 2024-01.tar.gz  # Monthly archives
   ```

2. **Performance Optimization**
   - Append-only writes (fast)
   - Daily file rotation
   - Index file for quick lookups
   - Async I/O for non-blocking

3. **Data Retention**
   - Keep 30 days of active history
   - Archive older data monthly
   - Configurable retention policy

### 🎯 Advanced Features

1. **Audit Reports**
   - Daily activity summary
   - User activity reports
   - Task lifecycle analytics
   - Compliance reporting

2. **Change Notifications**
   - Notify assignee of changes
   - Alert on high-priority modifications
   - Webhook for external monitoring

3. **History Search**
   - Full-text search in history
   - Complex queries (who changed X to Y)
   - Export history to CSV

### 🔒 Security Considerations

1. **Access Control**
   - Only admins can view full history
   - Users can view their own actions
   - Sensitive data masking

2. **Integrity**
   - Checksums for history files
   - Tamper detection
   - Backup verification

3. **Privacy**
   - GDPR compliance
   - Right to be forgotten
   - Data anonymization options

### 🧪 Testing Checklist

- [ ] Task creation records history
- [ ] Status changes are tracked
- [ ] User info correctly captured
- [ ] History retrieval works
- [ ] File rotation at midnight
- [ ] Performance with 10k+ entries
- [ ] Concurrent write handling

### 🎯 Success Metrics

- [ ] 100% of changes tracked
- [ ] < 10ms to write history
- [ ] < 100ms to retrieve task history
- [ ] Zero data loss
- [ ] 30-day retention working