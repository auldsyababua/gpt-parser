-- ==========================================
-- GPT-Parser Database Schema (Adapted from 10NZ_FLRTS)
-- ==========================================
-- This is a simplified schema focused on task parsing and management

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==========================================
-- USERS TABLE (Simplified from flrts_users)
-- ==========================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_id VARCHAR(50) UNIQUE NOT NULL,
    telegram_username VARCHAR(100) UNIQUE NOT NULL,  -- e.g., 'colin_10netzero'
    display_name VARCHAR(100) NOT NULL,              -- e.g., 'Colin'
    email VARCHAR(255),
    timezone VARCHAR(50) NOT NULL DEFAULT 'America/Chicago',
    role VARCHAR(50) NOT NULL DEFAULT 'operator' CHECK (role IN ('admin', 'operator', 'viewer')),
    is_active BOOLEAN DEFAULT TRUE,
    -- Notification preferences
    notifications_enabled BOOLEAN DEFAULT TRUE,
    reminder_minutes_before INTEGER DEFAULT 30,
    daily_summary_enabled BOOLEAN DEFAULT FALSE,
    daily_summary_time TIME DEFAULT '08:00',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- SITES TABLE (Simplified)
-- ==========================================
CREATE TABLE IF NOT EXISTS sites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,  -- e.g., 'Site A', 'Site B'
    location VARCHAR(255),
    timezone VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- TASKS TABLE (Core table for parsed tasks)
-- ==========================================
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    -- Display ID for easy reference
    task_id_display VARCHAR(50) NOT NULL UNIQUE DEFAULT ('TASK-' || EXTRACT(EPOCH FROM NOW())::TEXT),
    
    -- Task core data
    title VARCHAR(500) NOT NULL,
    description TEXT,
    original_message TEXT NOT NULL,  -- The original unparsed message
    
    -- People involved
    assigner_id UUID NOT NULL REFERENCES users(id),
    assignee_id UUID NOT NULL REFERENCES users(id),
    
    -- Location
    site_id UUID REFERENCES sites(id),
    
    -- Temporal data
    due_date DATE,
    due_time TIME,
    due_datetime_utc TIMESTAMPTZ,  -- Combined UTC datetime for queries
    reminder_date DATE,
    reminder_time TIME,
    reminder_datetime_utc TIMESTAMPTZ,
    timezone_context VARCHAR(50),  -- If user specified a timezone
    
    -- Task metadata
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled', 'blocked')),
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    
    -- Parsing metadata
    parser_confidence DECIMAL(3,2),  -- 0.00 to 1.00
    parser_version VARCHAR(50),
    parser_type VARCHAR(50),  -- 'openai', 'groq', 'temporal_preprocessor'
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ
);

-- ==========================================
-- TASK HISTORY TABLE (Audit trail)
-- ==========================================
CREATE TABLE IF NOT EXISTS task_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    action VARCHAR(50) NOT NULL,  -- 'created', 'updated', 'status_changed', etc.
    
    -- Store the complete before/after state
    old_values JSONB,
    new_values JSONB,
    
    -- Specific change tracking
    field_changed VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    
    -- Metadata
    ip_address INET,
    user_agent TEXT,
    client_type VARCHAR(50),  -- 'telegram_bot', 'web_app', 'api'
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- NOTIFICATIONS TABLE (Track sent notifications)
-- ==========================================
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    
    notification_type VARCHAR(50) NOT NULL,  -- 'reminder', 'overdue', 'assigned', 'daily_summary'
    scheduled_for TIMESTAMPTZ NOT NULL,
    sent_at TIMESTAMPTZ,
    
    -- Delivery tracking
    status VARCHAR(50) NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'sent', 'delivered', 'failed', 'snoozed', 'cancelled')),
    delivery_channel VARCHAR(50) DEFAULT 'telegram',
    
    -- Interaction tracking
    read_at TIMESTAMPTZ,
    action_taken VARCHAR(50),  -- 'completed', 'snoozed_15min', 'snoozed_1hr', etc.
    action_taken_at TIMESTAMPTZ,
    
    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- PARSING ERRORS TABLE (Track failed parses)
-- ==========================================
CREATE TABLE IF NOT EXISTS parsing_errors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    original_message TEXT NOT NULL,
    error_type VARCHAR(100),
    error_message TEXT,
    parser_type VARCHAR(50),
    raw_response TEXT,  -- Store the raw LLM response if available
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- INDEXES FOR PERFORMANCE
-- ==========================================

-- Tasks indexes
CREATE INDEX idx_tasks_assignee_status ON tasks(assignee_id, status);
CREATE INDEX idx_tasks_due_datetime ON tasks(due_datetime_utc);
CREATE INDEX idx_tasks_reminder_datetime ON tasks(reminder_datetime_utc);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_tasks_site ON tasks(site_id);

-- Task history indexes
CREATE INDEX idx_task_history_task_id ON task_history(task_id, created_at);
CREATE INDEX idx_task_history_user_id ON task_history(user_id, created_at);

-- Notifications indexes
CREATE INDEX idx_notifications_scheduled ON notifications(scheduled_for, status);
CREATE INDEX idx_notifications_user ON notifications(user_id, status);
CREATE INDEX idx_notifications_task ON notifications(task_id);

-- ==========================================
-- HELPER FUNCTIONS
-- ==========================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ==========================================
-- TRIGGERS
-- ==========================================

-- Auto-update updated_at for users
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-update updated_at for sites
CREATE TRIGGER update_sites_updated_at BEFORE UPDATE ON sites
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-update updated_at for tasks
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-update updated_at for notifications
CREATE TRIGGER update_notifications_updated_at BEFORE UPDATE ON notifications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- SEED DATA
-- ==========================================

-- Insert default users
INSERT INTO users (telegram_id, telegram_username, display_name, timezone, role) VALUES
    ('123456789', 'colin_10netzero', 'Colin', 'America/Los_Angeles', 'admin'),
    ('987654321', 'bryan_10netzero', 'Bryan', 'America/Chicago', 'operator'),
    ('456789123', 'joel_10netzero', 'Joel', 'America/Chicago', 'operator')
ON CONFLICT (telegram_username) DO NOTHING;

-- Insert default sites
INSERT INTO sites (name, location) VALUES
    ('Site A', 'Location A'),
    ('Site B', 'Location B'),
    ('Site C', 'Location C'),
    ('Site D', 'Location D')
ON CONFLICT (name) DO NOTHING;