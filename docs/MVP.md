# 🧱 Design Doc: GPT-Powered Task Reminder System for Off-Grid Bitcoin Mining Ops

### Sub-MVP Focus: Validate GPT → Structured JSON parsing before plumbing

---

## 🔁 Updated Dev Sequence

**Step 1.** Build & test a Custom GPT that converts natural language into JSON
**Step 2.** Grade its output using 30 realistic task prompts
**Step 3.** Refine system prompt until accuracy is solid
**Step 4.** Build plumbing: webhook → n8n → Sheets/Notion/etc

---

## 🎯 GOAL

Ensure a Custom GPT reliably parses tasks from ops managers (Colin, Bryan, Joel) into structured JSON objects with fields needed for downstream automation.

---

## 🧠 Step 1: Build Custom GPT

* Go to [https://chat.openai.com/gpts](https://chat.openai.com/gpts)
* Click **Create a GPT**
* Enable **Actions** (not needed for Sub-MVP yet)
* Set system prompt (see below)
* Interface via ChatGPT UI for now (manual testing)

---

## 🧾 Step 2: Test Prompts

Use these 30 prompts to validate accuracy:

<details>
<summary>📋 View All 30 Domain-Specific Task Prompts</summary>

1. Bryan needs to check genset #2’s oil levels tomorrow at 3pm.
2. Colin, make sure to call Lucky Electric next Monday at 9:30am to confirm the rewire.
3. Text Joel at 7 tonight about the new flare readings.
4. Joel — pick up the Starlink from Site C on Thursday after lunch.
5. Bryan, follow up with LoneStar Permitting next Friday morning.
6. Colin — send the invoice for the flare skids in 2 hours.
7. In 45 minutes, remind Joel to reboot the watchdog script on site A.
8. One week from now, Bryan should test the Gen3 throttle config.
9. Joel needs to call Upstream Data support on July 10th at 10am.
10. Colin — confirm delivery window with trucking company July 15 at 2:30pm.
11. Mark down “inspect vent stack heat discoloration” for this Saturday (Bryan).
12. Joel, pay the generator rental invoice tomorrow.
13. Colin — finalize deal terms with power co-op by next Wednesday.
14. Sometime this week, Bryan should price out steel panels for Site D’s shelter.
15. Early afternoon Thursday — Joel and Colin meet to review load-sharing logic.
16. Add “re-anchor solar rig after storm” to Colin’s list.
17. Joel — “replace padlock on Site B container” needs to be tracked.
18. Bryan — schedule flare maintenance walk for next week.
19. Remind Colin every Friday at 5pm to pull uptime logs from all telemetry boxes.
20. In 2 weeks, Bryan needs to confirm Joel rescheduled Site A fuel delivery from July 22 to July 25.
21. Joel — remind Bryan tomorrow morning to remind Colin about the tax exemption doc.
22. Don’t let Joel forget to check coolant every other day at 8am this month.
23. Bryan — renew generator insurance policy by July 30.
24. Every Monday at 9am, Joel should run checks on SHA-256 tuning scripts.
25. Bryan — pay the monthly storage unit bill on the 1st.
26. Colin — draft revised network topology diagram for Site C before Tuesday’s call.
27. Submit final invoice for contractor welding work before Thursday EOD (Joel).
28. Joel — run blower fans manually before shutdown tonight.
29. Bryan — vacuum inside control cabinet at Site D every Saturday morning.
30. Colin — remind yourself to compliment Joel’s generator fix daily at 9am.

</details>

---

## 🧩 Step 3: Expected JSON Format

```json
{
  "assignee": "Colin", 
  "task": "Check genset #2’s oil levels", 
  "due_date": "2025-07-10", 
  "due_time": "15:00", 
  "status": "pending",
  "site": "Site B", 
  "created_at": "2025-07-09T08:15"
}
```

Optional/bonus fields:

* `site` (e.g. “Site A” / “Site C”)
* `repeat_interval` (e.g. `weekly`, `monthly`, `every Friday`)
* `related_to` (e.g. `Joel`, `contractor invoice`, etc.)

---

## 🧠 Step 4: Custom GPT System Prompt (Draft)

```
You are a structured assistant for off-grid bitcoin mine managers. Your job is to extract structured task data from natural language input.

All tasks are assigned to one of: Colin (default), Bryan, or Joel.

Convert each task into JSON with the following fields:

- assignee (Colin, Bryan, or Joel)
- task (short task summary)
- due_date (YYYY-MM-DD)
- due_time (HH:MM 24h, omit if unavailable)
- status ("pending")
- created_at (current timestamp)
- site (optional: Site A, Site B, etc.)
- repeat_interval (optional: "weekly", "daily", etc.)

Return only the JSON block. If the date/time is unclear, make your best guess and add `"approximate": true`.

If no time or date is given, use today's date and leave time empty.
```
