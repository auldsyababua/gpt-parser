# Database Backend Setup Guide

This guide walks through setting up the PostgreSQL database backend using Supabase (or local PostgreSQL).

## Option 1: Using Existing Supabase Instance

Since you already have a Supabase instance from the 10NZ_FLRTS project, we can reuse it.

### 1. Environment Variables

Create or update your `.env` file with your Supabase credentials:

```bash
# Supabase Configuration
SUPABASE_URL=https://[your-project-ref].supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Direct Database Connection (from Supabase dashboard)
DATABASE_URL=postgresql://postgres.[project-ref]:[password]@[region].pooler.supabase.com:6543/postgres
# Or use the direct connection string:
SUPABASE_DB_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
```

### 2. Apply the Schema

Run the schema SQL file in Supabase:

1. Go to Supabase Dashboard > SQL Editor
2. Copy the contents of `schema_from_FLRTS.sql`
3. Run the query

Or use the Supabase CLI:

```bash
supabase db push --file scratch/1-database-backend/schema_from_FLRTS.sql
```

### 3. Using Supabase MCP

If you have the Supabase MCP configured:

```bash
# List tables
mcp supabase tables list

# Query tasks
mcp supabase query "SELECT * FROM tasks WHERE status = 'pending'"
```

## Option 2: Local PostgreSQL Setup

### 1. Install PostgreSQL

```bash
# macOS
brew install postgresql
brew services start postgresql

# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 2. Create Database

```bash
# Connect as postgres user
psql -U postgres

# Create database
CREATE DATABASE gpt_parser;

# Create user (optional)
CREATE USER gpt_parser_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE gpt_parser TO gpt_parser_user;
```

### 3. Apply Schema

```bash
psql -U postgres -d gpt_parser -f scratch/1-database-backend/schema_from_FLRTS.sql
```

## Python Setup

### 1. Install Dependencies

```bash
pip install sqlalchemy psycopg2-binary python-dotenv

# Optional: For Supabase client
pip install supabase
```

### 2. Initialize Database

```python
# Initialize the database with tables and seed data
from database import db_manager

# Create all tables
db_manager.init_db()

# Or just create tables without seed data
db_manager.create_tables()
```

### 3. Test Connection

```python
from database import db_manager
from models import User, Task

# Test query
with db_manager.get_session() as session:
    users = session.query(User).all()
    for user in users:
        print(f"User: {user.display_name} (@{user.telegram_username})")
```

## Integration with GPT-Parser

### 1. Update Task Creation

```python
# In assistants_api_runner.py or parsers/openai_assistant.py
from database import db_manager
from models import Task, User
import uuid
from datetime import datetime

async def save_task_to_database(parsed_task: dict, user_telegram_id: str):
    """Save parsed task to database instead of Google Sheets."""
    
    with db_manager.get_session() as session:
        # Get user
        assigner = session.query(User).filter_by(telegram_id=user_telegram_id).first()
        if not assigner:
            raise ValueError(f"User not found: {user_telegram_id}")
        
        # Get assignee
        assignee_name = parsed_task.get('assignee', 'Colin')
        assignee = session.query(User).filter_by(display_name=assignee_name).first()
        if not assignee:
            assignee = assigner  # Default to self-assignment
        
        # Create task
        task = Task(
            task_id_display=f"TASK-{int(datetime.now().timestamp())}",
            title=parsed_task.get('task', ''),
            original_message=parsed_task.get('original_message', ''),
            assigner_id=assigner.id,
            assignee_id=assignee.id,
            due_date=parsed_task.get('due_date'),
            due_time=parsed_task.get('due_time'),
            reminder_date=parsed_task.get('reminder_date'),
            reminder_time=parsed_task.get('reminder_time'),
            status='pending',
            priority=parsed_task.get('priority', 'normal'),
            parser_confidence=parsed_task.get('confidence'),
            parser_type='openai_assistant'
        )
        
        session.add(task)
        session.commit()
        
        return {
            'success': True,
            'task_id': str(task.id),
            'task_display_id': task.task_id_display
        }
```

### 2. Query Tasks

```python
# Get tasks for a user
def get_user_tasks(telegram_username: str, status: str = None):
    with db_manager.get_session() as session:
        query = session.query(Task).join(
            User, Task.assignee_id == User.id
        ).filter(
            User.telegram_username == telegram_username
        )
        
        if status:
            query = query.filter(Task.status == status)
        
        return [task.to_dict() for task in query.all()]
```

### 3. Task History Tracking

```python
from models import TaskHistory

def record_task_change(task_id: str, user_id: str, action: str, changes: dict):
    """Record task history entry."""
    with db_manager.get_session() as session:
        history = TaskHistory(
            task_id=task_id,
            user_id=user_id,
            action=action,
            new_values=changes,
            client_type='telegram_bot'
        )
        session.add(history)
        session.commit()
```

## Migration Strategy

### Phase 1: Parallel Operation (Current)
1. Keep Google Sheets integration
2. Also write to database
3. Compare results

### Phase 2: Database Primary
1. Read from database
2. Write to both database and Sheets
3. Sheets becomes backup

### Phase 3: Full Migration
1. Remove Google Sheets dependency
2. Database only
3. Optional: Export to Sheets functionality

## Testing

```python
# Test script
if __name__ == "__main__":
    # Test database connection
    from database import db_manager
    
    print("Testing database connection...")
    try:
        with db_manager.get_session() as session:
            session.execute("SELECT 1")
            print("✅ Database connected successfully!")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
    
    # Test models
    from models import User, Site, Task
    
    with db_manager.get_session() as session:
        user_count = session.query(User).count()
        site_count = session.query(Site).count()
        task_count = session.query(Task).count()
        
        print(f"\nDatabase contents:")
        print(f"- Users: {user_count}")
        print(f"- Sites: {site_count}")
        print(f"- Tasks: {task_count}")
```

## Next Steps

1. ✅ Set up database connection
2. ✅ Create schema
3. 🔄 Update task creation to use database
4. 🔄 Add task history tracking
5. 🔄 Implement query endpoints
6. 🔄 Create backup/export functionality