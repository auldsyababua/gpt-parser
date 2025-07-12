"""SQLAlchemy models for GPT-Parser database."""

from datetime import datetime
import uuid
from enum import Enum
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    ForeignKey,
    Float,
    JSON,
    Date,
    Time,
    Boolean,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class NotificationStatus(str, Enum):
    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    SNOOZED = "snoozed"
    CANCELLED = "cancelled"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(String(50), unique=True, nullable=False)
    telegram_username = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    email = Column(String(255))
    timezone = Column(String(50), nullable=False, default="America/Chicago")
    role = Column(String(50), nullable=False, default=UserRole.OPERATOR)
    is_active = Column(Boolean, default=True)

    # Notification preferences
    notifications_enabled = Column(Boolean, default=True)
    reminder_minutes_before = Column(Integer, default=30)
    daily_summary_enabled = Column(Boolean, default=False)
    daily_summary_time = Column(Time, default="08:00")

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    assigned_tasks = relationship(
        "Task", foreign_keys="Task.assignee_id", back_populates="assignee"
    )
    created_tasks = relationship(
        "Task", foreign_keys="Task.assigner_id", back_populates="assigner"
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "telegram_id": self.telegram_id,
            "telegram_username": self.telegram_username,
            "display_name": self.display_name,
            "email": self.email,
            "timezone": self.timezone,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Site(Base):
    __tablename__ = "sites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    location = Column(String(255))
    timezone = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    tasks = relationship("Task", back_populates="site")

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "location": self.location,
            "timezone": self.timezone,
            "is_active": self.is_active,
        }


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id_display = Column(String(50), unique=True, nullable=False)

    # Core task data
    title = Column(String(500), nullable=False)
    description = Column(Text)
    original_message = Column(Text, nullable=False)

    # People
    assigner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Location
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"))

    # Temporal data
    due_date = Column(Date)
    due_time = Column(Time)
    due_datetime_utc = Column(DateTime(timezone=True))
    reminder_date = Column(Date)
    reminder_time = Column(Time)
    reminder_datetime_utc = Column(DateTime(timezone=True))
    timezone_context = Column(String(50))

    # Metadata
    status = Column(String(50), nullable=False, default=TaskStatus.PENDING)
    priority = Column(String(20), default=TaskPriority.NORMAL)

    # Parsing metadata
    parser_confidence = Column(Float)
    parser_version = Column(String(50))
    parser_type = Column(String(50))

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    completed_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))

    # Relationships
    assigner = relationship(
        "User", foreign_keys=[assigner_id], back_populates="created_tasks"
    )
    assignee = relationship(
        "User", foreign_keys=[assignee_id], back_populates="assigned_tasks"
    )
    site = relationship("Site", back_populates="tasks")
    history = relationship(
        "TaskHistory", back_populates="task", cascade="all, delete-orphan"
    )
    notifications = relationship(
        "Notification", back_populates="task", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "task_id_display": self.task_id_display,
            "title": self.title,
            "description": self.description,
            "original_message": self.original_message,
            "assigner_id": str(self.assigner_id),
            "assignee_id": str(self.assignee_id),
            "site_id": str(self.site_id) if self.site_id else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "due_time": self.due_time.isoformat() if self.due_time else None,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TaskHistory(Base):
    __tablename__ = "task_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)

    # Change tracking
    old_values = Column(JSON)
    new_values = Column(JSON)
    field_changed = Column(String(100))
    old_value = Column(Text)
    new_value = Column(Text)

    # Metadata
    ip_address = Column(INET)
    user_agent = Column(Text)
    client_type = Column(String(50))

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    task = relationship("Task", back_populates="history")
    user = relationship("User")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    notification_type = Column(String(50), nullable=False)
    scheduled_for = Column(DateTime(timezone=True), nullable=False)
    sent_at = Column(DateTime(timezone=True))

    # Delivery tracking
    status = Column(String(50), nullable=False, default=NotificationStatus.SCHEDULED)
    delivery_channel = Column(String(50), default="telegram")

    # Interaction tracking
    read_at = Column(DateTime(timezone=True))
    action_taken = Column(String(50))
    action_taken_at = Column(DateTime(timezone=True))

    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    task = relationship("Task", back_populates="notifications")
    user = relationship("User")


class ParsingError(Base):
    __tablename__ = "parsing_errors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    original_message = Column(Text, nullable=False)
    error_type = Column(String(100))
    error_message = Column(Text)
    parser_type = Column(String(50))
    raw_response = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    user = relationship("User")
