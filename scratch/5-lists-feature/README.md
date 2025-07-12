# Lists Feature

## Overview
Implement support for checklists and task templates, allowing users to create reusable lists for common operations like daily inspections, maintenance routines, and multi-step procedures.

## Status: READY FOR IMPLEMENTATION

### Prerequisites
- Database backend implemented
- Basic task creation working
- User authentication in place

### 🎯 Target Features

1. **List Creation & Management**
   - Create named lists (e.g., "Daily Site B Inspection")
   - Add/remove/reorder items
   - Set list metadata (site, frequency, category)
   - Clone existing lists
   - Archive completed lists

2. **List Types**
   - **Checklists**: Simple check-off items
   - **Task Templates**: Convert to individual tasks
   - **Recurring Lists**: Auto-generate daily/weekly
   - **Sequential Lists**: Items must be done in order
   - **Conditional Lists**: Items depend on previous answers

3. **Natural Language Support**
   - "Create a daily checklist: oil, coolant, belts, filters"
   - "Start the morning inspection checklist for Site A"
   - "Convert the maintenance list to tasks for Joel"
   - "Show me all inspection checklists"

4. **List Execution**
   - Check off items inline
   - Add notes/photos to items
   - Track completion percentage
   - Time tracking per item
   - Skip items with reason

5. **List Templates Library**
   - Pre-built common lists
   - User-created templates
   - Share templates between users
   - Version control for templates

## 📋 Example Use Cases

### Daily Inspection Checklist
```
User: "Create daily inspection list for Site B"

Bot: 📋 Creating list: "Daily Inspection - Site B"
     What items should I include?

User: "Check oil levels, check coolant, inspect belts, 
      check air filters, verify telemetry, test shutdown"

Bot: ✅ List created with 6 items:
     
     📋 Daily Inspection - Site B
     □ Check oil levels
     □ Check coolant
     □ Inspect belts
     □ Check air filters
     □ Verify telemetry
     □ Test shutdown
     
     [▶️ Start] [📝 Edit] [🔄 Convert to Tasks]
```

### Executing a List
```
User: [Taps ▶️ Start]

Bot: 📋 Daily Inspection - Site B (0/6)
     
     Current: Check oil levels
     
     [✅ Done] [⏭️ Skip] [📝 Note] [📸 Photo]

User: [Taps ✅ Done]

Bot: ✅ 1/6 complete
     
     Current: Check coolant
     
     [✅ Done] [⏭️ Skip] [📝 Note] [📸 Photo]
```

### Converting to Tasks
```
User: "Convert the weekly maintenance list to tasks for Bryan"

Bot: 🔄 Converting list to tasks...
     
     Created 8 tasks for Bryan:
     • Change oil - Due tomorrow 8 AM
     • Replace filters - Due tomorrow 9 AM
     • Check batteries - Due tomorrow 10 AM
     ... (5 more)
     
     ✅ All tasks created and assigned!
```

## 📊 Database Schema

```sql
-- Lists table
CREATE TABLE lists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    list_id_display VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Metadata
    created_by_id UUID REFERENCES users(id) NOT NULL,
    site_id UUID REFERENCES sites(id),
    category VARCHAR(50), -- 'inspection', 'maintenance', 'safety', etc.
    list_type VARCHAR(50) DEFAULT 'checklist', -- 'checklist', 'template', 'sequential'
    
    -- Recurrence
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_pattern VARCHAR(50), -- 'daily', 'weekly', 'monthly'
    next_occurrence DATE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_template BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- List items table
CREATE TABLE list_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    list_id UUID REFERENCES lists(id) ON DELETE CASCADE,
    
    -- Item details
    title VARCHAR(500) NOT NULL,
    description TEXT,
    position INTEGER NOT NULL, -- Order in list
    
    -- Task conversion settings
    default_assignee_id UUID REFERENCES users(id),
    estimated_duration_minutes INTEGER,
    priority VARCHAR(20) DEFAULT 'normal',
    
    -- Dependencies
    depends_on_item_id UUID REFERENCES list_items(id),
    
    is_optional BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(list_id, position)
);

-- List executions (instances of a list being used)
CREATE TABLE list_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    list_id UUID REFERENCES lists(id),
    executed_by_id UUID REFERENCES users(id),
    site_id UUID REFERENCES sites(id),
    
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    -- Summary
    total_items INTEGER,
    completed_items INTEGER DEFAULT 0,
    skipped_items INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(50) DEFAULT 'in_progress', -- 'in_progress', 'completed', 'abandoned'
    notes TEXT
);

-- Execution items (tracking each item's completion)
CREATE TABLE list_execution_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID REFERENCES list_executions(id) ON DELETE CASCADE,
    list_item_id UUID REFERENCES list_items(id),
    
    -- Completion data
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'completed', 'skipped'
    completed_at TIMESTAMPTZ,
    completed_by_id UUID REFERENCES users(id),
    
    -- Additional data
    notes TEXT,
    photo_urls TEXT[],
    skip_reason TEXT,
    
    -- Time tracking
    started_at TIMESTAMPTZ,
    duration_seconds INTEGER
);

-- Indexes
CREATE INDEX idx_lists_creator ON lists(created_by_id);
CREATE INDEX idx_lists_site ON lists(site_id);
CREATE INDEX idx_lists_category ON lists(category);
CREATE INDEX idx_executions_user ON list_executions(executed_by_id);
CREATE INDEX idx_executions_status ON list_executions(status);
```

## 🔧 Technical Implementation

### 1. List Parser
```python
# parsers/list_parser.py
import re
from typing import List, Dict, Optional

class ListParser:
    """Parse natural language list creation requests."""
    
    def parse_list_creation(self, message: str) -> Optional[Dict]:
        """Parse a list creation request."""
        
        # Patterns for list creation
        patterns = [
            r"create (?:a )?(.+?) (?:check)?list:?\s*(.+)",
            r"new (.+?) list:?\s*(.+)",
            r"(.+?) checklist:?\s*(.+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                list_name = match.group(1).strip()
                items_text = match.group(2).strip()
                
                # Parse items (comma, semicolon, or line separated)
                items = self._parse_items(items_text)
                
                return {
                    'type': 'list_creation',
                    'name': list_name,
                    'items': items,
                    'category': self._infer_category(list_name),
                    'site': self._extract_site(message)
                }
        
        return None
    
    def _parse_items(self, text: str) -> List[str]:
        """Parse items from text."""
        # Try different separators
        if ',' in text:
            items = [item.strip() for item in text.split(',')]
        elif ';' in text:
            items = [item.strip() for item in text.split(';')]
        elif '\n' in text:
            items = [item.strip() for item in text.split('\n')]
        else:
            # Assume single item
            items = [text.strip()]
        
        # Filter empty items
        return [item for item in items if item]
```

### 2. List Manager
```python
# services/list_manager.py
from database import db_manager
from models import List, ListItem, ListExecution

class ListManager:
    """Manage list operations."""
    
    async def create_list(self, user_id: str, name: str, 
                         items: List[str], **kwargs) -> List:
        """Create a new list with items."""
        with db_manager.get_session() as session:
            # Create list
            list_obj = List(
                name=name,
                created_by_id=user_id,
                category=kwargs.get('category', 'general'),
                site_id=kwargs.get('site_id'),
                list_type=kwargs.get('list_type', 'checklist')
            )
            session.add(list_obj)
            session.flush()
            
            # Add items
            for position, item_text in enumerate(items):
                item = ListItem(
                    list_id=list_obj.id,
                    title=item_text,
                    position=position
                )
                session.add(item)
            
            session.commit()
            return list_obj
    
    async def start_execution(self, list_id: str, user_id: str) -> ListExecution:
        """Start executing a list."""
        with db_manager.get_session() as session:
            # Get list and items
            list_obj = session.query(List).filter_by(id=list_id).first()
            items = session.query(ListItem).filter_by(
                list_id=list_id
            ).order_by(ListItem.position).all()
            
            # Create execution
            execution = ListExecution(
                list_id=list_id,
                executed_by_id=user_id,
                site_id=list_obj.site_id,
                total_items=len(items)
            )
            session.add(execution)
            session.commit()
            
            return execution
    
    async def convert_to_tasks(self, list_id: str, assignee_id: str) -> List[Task]:
        """Convert a list to individual tasks."""
        # Implementation for converting list items to tasks
        pass
```

### 3. Telegram Bot Integration
```python
# integrations/telegram/list_handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def handle_list_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle list creation from Telegram."""
    # Parse the message
    parser = ListParser()
    parsed = parser.parse_list_creation(update.message.text)
    
    if parsed:
        # Create the list
        list_obj = await list_manager.create_list(
            user_id=context.user_data['user_id'],
            **parsed
        )
        
        # Show confirmation with actions
        keyboard = [
            [
                InlineKeyboardButton("▶️ Start", 
                                   callback_data=f"start_list_{list_obj.id}"),
                InlineKeyboardButton("📝 Edit", 
                                   callback_data=f"edit_list_{list_obj.id}"),
            ],
            [
                InlineKeyboardButton("🔄 Convert to Tasks", 
                                   callback_data=f"convert_list_{list_obj.id}"),
                InlineKeyboardButton("📋 View Lists", 
                                   callback_data="view_lists"),
            ]
        ]
        
        await update.message.reply_text(
            f"✅ List created: {list_obj.name}\n"
            f"Items: {len(parsed['items'])}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
```

## 🎯 Advanced Features

### 1. Smart Templates
- Auto-suggest items based on list name
- Learn from completed lists
- Seasonal adjustments (winter vs summer checks)

### 2. Conditional Logic
- "If oil is low, add 'order oil' task"
- Skip sections based on equipment type
- Dynamic lists based on conditions

### 3. Integration Features
- Export lists to PDF/Excel
- Share via link
- Sync with external checklists
- QR codes for quick access

### 4. Analytics
- Average completion time per list
- Most skipped items
- Completion rates by user/site
- Optimize list order

## 🧪 Success Metrics

- [ ] 80% of daily tasks use lists
- [ ] < 2 seconds to load a list
- [ ] 95% completion rate for started lists
- [ ] 50% reduction in task creation time