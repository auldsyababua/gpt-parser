# Notification System

## Overview
Implement a proactive notification system that sends reminders to users via Telegram at scheduled times, ensuring tasks aren't forgotten.

## Status: READY FOR IMPLEMENTATION

### Prerequisites
- Telegram bot operational
- Task schema includes reminder times
- User timezone support working
- Task storage accessible

### 🎯 Target Features

1. **Scheduled Reminders**
   - Send notifications at task reminder time
   - Support multiple reminder times per task
   - Timezone-aware scheduling
   - Configurable reminder windows

2. **Notification Types**
   - Task due soon (30 min before)
   - Task overdue
   - Daily summary (optional)
   - High-priority alerts
   - Task assigned to you

3. **Interactive Notifications**
   - Mark complete from notification
   - Snooze reminders (15min, 1hr, tomorrow)
   - Add quick comment
   - View task details

4. **Smart Features**
   - Skip completed tasks
   - Escalation for ignored reminders
   - Quiet hours respect
   - Weekend/holiday awareness

### 💁 Notification Examples

**Task Reminder:**
```
⏰ Reminder: Task due in 30 minutes!

📋 Check oil at Site B
👤 Assigned to: You
🕐 Due: Today at 3:00 PM CST
📍 Location: Site B

[✅ Complete] [⏱️ Snooze] [💬 Comment]
```

**Daily Summary:**
```
🌅 Good morning, Joel!

Today's tasks (3):
• 9:00 AM - Check oil at Site A
• 2:00 PM - Meet contractor at Site B  
• 4:00 PM - Generator maintenance

Overdue (1):
⚠️ Submit weekly report (2 days late)

[📋 View All] [⚙️ Settings]
```

### 🔧 Technical Implementation

1. **Notification Scheduler**
   ```python
   # scheduler/notification_scheduler.py
   import asyncio
   import schedule
   from datetime import datetime, timedelta
   import pytz
   from telegram import InlineKeyboardButton, InlineKeyboardMarkup
   
   class NotificationScheduler:
       def __init__(self, bot, task_storage):
           self.bot = bot
           self.task_storage = task_storage
           self.scheduled_jobs = {}
       
       async def start(self):
           """Start the notification scheduler."""
           # Check for upcoming tasks every minute
           schedule.every(1).minutes.do(self.check_upcoming_tasks)
           
           # Send daily summaries
           schedule.every().day.at("08:00").do(self.send_daily_summaries)
           
           while True:
               schedule.run_pending()
               await asyncio.sleep(60)
       
       async def check_upcoming_tasks(self):
           """Check for tasks that need reminders."""
           now = datetime.utcnow()
           upcoming_window = now + timedelta(minutes=30)
           
           # Get tasks with reminders in the next 30 minutes
           tasks = await self.task_storage.get_tasks_by_reminder_time(
               start_time=now,
               end_time=upcoming_window
           )
           
           for task in tasks:
               if task['id'] not in self.scheduled_jobs:
                   await self.schedule_reminder(task)
       
       async def schedule_reminder(self, task: dict):
           """Schedule a single task reminder."""
           reminder_time = datetime.fromisoformat(task['reminder_datetime'])
           user_tz = pytz.timezone(task['assignee_timezone'])
           
           # Convert to user's local time
           local_time = reminder_time.astimezone(user_tz)
           
           # Schedule the notification
           job_id = f"reminder_{task['id']}"
           
           async def send_notification():
               await self.send_task_reminder(task)
               del self.scheduled_jobs[job_id]
           
           # Calculate delay
           delay = (reminder_time - datetime.utcnow()).total_seconds()
           if delay > 0:
               self.scheduled_jobs[job_id] = asyncio.create_task(
                   self._delayed_notification(delay, send_notification)
               )
       
       async def send_task_reminder(self, task: dict):
           """Send a task reminder notification."""
           keyboard = [
               [
                   InlineKeyboardButton("✅ Complete", 
                                      callback_data=f"complete_{task['id']}"),
                   InlineKeyboardButton("⏱️ Snooze", 
                                      callback_data=f"snooze_{task['id']}"),
               ],
               [
                   InlineKeyboardButton("💬 Comment", 
                                      callback_data=f"comment_{task['id']}"),
                   InlineKeyboardButton("🔄 View", 
                                      callback_data=f"view_{task['id']}"),
               ]
           ]
           
           message = f"""⏰ Reminder: Task due in 30 minutes!

📋 {task['title']}
👤 Assigned to: You
🕐 Due: {task['due_time_local']}
📍 Location: {task.get('site', 'Not specified')}
"""
           
           await self.bot.send_message(
               chat_id=task['assignee_telegram_id'],
               text=message,
               reply_markup=InlineKeyboardMarkup(keyboard)
           )
   ```

2. **Snooze Handler**
   ```python
   async def handle_snooze(update: Update, context: ContextTypes.DEFAULT_TYPE):
       """Handle snooze button clicks."""
       query = update.callback_query
       await query.answer()
       
       task_id = query.data.split('_')[1]
       
       # Show snooze options
       keyboard = [
           [
               InlineKeyboardButton("15 minutes", 
                                  callback_data=f"snooze_15_{task_id}"),
               InlineKeyboardButton("1 hour", 
                                  callback_data=f"snooze_60_{task_id}"),
           ],
           [
               InlineKeyboardButton("Tomorrow", 
                                  callback_data=f"snooze_tomorrow_{task_id}"),
               InlineKeyboardButton("❌ Cancel", 
                                  callback_data="cancel_snooze"),
           ]
       ]
       
       await query.edit_message_text(
           "How long would you like to snooze this reminder?",
           reply_markup=InlineKeyboardMarkup(keyboard)
       )
   ```

3. **Daily Summary Generator**
   ```python
   async def generate_daily_summary(user_id: str) -> str:
       """Generate daily task summary for user."""
       user = user_config.get_user_by_telegram_id(user_id)
       user_tz = pytz.timezone(user.timezone)
       
       # Get today's tasks
       today = datetime.now(user_tz).date()
       tasks = await task_storage.get_tasks_by_assignee_and_date(
           assignee_id=user_id,
           date=today
       )
       
       # Get overdue tasks
       overdue = await task_storage.get_overdue_tasks(assignee_id=user_id)
       
       # Format summary
       summary = f"🌅 Good morning, {user.display_name}!\n\n"
       
       if tasks:
           summary += f"Today's tasks ({len(tasks)}):\n"
           for task in sorted(tasks, key=lambda x: x['due_time']):
               time = task['due_time_local'].strftime("%I:%M %p")
               summary += f"• {time} - {task['title']}\n"
       else:
           summary += "No tasks scheduled for today 🎉\n"
       
       if overdue:
           summary += f"\nOverdue ({len(overdue)}):\n"
           for task in overdue[:3]:  # Show max 3
               days_late = (today - task['due_date']).days
               summary += f"⚠️ {task['title']} ({days_late} days late)\n"
       
       return summary
   ```

### 📅 Scheduling Architecture

1. **Persistent Scheduler**
   - Runs as separate process/container
   - Survives bot restarts
   - Loads pending notifications on startup

2. **Job Queue**
   - Redis/RabbitMQ for reliability
   - Retry failed notifications
   - Handle duplicate prevention

3. **Time Management**
   - All times stored in UTC
   - Convert to user timezone for display
   - Handle DST transitions

### ⚙️ Configuration Options

```python
# User notification preferences
{
    "notifications_enabled": true,
    "reminder_minutes_before": 30,
    "daily_summary_enabled": true,
    "daily_summary_time": "08:00",
    "quiet_hours": {
        "enabled": true,
        "start": "22:00",
        "end": "07:00"
    },
    "escalation": {
        "enabled": true,
        "after_minutes": 60,
        "notify_manager": true
    }
}
```

### 🎯 Advanced Features

1. **Smart Notifications**
   - Group multiple due-soon tasks
   - Skip if user already in chat
   - Location-based reminders
   - Weather-aware scheduling

2. **Escalation Chain**
   - Remind again after X minutes
   - Notify supervisor if ignored
   - Create urgent flag
   - SMS fallback (future)

3. **Analytics**
   - Track notification effectiveness
   - Response time metrics
   - Snooze patterns
   - Optimize reminder timing

### 🧪 Performance Requirements

- Schedule accuracy: ± 1 minute
- Concurrent notifications: 100+
- Delivery rate: 99%+
- Resource usage: < 100MB RAM

### 🔒 Security & Privacy

1. **Data Protection**
   - Don't log message content
   - Encrypt user preferences
   - Secure telegram IDs

2. **Rate Limiting**
   - Max notifications per user per hour
   - Prevent notification spam
   - Telegram API limits respect

### 🧪 Testing Scenarios

1. **Timing Tests**
   - Exact time delivery
   - Timezone boundaries
   - DST transitions
   - Midnight tasks

2. **Load Tests**
   - 100 simultaneous notifications
   - Rapid snooze/complete actions
   - Bot restart during scheduling

3. **Edge Cases**
   - User blocks bot
   - Task deleted after scheduling
   - Invalid timezone
   - Network failures

### 🎯 Success Metrics

- [ ] 95%+ on-time delivery
- [ ] 80%+ notification interaction rate
- [ ] < 5% snooze-and-forget rate
- [ ] 90%+ user satisfaction