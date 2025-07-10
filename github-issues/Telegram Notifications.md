### 💬 Enhancement: Add Telegram Notification Support

**Goal:**
Expand the existing Telegram bot to send proactive notifications and reminders.

---

### 📋 Requirements

1. **Proactive Notifications**
   - Send reminders at scheduled times without user prompting
   - Store Telegram chat IDs for each user
   - Rich message formatting with inline buttons

2. **Notification Types**
   - Task reminders at reminder_time
   - Due task alerts
   - Daily summary of tasks
   - Urgent task escalations

3. **Interactive Features**
   - Mark complete button
   - Snooze reminder (15min, 1hr, etc.)
   - Request task details
   - Quick reply to update status

4. **Message Format**
   ```
   ⏰ Task Reminder
   
   📄 Check oil levels at Site A
   🕑 Due: Today at 4:00 PM CST
   👤 Assigned by: Colin
   
   [✅ Complete] [🕒 Snooze] [📝 Details]
   ```

---

### 🔧 Implementation Considerations

- Use python-telegram-bot's job queue for scheduling
- Persistent storage of chat IDs and user preferences
- Handle bot restarts gracefully (reload scheduled jobs)
- Rate limiting to respect Telegram's API limits
- Timezone-aware scheduling
- Group chat support for team notifications

---

### 📦 Dependencies

- Existing python-telegram-bot setup
- APScheduler or similar for job scheduling
- Redis/SQLite for persistent job storage