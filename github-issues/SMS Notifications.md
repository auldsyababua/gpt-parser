### 📱 Enhancement: Add SMS Notification Support

**Goal:**
Send task reminders via SMS/text message to assignees' phones.

---

### 📋 Requirements

1. **SMS Provider Integration**
   - Support for Twilio, AWS SNS, or similar
   - Fallback providers for reliability
   - International number support

2. **Message Format**
   - Concise format due to SMS limitations (160 chars)
   - Essential info only:
     ```
     TASK REMINDER:
     Check oil levels
     Due: Today 4:00 PM
     Site: A
     -Colin
     ```

3. **User Configuration**
   - Store phone numbers securely
   - Validate phone number formats
   - Timezone-aware delivery
   - Opt-in/out preferences

4. **Delivery Features**
   - Delivery confirmation
   - Failed message retry
   - Do not disturb hours
   - Emergency override option

---

### 🔧 Implementation Considerations

- Cost management (SMS charges)
- Rate limiting to prevent spam
- Phone number verification process
- Multi-part message handling for longer tasks
- Compliance with SMS regulations (TCPA, GDPR)

---

### 📦 Dependencies

- Twilio SDK or AWS Boto3
- Phone number validation library
- Message queuing system