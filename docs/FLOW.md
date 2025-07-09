# ✅ **FLRTS MVP Pipeline (End-to-End Flow)**

### 1. 🎤 **User Input**

Colin writes a natural language task (via Claude or Custom GPT interface):

> “Remind Joel at 7pm tomorrow to restart the node at Site A.”

---

### 2. 🧠 **Custom GPT Parsing**

* Uses the `system_prompt.txt` you defined
* Assumes:

  * Colin is the assigner
  * All times are parsed relative to **current time in Colin’s timezone**
  * All output times are converted to **UTC**
  * Returns JSON with fields:

    ```json
    {
      "assigner": "Colin",
      "assignee": "Joel",
      "task": "Restart the node at Site A",
      "due_date": "2025-07-10",
      "due_time": "02:00",
      "reminder_time": "01:00",
      "status": "pending",
      "created_at": "2025-07-09T08:00",
      "site": "Site A"
    }
    ```

---

### 3. 📁 **Test Coverage**

* 30 domain-specific prompts in `tests/inputs.txt`
* GPT's output will be manually validated against the `task_schema.json`
* `evaluate_output.py` (optional next step) will automate validation against schema

---

### 4. 📄 **Storage (MVP)**

* Instead of a database, all structured task data is pasted into a **Google Sheet**
* Columns:

  ```
  Task Title | Assignee | Assigner | Due Date | Due Time | Reminder Time | Status | Site | Created At
  ```

---

### 5. 🧪 **Validation Flow**

* Colin copies GPT output
* Checks it manually or with `evaluate_output.py`
* Pastes valid rows into the Google Sheet

---

### 6. 🪝 (Optional) **Webhook Action (future step)**

* A GPT action (`SubmitTask`) can POST to an n8n webhook when you're ready
* Sheet automation or database writes can be added later

---

### ✅ Design Principles

* 🟩 JSON schema validation via `task_schema.json`
* 🟩 All times in UTC
* 🟩 Assignments limited to Colin, Bryan, Joel
* 🟨 Timezone conversion **not handled yet** (only standardized UTC)
* 🟥 No recurrence, subtasks, or multi-reminder logic yet

---