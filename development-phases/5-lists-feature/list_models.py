"""SQLAlchemy models for Lists feature."""

from datetime import datetime
import uuid
from enum import Enum
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    ForeignKey,
    Integer,
    Boolean,
    Date,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

# Import Base from the main models
from models import Base


class ListType(str, Enum):
    CHECKLIST = "checklist"  # Simple check-off items
    TEMPLATE = "template"  # Convert to tasks
    SEQUENTIAL = "sequential"  # Must complete in order
    CONDITIONAL = "conditional"  # Items depend on previous


class ListCategory(str, Enum):
    INSPECTION = "inspection"
    MAINTENANCE = "maintenance"
    SAFETY = "safety"
    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    GENERAL = "general"


class ListExecutionStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    PAUSED = "paused"


class ListItemStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class List(Base):
    __tablename__ = "lists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    list_id_display = Column(
        String(50),
        unique=True,
        nullable=False,
        default=lambda: f"LIST-{int(datetime.now().timestamp())}",
    )

    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Metadata
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"))
    category = Column(String(50), default=ListCategory.GENERAL)
    list_type = Column(String(50), default=ListType.CHECKLIST)

    # Recurrence
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(50))  # 'daily', 'weekly', 'monthly', 'custom'
    recurrence_days = Column(ARRAY(Integer))  # [1,3,5] for Mon,Wed,Fri
    next_occurrence = Column(Date)

    # Status
    is_active = Column(Boolean, default=True)
    is_template = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)  # Can other users use this template

    # Estimates
    estimated_duration_minutes = Column(Integer)  # Total time to complete

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_executed_at = Column(DateTime(timezone=True))

    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    site = relationship("Site")
    items = relationship(
        "ListItem",
        back_populates="list",
        cascade="all, delete-orphan",
        order_by="ListItem.position",
    )
    executions = relationship(
        "ListExecution", back_populates="list", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "list_id_display": self.list_id_display,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "list_type": self.list_type,
            "site_id": str(self.site_id) if self.site_id else None,
            "is_recurring": self.is_recurring,
            "is_template": self.is_template,
            "item_count": len(self.items) if self.items else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ListItem(Base):
    __tablename__ = "list_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    list_id = Column(
        UUID(as_uuid=True), ForeignKey("lists.id", ondelete="CASCADE"), nullable=False
    )

    # Item details
    title = Column(String(500), nullable=False)
    description = Column(Text)
    position = Column(Integer, nullable=False)  # Order in list

    # Task conversion settings (when converting list to tasks)
    default_assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    estimated_duration_minutes = Column(Integer)
    priority = Column(String(20), default="normal")

    # For conditional lists
    depends_on_item_id = Column(UUID(as_uuid=True), ForeignKey("list_items.id"))
    condition_type = Column(
        String(50)
    )  # 'if_completed', 'if_skipped', 'if_value_equals'
    condition_value = Column(String(255))  # Expected value for conditions

    # Metadata
    is_optional = Column(Boolean, default=False)
    requires_photo = Column(Boolean, default=False)
    requires_note = Column(Boolean, default=False)

    # Common values or ranges (for validation)
    expected_values = Column(ARRAY(String))  # ['OK', 'Low', 'Empty']
    min_value = Column(String(50))  # For numeric checks
    max_value = Column(String(50))

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    list = relationship("List", back_populates="items")
    default_assignee = relationship("User")
    depends_on = relationship("ListItem", remote_side=[id])

    def to_dict(self):
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "position": self.position,
            "is_optional": self.is_optional,
            "estimated_duration_minutes": self.estimated_duration_minutes,
        }


class ListExecution(Base):
    __tablename__ = "list_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    list_id = Column(UUID(as_uuid=True), ForeignKey("lists.id"), nullable=False)
    executed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"))

    # Timing
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))
    paused_at = Column(DateTime(timezone=True))

    # Progress
    total_items = Column(Integer, nullable=False)
    completed_items = Column(Integer, default=0)
    skipped_items = Column(Integer, default=0)
    current_item_position = Column(Integer, default=0)

    # Status
    status = Column(String(50), default=ListExecutionStatus.IN_PROGRESS)
    notes = Column(Text)

    # Context (weather, conditions, etc.)
    execution_context = Column(JSON)  # {"weather": "sunny", "temperature": 75}

    # Relationships
    list = relationship("List", back_populates="executions")
    executed_by = relationship("User")
    site = relationship("Site")
    items = relationship(
        "ListExecutionItem", back_populates="execution", cascade="all, delete-orphan"
    )

    @property
    def completion_percentage(self):
        if self.total_items == 0:
            return 0
        return int((self.completed_items / self.total_items) * 100)

    def to_dict(self):
        return {
            "id": str(self.id),
            "list_id": str(self.list_id),
            "status": self.status,
            "progress": f"{self.completed_items}/{self.total_items}",
            "completion_percentage": self.completion_percentage,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }


class ListExecutionItem(Base):
    __tablename__ = "list_execution_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("list_executions.id", ondelete="CASCADE"),
        nullable=False,
    )
    list_item_id = Column(
        UUID(as_uuid=True), ForeignKey("list_items.id"), nullable=False
    )

    # Completion data
    status = Column(String(50), default=ListItemStatus.PENDING)
    completed_at = Column(DateTime(timezone=True))
    completed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Data captured
    value = Column(
        String(255)
    )  # For items that capture values (e.g., "Oil Level: 75%")
    notes = Column(Text)
    photo_urls = Column(ARRAY(String))
    skip_reason = Column(Text)

    # Time tracking
    started_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)

    # Relationships
    execution = relationship("ListExecution", back_populates="items")
    list_item = relationship("ListItem")
    completed_by = relationship("User")

    def to_dict(self):
        return {
            "id": str(self.id),
            "list_item_id": str(self.list_item_id),
            "status": self.status,
            "value": self.value,
            "notes": self.notes,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }
