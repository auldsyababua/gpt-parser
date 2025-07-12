# Simplified: Two List Types

## Type 1: Checklists (Reusable)

**What they're for:**
- Daily routines
- Standard procedures
- Safety checks
- Maintenance schedules

**How they work:**
- Template that never changes
- "Start" begins a fresh run
- Check off items as you go
- Complete and it resets for next time

**Examples:**
- "Daily Site B Inspection" (run every morning)
- "Generator Shutdown Procedure" (run when needed)
- "Weekly Maintenance" (run Mondays)

---

## Type 2: Todo Lists (Living)

**What they're for:**
- Shopping/parts lists
- Ongoing issues
- Ideas and reminders
- Shared team lists

**How they work:**
- Add/remove items anytime
- Items stay checked off
- No "completion" - it's ongoing
- Multiple people can add items

**Examples:**
- "Site A Shopping List"
- "Generator 3 Issues"
- "Bryan's Todo List"

---

## Simple Implementation

### Creating a list:
```
Bot: What will we call this list?
User: Daily generator inspection

Bot: Is this a:
[🔁 Checklist (reusable)] [📝 Todo List (ongoing)]

User: [Clicks Checklist]

Bot: Great! What items should this checklist include?
(separate with periods)
```

### Different interfaces:

**Checklist:**
```
🔁 Daily Generator Inspection
Last run: Yesterday ✅

[▶️ Start Checklist]
```

**Todo List:**
```
📝 Site A Shopping List
☐️ Oil filters
☑️ Coolant (bought)
☐️ New gauge

[+ Add Item]
```

### Key Differences:

| Feature | Checklist | Todo List |
|---------|-----------|-----------||
| Items can be edited | No | Yes |
| Items reset after completion | Yes | No |
| Can add items anytime | No | Yes |
| Has "runs" or "executions" | Yes | No |
| Shows history | Yes | No |
| Items stay checked | No | Yes |

This keeps it simple with just two clear types!