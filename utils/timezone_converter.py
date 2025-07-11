"""Timezone conversion utilities for task parsing."""

from datetime import datetime
from typing import Dict, Optional, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.timezone_config import get_user_timezone


def convert_time_between_users(
    dt: datetime,
    time_str: Optional[str],
    from_user: str,
    to_user: str,
    is_date_only: bool = False,
) -> Tuple[str, str]:
    """Convert date/time from one user's timezone to another's.

    Args:
        dt: Base datetime object (in UTC or naive)
        time_str: Time string in HH:MM format (optional)
        from_user: Username of the person setting the time
        to_user: Username of the person receiving the task
        is_date_only: If True, only return date without time

    Returns:
        Tuple of (date_str, time_str) in YYYY-MM-DD and HH:MM formats
    """
    # Get timezones
    from_tz = get_user_timezone(from_user)
    to_tz = get_user_timezone(to_user)

    # If we have a time string, parse it and combine with date
    if time_str and not is_date_only:
        hour, minute = map(int, time_str.split(":"))
        # Create datetime in from_user's timezone
        dt_with_time = dt.replace(hour=hour, minute=minute)
        dt_from = dt_with_time.replace(tzinfo=from_tz)

        # Convert to to_user's timezone
        dt_to = dt_from.astimezone(to_tz)

        return dt_to.strftime("%Y-%m-%d"), dt_to.strftime("%H:%M")
    else:
        # For date-only tasks, just use the date as-is
        return dt.strftime("%Y-%m-%d"), ""


def process_task_with_timezones(task_json: Dict, assigner: str = "Colin") -> Dict:
    """Process a parsed task JSON to handle timezone conversions.

    Args:
        task_json: The parsed task dictionary
        assigner: The person who assigned the task (default: Colin)

    Returns:
        Updated task dictionary with timezone-adjusted times
    """
    assignee = task_json.get("assignee", "Colin")
    
    # Check timezone context from LLM
    timezone_context = task_json.get("timezone_context", "assigner_local")
    
    # If times are already in a specific timezone (not assigner's local), don't convert
    if timezone_context != "assigner_local":
        # Just add timezone info for reference
        task_json["timezone_info"] = {
            "times_are_in": timezone_context,
            "assigner_tz": str(get_user_timezone(assigner)),
            "assignee_tz": str(get_user_timezone(assignee)),
            "converted": False,
        }
        return task_json

    # If assigner and assignee are the same, no conversion needed
    if assigner == assignee:
        return task_json

    # Get current date as base (this will be in assigner's context)
    base_date = datetime.strptime(task_json["due_date"], "%Y-%m-%d")

    # Convert due date/time only if in assigner's local timezone
    due_time = task_json.get("due_time", "")
    if due_time:
        due_date, due_time = convert_time_between_users(
            base_date, due_time, assigner, assignee
        )
        task_json["due_date"] = due_date
        task_json["due_time"] = due_time

    # Convert reminder date/time if present
    reminder_date = task_json.get("reminder_date")
    reminder_time = task_json.get("reminder_time")

    if reminder_date and reminder_time:
        reminder_base = datetime.strptime(reminder_date, "%Y-%m-%d")
        reminder_date, reminder_time = convert_time_between_users(
            reminder_base, reminder_time, assigner, assignee
        )
        task_json["reminder_date"] = reminder_date
        task_json["reminder_time"] = reminder_time

    # Add timezone info to the task for clarity
    task_json["timezone_info"] = {
        "assigner_tz": str(get_user_timezone(assigner)),
        "assignee_tz": str(get_user_timezone(assignee)),
        "converted": True,
    }

    return task_json
