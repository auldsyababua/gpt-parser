### <¯ Enhancement: Add Structured Parsing Options for LLM Task Processing

**Goal:**
Provide the LLM with structured, selectable options for complex fields like repeat intervals, status updates, and other dynamic parameters to improve parsing accuracy and consistency.

---

### >à Problem

Currently, the LLM interprets free-form text for complex fields like repeat intervals, resulting in inconsistent outputs. For example:

**Input:**
> "Send a letter at 3am every 3rd Thursday of the month"

**Current Output (free-form):**
```
Repeat Interval: "monthly on the third Thursday"
```

This approach lacks structure and makes downstream processing difficult. The LLM is "doing its best" without clear guidance on valid options.

---

###  Proposed Behavior

Implement structured option sets for complex fields that the LLM can select from:

#### 1. **Repeat Interval Options**

Break down into selectable components:

**Ordinal Position:**
- `1st` | `2nd` | `3rd` | `4th` | `5th` | `last`

**Time Unit:**
- `day` | `weekday` | `weekend` | `week` | `month` | `quarter` | `year`

**Scope:**
- `of the week` | `of the month` | `of the quarter` | `of the year`

**Frequency Modifiers:**
- `every` | `every other` | `every 3rd` | `every N`

#### 2. **Status Options**

Structured status transitions with required parameters:

- `pending` ’ Default state
- `complete` ’ Task finished
- `deferred` ’ Requires: `new_date`, `new_time`, `reason` (optional)
- `reassigned` ’ Requires: `new_assignee`, `handoff_notes` (optional)
- `cancelled` ’ Requires: `reason`
- `in_progress` ’ Optional: `completion_percentage`

#### 3. **Priority Levels**

- `urgent` | `high` | `normal` | `low` | `backlog`

#### 4. **Notification Methods**

- `push` | `email` | `sms` | `slack` | `none`

#### 5. **Site Assignment Options**

- Dynamic list based on available sites
- `all_sites` | `site_group:<name>` | specific site names

---

### >ê Examples

**Input:**
> "Send a letter at 3am every 3rd Thursday of the month"

**Structured Output:**
```json
{
  "repeat_interval": {
    "ordinal": "3rd",
    "unit": "weekday",
    "weekday": "Thursday",
    "scope": "of the month",
    "frequency": "every"
  }
}
```

**Input:**
> "Defer the inspection to next Monday because of weather"

**Structured Output:**
```json
{
  "status": "deferred",
  "status_params": {
    "new_date": "2025-07-14",
    "new_time": null,
    "reason": "weather conditions"
  }
}
```

---

### =' Implementation Plan

1. **Define Option Schemas**
   - Create JSON schemas for each option type
   - Include validation rules and dependencies

2. **LLM Prompt Engineering**
   - Update system prompts to include available options
   - Provide examples of correct option selection
   - Add validation layer to ensure selected options are valid

3. **Parser Updates**
   - Modify parser to expect structured options
   - Add fallback for legacy free-form inputs
   - Implement option validation

4. **Database Schema**
   - Add enum fields for fixed options
   - Create lookup tables for dynamic options
   - Add JSON fields for complex structured data

---

### =Ê Additional Option Categories to Consider

1. **Duration Options**
   - `minutes` | `hours` | `days` | `weeks` | `months`
   - Compound durations: "2 hours 30 minutes"

2. **Conditional Triggers**
   - `if_not_complete_by` ’ time
   - `if_no_response_from` ’ assignee
   - `after_task_complete` ’ task_id

3. **Escalation Paths**
   - `notify_manager_after` ’ duration
   - `escalate_to` ’ person/role
   - `max_deferrals` ’ number

4. **Location Constraints**
   - `onsite_only` | `remote_ok` | `specific_location`
   - GPS coordinates for field work

5. **Resource Requirements**
   - `requires_equipment` ’ list
   - `requires_personnel` ’ count/roles
   - `weather_dependent` ’ conditions

---

### >ñ Dependencies

* Schema validation library (e.g., `jsonschema`, `zod`)
* Enum management for database
* LLM prompt versioning system

---

### <¯ Success Metrics

- Reduction in parsing errors by 80%
- Consistent output format across all tasks
- Ability to programmatically validate all LLM outputs
- Support for complex scheduling patterns without ambiguity