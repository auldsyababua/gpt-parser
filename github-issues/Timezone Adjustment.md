Here’s the GitHub issue body text:

---

### 🚀 Enhancement: Add Local Timezone Translation for Task Reminders

**Goal:**
Enable the system to properly interpret and convert times mentioned by the assigner (default: Colin, in California / PDT) into the assignee’s local timezone (e.g., Joel in Texas / CST).

---

### 🧠 Problem

Right now, when Colin issues a task like:

> “At 3pm tomorrow, remind Joel to check the backyard for oil at 4pm.”

…the system interprets:

* `"3pm tomorrow"` as a reminder trigger time
* `"4pm tomorrow"` as the actual task due time

However, **both times are understood in Colin’s timezone (PDT)**, but Joel lives in CST. The result: Joel gets the reminder at the wrong local time unless we manually adjust.

---

### ✅ Proposed Behavior

1. **Assign Colin's default timezone as PDT (America/Los\_Angeles)**
2. **Parse all datetime expressions in Colin’s timezone**
3. **Convert parsed times to UTC/GMT**
4. **Then convert the UTC times into the assignee’s timezone**, e.g.:

   * Joel → CST (America/Chicago)

---

### 🧪 Example

**Input (from Colin):**

> “At 3pm tomorrow, remind Joel to check the backyard for oil at 4pm.”

**Interpretation:**

* Colin's 3:00 PM PDT → 22:00 UTC
* Colin's 4:00 PM PDT → 23:00 UTC

**Translate to CST (Joel):**

* Reminder time: 5:00 PM CST (22:00 UTC)
* Task time: 6:00 PM CST (23:00 UTC)

**Expected Output JSON:**

```json
{
  "assigner": "Colin",
  "assignee": "Joel",
  "task": "Check the backyard for oil",
  "due_date": "2025-07-10",
  "due_time": "18:00",
  "reminder_time": "17:00",
  "created_at": "2025-07-09T08:00",
  "status": "pending"
}
```

---

### 🔧 Implementation Plan

* Add a timezone map for all assignees (e.g., Colin → America/Los\_Angeles, Joel → America/Chicago)
* Update parsing logic to:

  1. Parse datetime expressions using assigner’s TZ
  2. Convert to UTC
  3. Re-convert to assignee’s TZ before output
* (Optional) Add `reminder_time` field to distinguish from `due_time`

---

### 🧱 Dependencies

* Python: `pytz`, `dateutil`, or `zoneinfo`
* Node.js: `luxon`, `dayjs`, or `date-fns-tz`

---

Let me know if you want this applied to the future automation pipeline or just added to schema/plumbing design now.

---

### 🔄 Update: Explicit Timezone Handling

**Additional Requirement:**
When a timezone is explicitly stated in the input (e.g., "4pm CST", "9am EST"), the system should:

1. Parse and recognize the explicit timezone
2. Use that timezone for the time calculation instead of defaulting to assigner's timezone
3. Still convert to assignee's local timezone for display

**Example:**
- Input: "At 4pm CST tomorrow, remind Joel to check the oil"
- System recognizes "CST" and interprets 4pm as Central Time
- Converts to Joel's local time for the reminder (which happens to also be CST)

This prevents confusion when assigners specify times in the recipient's timezone or any other explicit timezone.
