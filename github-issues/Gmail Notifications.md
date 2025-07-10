### 🔔 Enhancement: Add Gmail Notification Support

**Goal:**
Send task reminders and notifications via Gmail to assignees at the appropriate times.

---

### 📋 Requirements

1. **Gmail Integration**
   - Use Gmail API to send notifications
   - Support HTML email templates for better formatting
   - Include task details, due times, and any site information

2. **Notification Timing**
   - Send reminders at the specified reminder_time in assignee's local timezone
   - Option for task due notifications
   - Handle recurring tasks appropriately

3. **Email Content**
   - Clear subject line: "Task Reminder: [Task Description]"
   - Body includes:
     - Task description
     - Due date/time in assignee's timezone
     - Site location (if applicable)
     - Assigner information
   - Mobile-friendly formatting

4. **Configuration**
   - Store Gmail credentials securely
   - Map users to email addresses
   - Allow users to opt-in/out of email notifications

---

### 🔧 Implementation Considerations

- Use Gmail API with OAuth2 authentication
- Queue system for scheduled email sending
- Retry logic for failed sends
- Unsubscribe mechanism
- Email tracking (opened/clicked)

---

### 📦 Dependencies

- `google-api-python-client`
- `google-auth`
- Email templating library (e.g., Jinja2)
- Background task scheduler (e.g., Celery, APScheduler)