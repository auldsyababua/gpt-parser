"""Timezone configuration for multi-user support."""

from typing import Dict
from zoneinfo import ZoneInfo

# User timezone mappings
USER_TIMEZONES: Dict[str, str] = {
    "Colin": "America/Los_Angeles",  # PDT/PST
    "Joel": "America/Chicago",  # CDT/CST
    "Bryan": "America/Chicago",  # CDT/CST
}

# Default timezone for users not in the mapping
DEFAULT_TIMEZONE = "UTC"


def get_user_timezone(username: str) -> ZoneInfo:
    """Get ZoneInfo object for a user.

    Args:
        username: The name of the user

    Returns:
        ZoneInfo object for the user's timezone
    """
    tz_name = USER_TIMEZONES.get(username, DEFAULT_TIMEZONE)
    return ZoneInfo(tz_name)


def get_timezone_abbreviation(username: str) -> str:
    """Get the timezone abbreviation for a user.

    Args:
        username: The name of the user

    Returns:
        Timezone abbreviation (e.g., 'PDT', 'CST')
    """
    timezone_to_abbr = {
        "America/Los_Angeles": "PDT/PST",
        "America/Chicago": "CDT/CST",
        "UTC": "UTC",
    }
    tz_name = USER_TIMEZONES.get(username, DEFAULT_TIMEZONE)
    return timezone_to_abbr.get(tz_name, "UTC")
