"""Timezone configuration for multi-user support."""

from typing import Dict
from zoneinfo import ZoneInfo

# User timezone mappings
USER_TIMEZONES: Dict[str, str] = {
    "Colin": "America/Los_Angeles",  # PDT/PST
    "Joel": "America/Chicago",  # CDT/CST
    "Bryan": "America/Chicago",  # CDT/CST
}

# Telegram username to canonical name mapping
# This helps identify the same person across different representations
TELEGRAM_USER_MAPPING: Dict[str, str] = {
    "colin aulds | 10netzero.com": "Colin",
    "Colin_10NetZero": "Colin",
    # Add more mappings as needed
}

# Default timezone for users not in the mapping
DEFAULT_TIMEZONE = "UTC"


def normalize_username(username: str) -> str:
    """Normalize a username to its canonical form.

    Args:
        username: Raw username (could be Telegram username, display name, etc.)

    Returns:
        Canonical username for timezone lookups
    """
    # First check if it's in the Telegram mapping
    if username in TELEGRAM_USER_MAPPING:
        return TELEGRAM_USER_MAPPING[username]

    # Check lowercase version
    username_lower = username.lower()
    for telegram_name, canonical_name in TELEGRAM_USER_MAPPING.items():
        if telegram_name.lower() == username_lower:
            return canonical_name

    # Fall back to simple name matching for backward compatibility
    # This handles cases like "colin" -> "Colin"
    for canonical_name in USER_TIMEZONES.keys():
        if canonical_name.lower() == username_lower:
            return canonical_name

    # Return original if no match found
    return username


def get_user_timezone(username: str) -> ZoneInfo:
    """Get ZoneInfo object for a user.

    Args:
        username: The name of the user

    Returns:
        ZoneInfo object for the user's timezone
    """
    # Normalize the username first
    normalized = normalize_username(username)

    # Get timezone for normalized username
    tz_name = USER_TIMEZONES.get(normalized, DEFAULT_TIMEZONE)

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

    # Get the actual timezone using case-insensitive lookup
    tz = get_user_timezone(username)
    tz_key = str(tz.key)  # Get the timezone key like "America/Los_Angeles"

    return timezone_to_abbr.get(tz_key, "UTC")
