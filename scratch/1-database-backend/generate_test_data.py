#!/usr/bin/env python3
"""
Generate test data for the GPT-Parser database.

This creates realistic test tasks with various states, dates, and assignees
to help test querying, notifications, and history features.
"""

import random
from datetime import datetime, timedelta, time
from typing import List
import logging

# Add parent directory to path for imports
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db_manager
from models import User, Site, Task, TaskHistory, Notification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestDataGenerator:
    """Generate test data for the database."""

    def __init__(self):
        self.users = []
        self.sites = []
        self.task_templates = [
            # Oil/maintenance tasks
            "Check oil levels",
            "Change oil",
            "Check coolant levels",
            "Replace air filters",
            "Check generator status",
            "Inspect belts and hoses",
            "Test emergency shutdown",
            "Clean radiator",
            "Check fuel levels",
            "Verify telemetry data",
            # Site management
            "Meet contractor",
            "Site inspection",
            "Security check",
            "Fence repair",
            "Clear vegetation",
            "Check flare operation",
            # Administrative
            "Submit weekly report",
            "Update maintenance log",
            "Order parts",
            "Schedule contractor",
            "Review invoices",
            "Update site documentation",
        ]

    def load_existing_data(self):
        """Load existing users and sites."""
        with db_manager.get_session() as session:
            self.users = session.query(User).filter(User.is_active == True).all()
            self.sites = session.query(Site).filter(Site.is_active == True).all()

            logger.info(f"Loaded {len(self.users)} users and {len(self.sites)} sites")

    def generate_tasks(self, count: int = 50) -> List[Task]:
        """Generate test tasks with various properties."""
        tasks = []
        now = datetime.utcnow()

        for i in range(count):
            # Random task template
            task_title = random.choice(self.task_templates)

            # Random site
            site = random.choice(self.sites + [None])  # Some tasks have no site
            if site:
                task_title += f" at {site.name}"

            # Random users
            assigner = random.choice(self.users)
            assignee = random.choice(self.users)

            # Random timing
            # Mix of past, present, and future tasks
            if i < count * 0.3:  # 30% overdue
                days_ago = random.randint(1, 30)
                due_date = (now - timedelta(days=days_ago)).date()
                status = random.choice(
                    ["pending", "pending", "completed"]
                )  # Some overdue are completed
            elif i < count * 0.6:  # 30% upcoming
                days_ahead = random.randint(1, 14)
                due_date = (now + timedelta(days=days_ahead)).date()
                status = "pending"
            else:  # 40% completed
                days_ago = random.randint(1, 60)
                due_date = (now - timedelta(days=days_ago)).date()
                status = "completed"

            # Random time of day
            hour = random.randint(6, 18)  # Working hours
            minute = random.choice([0, 15, 30, 45])
            due_time = time(hour, minute)

            # Combine to UTC datetime
            due_datetime = datetime.combine(due_date, due_time)

            # Set reminder 30 minutes before
            reminder_datetime = due_datetime - timedelta(minutes=30)

            # Random priority
            if "emergency" in task_title.lower() or "urgent" in task_title.lower():
                priority = "urgent"
            elif random.random() < 0.2:
                priority = "high"
            elif random.random() < 0.6:
                priority = "normal"
            else:
                priority = "low"

            task = Task(
                task_id_display=f"TEST-{now.timestamp()}-{i}",
                title=task_title,
                description=f"Test task generated for {assignee.display_name}",
                original_message=f"Test: {task_title} for {assignee.display_name}",
                assigner_id=assigner.id,
                assignee_id=assignee.id,
                site_id=site.id if site else None,
                due_date=due_date,
                due_time=due_time,
                due_datetime_utc=due_datetime,
                reminder_date=reminder_datetime.date(),
                reminder_time=reminder_datetime.time(),
                reminder_datetime_utc=reminder_datetime,
                status=status,
                priority=priority,
                parser_confidence=random.uniform(0.7, 1.0),
                parser_type="test_generator",
                created_at=now - timedelta(days=random.randint(0, 90)),
            )

            if status == "completed":
                task.completed_at = due_datetime + timedelta(hours=random.randint(0, 8))

            tasks.append(task)

        return tasks

    def generate_history(self, tasks: List[Task]) -> List[TaskHistory]:
        """Generate history entries for tasks."""
        history_entries = []

        for task in tasks:
            # Creation entry
            history_entries.append(
                TaskHistory(
                    task_id=task.id,
                    user_id=task.assigner_id,
                    action="created",
                    new_values={
                        "title": task.title,
                        "assignee": task.assignee_id,
                        "status": "pending",
                    },
                    client_type="test_generator",
                    created_at=task.created_at,
                )
            )

            # Status changes for completed tasks
            if task.status == "completed":
                history_entries.append(
                    TaskHistory(
                        task_id=task.id,
                        user_id=task.assignee_id,
                        action="status_changed",
                        old_values={"status": "pending"},
                        new_values={"status": "completed"},
                        field_changed="status",
                        old_value="pending",
                        new_value="completed",
                        client_type="test_generator",
                        created_at=task.completed_at,
                    )
                )

        return history_entries

    def generate_notifications(self, tasks: List[Task]) -> List[Notification]:
        """Generate notification entries for upcoming tasks."""
        notifications = []
        now = datetime.utcnow()

        for task in tasks:
            if task.status == "pending" and task.reminder_datetime_utc:
                # Only create notifications for future reminders
                if task.reminder_datetime_utc > now:
                    notification = Notification(
                        task_id=task.id,
                        user_id=task.assignee_id,
                        notification_type="reminder",
                        scheduled_for=task.reminder_datetime_utc,
                        status="scheduled",
                        delivery_channel="telegram",
                    )
                    notifications.append(notification)

        return notifications

    def generate_all(self, task_count: int = 50, dry_run: bool = True):
        """Generate all test data."""
        logger.info(f"Generating {task_count} test tasks (dry_run={dry_run})")

        # Load existing data
        self.load_existing_data()

        if not self.users or not self.sites:
            logger.error("No users or sites found. Run database initialization first.")
            return

        # Generate data
        tasks = self.generate_tasks(task_count)
        history_entries = self.generate_history(tasks)
        notifications = self.generate_notifications(tasks)

        logger.info("Generated:")
        logger.info(f"  - {len(tasks)} tasks")
        logger.info(f"  - {len(history_entries)} history entries")
        logger.info(f"  - {len(notifications)} notifications")

        if not dry_run:
            with db_manager.get_session() as session:
                session.add_all(tasks)
                session.add_all(history_entries)
                session.add_all(notifications)
                session.commit()
                logger.info("Test data committed to database")
        else:
            logger.info("Dry run completed (no changes made)")

            # Show sample data
            logger.info("\nSample tasks:")
            for task in tasks[:5]:
                logger.info(f"  - {task.title} | {task.status} | Due: {task.due_date}")


def main():
    """Run the test data generator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate test data for GPT-Parser database"
    )
    parser.add_argument(
        "--count", type=int, default=50, help="Number of tasks to generate"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run without making changes"
    )
    parser.add_argument(
        "--init-db", action="store_true", help="Initialize database first"
    )
    args = parser.parse_args()

    if args.init_db:
        logger.info("Initializing database...")
        db_manager.init_db()

    generator = TestDataGenerator()
    generator.generate_all(task_count=args.count, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
