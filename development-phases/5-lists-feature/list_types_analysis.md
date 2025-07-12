# List Types Analysis

## 1. Reusable Checklists (Templates)

**Examples:**
- Daily generator inspection
- Weekly maintenance routine
- Site startup procedure
- Emergency shutdown procedure
- Contractor safety briefing
- Monthly deep inspection

**Characteristics:**
- Never modify the original template
- "Start" creates a new execution instance
- Track completion history
- Can see stats (completed 45/50 times)
- May want to schedule (every Monday)

**UI Behavior:**
- [ Start New ] [ View History ] [ Schedule ]
- Cannot edit items during execution
- Can skip items with reason
- Generates completion report

---

## 2. Living/Evolving Lists

**Examples:**
- Site A shopping list
- Parts to order
- Issues to fix at Site B
- Ideas for improvements
- Contact list for vendors
- Equipment inventory

**Characteristics:**
- Constantly add/remove items
- No "completion" - ongoing
- Items might have states (needed/ordered/received)
- Multiple people might add items
- Need to see who added what when

**UI Behavior:**
- [ + Add Item ] [ View All ] [ Clear Completed ]
- Can check off items (but they might come back)
- Can add notes to items
- Shows last modified date

---

## 3. One-Time Lists

**Examples:**
- Today's errands
- New site commissioning checklist
- Specific project tasks
- Meeting agenda items
- Inspection findings

**Characteristics:**
- Created for specific purpose
- Used once, then archived
- Linear progression
- Has a definite "complete" state

**UI Behavior:**
- [ Start ] [ Edit ] [ Delete ]
- Similar to reusable but no history
- Archived after completion

---

## 4. Hybrid: Recurring Generated Lists

**Examples:**
- "Monday tasks for Site A"
- "Bryan's daily assignments"
- "This week's maintenance items"

**Characteristics:**
- Auto-generated from tasks/schedules
- Read-only (managed by task system)
- Refreshes daily/weekly
- Can check off to update task status

---

## Proposed Implementation

### When Creating a List:

```
Bot: What will we call this list?
User: Site B shopping list

Bot: What type of list is this?
[🔁 Reusable Checklist] [📝 Living List] [✅ One-Time List]

User: [Clicks Living List]

Bot: Got it! This will be an ongoing list you can add to anytime.
What items would you like to start with? (separate with periods)
```

### Different Behaviors:

**Reusable Checklist:**
```
🔁 Daily Generator Inspection
Last run: Yesterday by Joel (5/5 completed)

[▶️ Start New Run] [📊 History] [🔔 Schedule]
```

**Living List:**
```
📝 Site B Shopping List (7 items)
Last updated: 2 hours ago

☑️ Oil filters (ordered 1/10)
☐️ Coolant - 5 gallons
☐️ New belt for generator 2

[+ Add Item] [👁️ View All] [🧹 Clear Done]
```

**One-Time List:**
```
✅ Today's Tasks (3/5 done)

[Continue] [View Items] [Delete]
```

### Database Considerations:

```sql
CREATE TABLE lists (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    list_type VARCHAR(50), -- 'reusable', 'living', 'one_time'
    created_by_id UUID,
    
    -- For living lists
    last_modified TIMESTAMPTZ,
    
    -- For reusable lists
    is_scheduled BOOLEAN DEFAULT FALSE,
    schedule_pattern VARCHAR(100),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_archived BOOLEAN DEFAULT FALSE
);

CREATE TABLE list_items (
    id UUID PRIMARY KEY,
    list_id UUID,
    title VARCHAR(500),
    
    -- For living lists
    added_by_id UUID,
    added_at TIMESTAMPTZ,
    status VARCHAR(50), -- 'active', 'completed', 'cancelled'
    completed_at TIMESTAMPTZ,
    
    -- For all types
    notes TEXT,
    position INTEGER
);

CREATE TABLE list_executions (
    -- Only for reusable checklists
    id UUID PRIMARY KEY,
    list_id UUID,
    executed_by_id UUID,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    completion_rate DECIMAL -- 0.8 = 80% completed
);
```