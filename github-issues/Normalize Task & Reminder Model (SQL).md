**Title:** Upgrade storage schema to normalized task/reminder model for multi-user scheduling

**Body:**

> Once MVP parsing is stable, we'll need to migrate from Google Sheets to a normalized relational structure. This supports more complex intent mappings and scalable scheduling logic.
>
> ### ✅ New Structure
>
> * One `tasks` table (or Sheet in prototype) that handles **all task types**, including pure reminders
> * One `notifications` table to support:
>
>   * Multiple pings per task
>   * Absolute and offset times
>   * Tracking `sent_at` and `method` (push/email/sms)
>
> ### 🧠 Why it matters
>
> * Enables features like:
>
>   * “Remind me 30 min before”
>   * “Remind Joel again in 2 hours if not done”
>   * “Send SMS reminder to contractor 10 minutes before arrival”
> * Clean separation of intent (“do X”) vs. delivery logic (“when/how to notify”)
>
> ### 🔄 Example Mapping
>
> Prompt:
>
> > “Remind me tomorrow at 9am to tell Joel to check Site A at 10am”
>
> Result:
>
> * `tasks.title`: “Check Site A”
> * `reminder_at_utc`: 16:00 UTC (9am PDT)
> * `due_at_utc`: 17:00 UTC (10am PDT)
> * Later: `notifications.fire_at_utc = 16:00 UTC`
>
> ### 🔧 Proposed Next Step
>
> * Introduce UUID-based `users`, `tasks`, and `notifications` tables
> * Add support for `reminder_only` tasks
> * Use `tz` from `users` to resolve local time in parsing layer
>


