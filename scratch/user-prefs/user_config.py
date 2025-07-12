"""User configuration and preferences."""

from typing import Dict, Optional
from dataclasses import dataclass
from datetime import time
import json
import os


@dataclass
class UserPreferences:
    """User preference settings."""

    username: str  # Telegram @username (without @)
    display_name: str  # Friendly name for tasks
    timezone: str  # IANA timezone (e.g., "America/Los_Angeles")
    default_reminder_minutes: int = 30  # Minutes before task to remind
    morning_time: time = time(8, 0)  # Default "morning" interpretation
    evening_time: time = time(17, 0)  # Default "evening" interpretation
    working_hours_start: time = time(8, 0)
    working_hours_end: time = time(18, 0)
    is_active: bool = True  # Can disable users without deleting
    role: str = "operator"  # operator, admin, viewer
    notification_preferences: Dict[str, bool] = None

    def __post_init__(self):
        if self.notification_preferences is None:
            self.notification_preferences = {
                "task_assigned": True,
                "task_due_soon": True,
                "task_overdue": True,
                "daily_summary": False,
            }


# Default user configuration
USERS = {
    "colin_10netzero": UserPreferences(
        username="colin_10netzero",
        display_name="Colin",
        timezone="America/Los_Angeles",  # PDT/PST
        role="admin",
        morning_time=time(7, 0),
        evening_time=time(18, 0),
    ),
    "bryan_10netzero": UserPreferences(
        username="bryan_10netzero",
        display_name="Bryan",
        timezone="America/Chicago",  # CDT/CST
        role="operator",
    ),
    "joel_10netzero": UserPreferences(
        username="joel_10netzero",
        display_name="Joel",
        timezone="America/Chicago",  # CDT/CST
        role="operator",
    ),
}


class UserConfigManager:
    """Manages user configuration and preferences."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "users.json"
        )
        self.users = self._load_config()

    def _load_config(self) -> Dict[str, UserPreferences]:
        """Load user config from file or use defaults."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    users = {}
                    for username, prefs in data.items():
                        # Convert time strings back to time objects
                        for time_field in [
                            "morning_time",
                            "evening_time",
                            "working_hours_start",
                            "working_hours_end",
                        ]:
                            if time_field in prefs and isinstance(
                                prefs[time_field], str
                            ):
                                h, m = map(int, prefs[time_field].split(":"))
                                prefs[time_field] = time(h, m)
                        users[username] = UserPreferences(**prefs)
                    return users
            except Exception as e:
                print(f"Error loading user config: {e}")
                return USERS.copy()
        return USERS.copy()

    def save_config(self):
        """Save current configuration to file."""
        data = {}
        for username, prefs in self.users.items():
            prefs_dict = prefs.__dict__.copy()
            # Convert time objects to strings for JSON
            for time_field in [
                "morning_time",
                "evening_time",
                "working_hours_start",
                "working_hours_end",
            ]:
                if time_field in prefs_dict and isinstance(
                    prefs_dict[time_field], time
                ):
                    prefs_dict[time_field] = prefs_dict[time_field].strftime("%H:%M")
            data[username] = prefs_dict

        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2)

    def get_user(self, username: str) -> Optional[UserPreferences]:
        """Get user preferences by username (without @)."""
        return self.users.get(username.lower().replace("@", ""))

    def is_authorized(self, username: str) -> bool:
        """Check if user is authorized and active."""
        user = self.get_user(username)
        return user is not None and user.is_active

    def add_user(self, user: UserPreferences) -> None:
        """Add or update a user."""
        self.users[user.username.lower()] = user
        self.save_config()

    def remove_user(self, username: str) -> bool:
        """Remove a user."""
        username = username.lower().replace("@", "")
        if username in self.users:
            del self.users[username]
            self.save_config()
            return True
        return False

    def list_active_users(self) -> Dict[str, UserPreferences]:
        """Get all active users."""
        return {u: p for u, p in self.users.items() if p.is_active}

    def get_users_by_timezone(self, timezone: str) -> Dict[str, UserPreferences]:
        """Get all users in a specific timezone."""
        return {
            u: p
            for u, p in self.users.items()
            if p.timezone == timezone and p.is_active
        }
