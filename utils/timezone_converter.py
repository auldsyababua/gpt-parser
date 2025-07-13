"""Timezone conversion utilities for task parsing."""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Optional, Tuple

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.timezone_config import get_user_timezone, normalize_username

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/timezone_converter.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


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
    logger = logging.getLogger(__name__)
    logger.info(
        f"[DEBUG] convert_time_between_users: INPUT - dt={dt}, time_str={time_str}, from_user={from_user}, to_user={to_user}"
    )

    # Get timezones using proper normalization
    from_tz = get_user_timezone(from_user)
    to_tz = get_user_timezone(to_user)

    logger.info(f"[DEBUG] convert_time_between_users: from_tz={from_tz}, to_tz={to_tz}")

    # If we have a time string, parse it and combine with date
    if time_str and not is_date_only:
        hour, minute = map(int, time_str.split(":"))
        logger.info(
            f"[DEBUG] convert_time_between_users: Parsed time - hour={hour}, minute={minute}"
        )

        # Create datetime in from_user's timezone
        dt_with_time = dt.replace(hour=hour, minute=minute)
        logger.info(f"[DEBUG] convert_time_between_users: dt_with_time={dt_with_time}")

        # The datetime is naive but represents time in from_user's timezone
        # With ZoneInfo, use replace() to attach timezone
        dt_from = dt_with_time.replace(tzinfo=from_tz)
        logger.info(f"[DEBUG] convert_time_between_users: dt_from (with tz)={dt_from}")

        # Convert to to_user's timezone
        dt_to = dt_from.astimezone(to_tz)
        logger.info(f"[DEBUG] convert_time_between_users: dt_to (converted)={dt_to}")

        result = (dt_to.strftime("%Y-%m-%d"), dt_to.strftime("%H:%M"))
        logger.info(f"[DEBUG] convert_time_between_users: RESULT = {result}")
        return result
    else:
        # For date-only tasks, just use the date as-is
        result = (dt.strftime("%Y-%m-%d"), "")
        logger.info(f"[DEBUG] convert_time_between_users: DATE-ONLY RESULT = {result}")
        return result


def process_task_with_timezones(task_json: Dict, assigner: str = "Colin") -> Dict:
    """Process a parsed task JSON to handle timezone conversions.

    Args:
        task_json: The parsed task dictionary
        assigner: The person who assigned the task (default: Colin)

    Returns:
        Updated task dictionary with timezone-adjusted times
    """
    logger = logging.getLogger(__name__)

    logger.info(
        f"[DEBUG] process_task_with_timezones: INPUT task_json = {json.dumps(task_json, indent=2)}"
    )
    logger.info(f"[DEBUG] process_task_with_timezones: assigner = '{assigner}'")

    # Get assigner's timezone
    assigner_tz = get_user_timezone(assigner)
    logger.info(f"[DEBUG] process_task_with_timezones: assigner_tz = {assigner_tz}")

    # Get assignee's timezone
    assignee = task_json.get("assignee", assigner)
    assignee_tz = get_user_timezone(assignee)
    logger.info(
        f"[DEBUG] process_task_with_timezones: assignee = '{assignee}', assignee_tz = {assignee_tz}"
    )

    # Check timezone context from LLM
    timezone_context = task_json.get("timezone_context", "assigner_local")
    logger.info(
        f"[DEBUG] process_task_with_timezones: timezone_context = '{timezone_context}'"
    )

    # If times are already in a specific timezone (not assigner's local), don't convert
    if timezone_context != "assigner_local":
        # Just add timezone info for reference
        task_json["timezone_info"] = {
            "times_are_in": timezone_context,
            "assigner_tz": str(assigner_tz),
            "assignee_tz": str(assignee_tz),
            "converted": False,
        }
        logger.info(
            "[DEBUG] process_task_with_timezones: timezone_context != assigner_local, skipping conversion"
        )
        return task_json

    # If assigner and assignee are the same person, no conversion needed
    # Use the normalization function to compare canonical names
    assigner_normalized = normalize_username(assigner)
    assignee_normalized = normalize_username(assignee)

    if assigner_normalized == assignee_normalized:
        logger.info(
            f"[DEBUG] process_task_with_timezones: same person - assigner '{assigner}' ({assigner_normalized}) == assignee '{assignee}' ({assignee_normalized}), no conversion needed"
        )
        # Add timezone info but mark as not converted
        task_json["timezone_info"] = {
            "assigner_tz": str(assigner_tz),
            "assignee_tz": str(assignee_tz),
            "converted": False,
        }
        return task_json

    # Get current date as base (this will be in assigner's context)
    base_date = datetime.strptime(task_json["due_date"], "%Y-%m-%d")

    # Convert due date/time only if in assigner's local timezone
    due_time = task_json.get("due_time", "")
    if due_time and assigner_normalized != assignee_normalized:
        logger.info(
            f"[DEBUG] process_task_with_timezones: Converting due time - {task_json['due_date']} {due_time} from {assigner} to {assignee}"
        )
        due_date, due_time = convert_time_between_users(
            base_date, due_time, assigner, assignee
        )
        logger.info(
            f"[DEBUG] process_task_with_timezones: Converted due time - {task_json['due_date']} {task_json.get('due_time')} -> {due_date} {due_time}"
        )
        task_json["due_date"] = due_date
        task_json["due_time"] = due_time

    # Convert reminder date/time if present
    reminder_date = task_json.get("reminder_date")
    reminder_time = task_json.get("reminder_time")

    if reminder_date and reminder_time and assigner_normalized != assignee_normalized:
        reminder_base = datetime.strptime(reminder_date, "%Y-%m-%d")
        logger.info(
            f"[DEBUG] process_task_with_timezones: Converting reminder time - {reminder_date} {reminder_time}"
        )
        reminder_date, reminder_time = convert_time_between_users(
            reminder_base, reminder_time, assigner, assignee
        )
        logger.info(
            f"[DEBUG] process_task_with_timezones: Converted reminder time - {reminder_date} {reminder_time}"
        )
        task_json["reminder_date"] = reminder_date
        task_json["reminder_time"] = reminder_time

    # Add timezone info to the task for clarity
    task_json["timezone_info"] = {
        "assigner_tz": str(assigner_tz),
        "assignee_tz": str(assignee_tz),
        "converted": True,
    }

    logger.info(
        f"[DEBUG] process_task_with_timezones: OUTPUT task_json = {json.dumps(task_json, indent=2)}"
    )
    return task_json
