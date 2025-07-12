#!/usr/bin/env python3
"""
Migrate existing task data from Google Sheets to PostgreSQL database.

This script:
1. Fetches data from Google Sheets via the Apps Script webhook
2. Transforms it to match our database schema
3. Inserts it into the PostgreSQL database
4. Maintains data integrity and relationships
"""

import os
import requests
from datetime import datetime
from typing import List, Dict, Optional
import logging
from dotenv import load_dotenv

# Add parent directory to path for imports
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db_manager
from models import User, Site, Task, TaskHistory

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SheetsMigrator:
    """Handles migration of tasks from Google Sheets to PostgreSQL."""

    def __init__(self):
        self.sheets_url = os.getenv("GOOGLE_APPS_SCRIPT_URL")
        if not self.sheets_url:
            raise ValueError("GOOGLE_APPS_SCRIPT_URL not found in environment")

        # Cache for user and site lookups
        self.users_cache = {}
        self.sites_cache = {}
        self._load_cache()

    def _load_cache(self):
        """Load users and sites into cache for quick lookup."""
        with db_manager.get_session() as session:
            # Cache users by display name
            users = session.query(User).all()
            for user in users:
                self.users_cache[user.display_name.lower()] = user
                # Also cache by telegram username
                self.users_cache[user.telegram_username] = user

            # Cache sites by name
            sites = session.query(Site).all()
            for site in sites:
                self.sites_cache[site.name.lower()] = site

            logger.info(
                f"Loaded {len(self.users_cache)} users and {len(self.sites_cache)} sites"
            )

    def fetch_sheets_data(self) -> List[Dict]:
        """Fetch all tasks from Google Sheets."""
        logger.info("Fetching data from Google Sheets...")

        # Modify the webhook URL to get all tasks
        # You might need to update your Apps Script to support this
        fetch_url = self.sheets_url.replace("/exec", "/exec?action=getAllTasks")

        try:
            response = requests.get(fetch_url, timeout=30)
            response.raise_for_status()

            data = response.json()
            if data.get("success"):
                tasks = data.get("tasks", [])
                logger.info(f"Fetched {len(tasks)} tasks from Sheets")
                return tasks
            else:
                logger.error(f"Failed to fetch tasks: {data.get('error')}")
                return []

        except Exception as e:
            logger.error(f"Error fetching from Sheets: {e}")
            return []

    def parse_datetime(self, date_str: Optional[str], time_str: Optional[str]) -> tuple:
        """Parse date and time strings from Sheets format."""
        parsed_date = None
        parsed_time = None
        parsed_datetime = None

        if date_str:
            try:
                # Handle various date formats from Sheets
                for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]:
                    try:
                        parsed_date = datetime.strptime(date_str, fmt).date()
                        break
                    except ValueError:
                        continue
            except Exception as e:
                logger.warning(f"Could not parse date '{date_str}': {e}")

        if time_str:
            try:
                # Handle various time formats
                for fmt in ["%H:%M", "%I:%M %p", "%H:%M:%S"]:
                    try:
                        parsed_time = datetime.strptime(time_str, fmt).time()
                        break
                    except ValueError:
                        continue
            except Exception as e:
                logger.warning(f"Could not parse time '{time_str}': {e}")

        # Combine into UTC datetime if both present
        if parsed_date and parsed_time:
            parsed_datetime = datetime.combine(parsed_date, parsed_time)

        return parsed_date, parsed_time, parsed_datetime

    def get_or_create_user(self, session, name: str) -> Optional[User]:
        """Get user by name, create if necessary."""
        if not name:
            return None

        name_lower = name.lower()

        # Check cache first
        if name_lower in self.users_cache:
            # Merge the cached object with the session
            return session.merge(self.users_cache[name_lower])

        # Try to find in database
        user = session.query(User).filter(User.display_name.ilike(f"%{name}%")).first()

        if not user:
            # Create a placeholder user
            logger.warning(f"Creating placeholder user for: {name}")
            user = User(
                telegram_id=f"placeholder_{name_lower}",
                telegram_username=f"placeholder_{name_lower}",
                display_name=name,
                timezone="America/Chicago",  # Default timezone
                role="operator",
            )
            session.add(user)
            session.flush()  # Get the ID without committing
            self.users_cache[name_lower] = user

        return user

    def get_or_create_site(self, session, site_name: str) -> Optional[Site]:
        """Get site by name, create if necessary."""
        if not site_name:
            return None

        site_name_lower = site_name.lower()

        # Check cache first
        if site_name_lower in self.sites_cache:
            return session.merge(self.sites_cache[site_name_lower])

        # Try to find in database
        site = session.query(Site).filter(Site.name.ilike(f"%{site_name}%")).first()

        if not site:
            # Create the site
            logger.warning(f"Creating new site: {site_name}")
            site = Site(name=site_name, location=f"Location for {site_name}")
            session.add(site)
            session.flush()
            self.sites_cache[site_name_lower] = site

        return site

    def transform_task(self, session, sheets_task: Dict) -> Optional[Task]:
        """Transform a Sheets task to database Task model."""
        try:
            # Get assigner (default to Colin if not specified)
            assigner_name = sheets_task.get("assigner", "Colin")
            assigner = self.get_or_create_user(session, assigner_name)

            # Get assignee
            assignee_name = sheets_task.get("assignee", sheets_task.get("assigned_to"))
            if not assignee_name:
                logger.warning(f"No assignee for task: {sheets_task}")
                return None
            assignee = self.get_or_create_user(session, assignee_name)

            # Get site if specified
            site = None
            site_name = sheets_task.get("site") or sheets_task.get("location")
            if site_name:
                site = self.get_or_create_site(session, site_name)

            # Parse dates and times
            due_date, due_time, due_datetime = self.parse_datetime(
                sheets_task.get("due_date"), sheets_task.get("due_time")
            )

            reminder_date, reminder_time, reminder_datetime = self.parse_datetime(
                sheets_task.get("reminder_date"), sheets_task.get("reminder_time")
            )

            # Create task
            task = Task(
                task_id_display=sheets_task.get(
                    "id", f"MIGRATED-{datetime.now().timestamp()}"
                ),
                title=sheets_task.get(
                    "task", sheets_task.get("title", "Untitled Task")
                ),
                description=sheets_task.get("description"),
                original_message=sheets_task.get("original_message", ""),
                assigner_id=assigner.id,
                assignee_id=assignee.id,
                site_id=site.id if site else None,
                due_date=due_date,
                due_time=due_time,
                due_datetime_utc=due_datetime,
                reminder_date=reminder_date,
                reminder_time=reminder_time,
                reminder_datetime_utc=reminder_datetime,
                timezone_context=sheets_task.get("timezone"),
                status=sheets_task.get("status", "pending").lower(),
                priority=sheets_task.get("priority", "normal").lower(),
                parser_confidence=sheets_task.get("confidence"),
                parser_type="sheets_migration",
                created_at=(
                    datetime.fromisoformat(sheets_task["timestamp"])
                    if "timestamp" in sheets_task
                    else datetime.utcnow()
                ),
            )

            return task

        except Exception as e:
            logger.error(f"Error transforming task {sheets_task}: {e}")
            return None

    def migrate(self, dry_run: bool = True):
        """Run the migration."""
        logger.info(f"Starting migration (dry_run={dry_run})")

        # Fetch data from Sheets
        sheets_tasks = self.fetch_sheets_data()
        if not sheets_tasks:
            logger.warning("No tasks to migrate")
            return

        # Transform and insert tasks
        successful = 0
        failed = 0

        with db_manager.get_session() as session:
            for sheets_task in sheets_tasks:
                task = self.transform_task(session, sheets_task)

                if task:
                    if not dry_run:
                        session.add(task)

                        # Add creation history
                        history = TaskHistory(
                            task_id=task.id,
                            user_id=task.assigner_id,
                            action="migrated_from_sheets",
                            new_values=sheets_task,
                            client_type="migration_script",
                        )
                        session.add(history)

                    successful += 1
                    logger.info(f"Migrated task: {task.title}")
                else:
                    failed += 1

            if not dry_run:
                session.commit()
                logger.info("Migration committed to database")
            else:
                logger.info("Dry run completed (no changes made)")

        logger.info(f"Migration complete: {successful} successful, {failed} failed")
        return successful, failed


def main():
    """Run the migration."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate tasks from Google Sheets to PostgreSQL"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run without making changes"
    )
    parser.add_argument(
        "--init-db", action="store_true", help="Initialize database before migration"
    )
    args = parser.parse_args()

    if args.init_db:
        logger.info("Initializing database...")
        db_manager.init_db()

    migrator = SheetsMigrator()
    migrator.migrate(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
