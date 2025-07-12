# Database Backend & Persistence

## Overview
Replace Google Sheets with a proper PostgreSQL database to enable advanced querying, better performance, and data integrity.

## Status: READY TO IMPLEMENT

## 🎯 What We Found from 10NZ_FLRTS

We can reuse substantial work from your 10NZ_FLRTS project:

1. **Database Schema** - Complete PostgreSQL schema with proper indexes
2. **SQLAlchemy Models** - Well-structured ORM models
3. **Supabase Configuration** - You already have a Supabase instance!
4. **Connection Patterns** - Database manager with session handling

### Files Created:
- `schema_from_FLRTS.sql` - Adapted schema for task parsing
- `models.py` - SQLAlchemy models for all entities
- `database.py` - Connection management and session handling
- `setup_guide.md` - Complete setup instructions
- `migrate_from_sheets.py` - Script to migrate existing Google Sheets data
- `generate_test_data.py` - Generate realistic test data for development

## 📦 Data Migration Options

### Option 1: Migrate Existing Test Data
```bash
# Dry run first to see what will be migrated
python migrate_from_sheets.py --dry-run

# Run actual migration
python migrate_from_sheets.py --init-db
```

### Option 2: Generate Fresh Test Data
```bash
# Generate 100 test tasks with history
python generate_test_data.py --count 100 --init-db

# Preview what will be created
python generate_test_data.py --count 50 --dry-run
```

Both options create:
- Tasks with various states (pending, completed, overdue)
- Full task history/audit trail
- Scheduled notifications for upcoming tasks
- Realistic timing and assignee distribution

### Prerequisites
- Phase 2 complete (multi-user support working)
- User profile system implemented
- Timezone handling tested and working

### 🎯 Target Features

1. **PostgreSQL Database Schema**
   - Normalized schema with proper relationships
   - Support for task history and audit trails
   - Optimized for common queries
   - Files: Create `database/schema.sql`

2. **Data Migration from Google Sheets**
   - Export existing tasks from Google Sheets
   - Transform to normalized database format
   - Preserve all historical data
   - Validate data integrity after migration
   - Files: Create `database/migrate_from_sheets.py`

3. **Data Access Layer**
   - ORM models for all entities (SQLAlchemy)
   - Repository pattern for data access
   - Connection pooling for performance
   - Transaction support
   - Files: Create `database/models.py`, `database/repositories.py`

4. **Query API**
   - RESTful endpoints for task operations
   - Filter by assignee, date range, status, site
   - Pagination for large result sets
   - Search functionality
   - Files: Create `api/tasks.py`

5. **Backup & Recovery**
   - Automated daily backups
   - Point-in-time recovery
   - Export to CSV/JSON
   - Disaster recovery procedures
   - Files: Create `database/backup.py`

### 📊 Database Schema Design

```sql
-- Core tables
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    role VARCHAR(50) NOT NULL DEFAULT 'technician',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE sites (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(255),
    timezone VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    external_id UUID DEFAULT gen_random_uuid(),
    assigner_id INTEGER REFERENCES users(id) NOT NULL,
    assignee_id INTEGER REFERENCES users(id) NOT NULL,
    site_id INTEGER REFERENCES sites(id),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    due_date DATE,
    due_time TIME,
    reminder_date DATE,
    reminder_time TIME,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'normal',
    repeat_interval VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    INDEX idx_assignee_status (assignee_id, status),
    INDEX idx_due_date (due_date),
    INDEX idx_created_at (created_at)
);

CREATE TABLE task_history (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) NOT NULL,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    action VARCHAR(50) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_task_history (task_id, created_at)
);

CREATE TABLE task_comments (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) NOT NULL,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    comment TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 🔄 Migration Strategy

1. **Phase 1: Parallel Operation**
   - Continue writing to Google Sheets
   - Also write to PostgreSQL
   - Compare data for validation
   - Duration: 1 week

2. **Phase 2: Database Primary**
   - PostgreSQL becomes primary storage
   - Google Sheets receives backup copies
   - Monitor for issues
   - Duration: 2 weeks

3. **Phase 3: Full Migration**
   - Disconnect Google Sheets
   - PostgreSQL only
   - Keep Sheets export capability

### 🧪 Performance Requirements
- Task creation: < 100ms
- Query response: < 200ms for 10k records
- Concurrent users: Support 100+
- Database size: Handle 1M+ tasks
- Backup time: < 5 minutes for full backup

### 🔧 Technical Implementation

1. **Connection Management**
   ```python
   # database/connection.py
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker
   
   engine = create_engine(
       DATABASE_URL,
       pool_size=20,
       max_overflow=40,
       pool_pre_ping=True
   )
   SessionLocal = sessionmaker(bind=engine)
   ```

2. **Repository Pattern**
   ```python
   # database/repositories.py
   class TaskRepository:
       def create(self, task_data: dict) -> Task:
           """Create new task with history tracking"""
           
       def get_by_assignee(self, user_id: int, 
                          status: str = None) -> List[Task]:
           """Get tasks for specific assignee"""
           
       def update_status(self, task_id: int, 
                        new_status: str, user_id: int) -> Task:
           """Update task status with audit trail"""
   ```

### 🎯 Success Metrics
- [ ] Zero data loss during migration
- [ ] All queries complete in < 200ms
- [ ] 99.9% uptime
- [ ] Automated backups running daily
- [ ] Support for 1M+ tasks

### 🚨 Risk Mitigation
1. **Data Loss**: Triple backup strategy (DB, filesystem, cloud)
2. **Performance**: Index optimization and query analysis
3. **Migration Errors**: Extensive testing with production data copy
4. **Downtime**: Blue-green deployment strategy