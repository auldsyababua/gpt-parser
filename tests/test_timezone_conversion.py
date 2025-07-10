"""Tests for timezone conversion functionality."""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.timezone_config import get_user_timezone
from utils.timezone_converter import (
    convert_time_between_users,
    process_task_with_timezones,
)


def test_timezone_mappings():
    """Test that user timezone mappings are correct."""
    print("Testing timezone mappings...")
    assert str(get_user_timezone("Colin")) == "America/Los_Angeles"
    assert str(get_user_timezone("Joel")) == "America/Chicago"
    assert str(get_user_timezone("Bryan")) == "America/Los_Angeles"
    assert str(get_user_timezone("Unknown")) == "UTC"  # Default
    print("✓ Timezone mappings correct")


def test_time_conversion():
    """Test time conversion between timezones."""
    print("\nTesting time conversions...")

    # Test case: Colin (PDT) assigns task to Joel (CDT) at 3pm
    base_date = datetime(2025, 7, 10)  # Summer time (DST active)

    # Convert 3pm PDT to CDT (should be 5pm)
    date_str, time_str = convert_time_between_users(base_date, "15:00", "Colin", "Joel")
    assert time_str == "17:00", f"Expected 17:00, got {time_str}"
    print("✓ 3pm PDT → 5pm CDT conversion correct")

    # Convert 4pm PDT to CDT (should be 6pm)
    date_str, time_str = convert_time_between_users(base_date, "16:00", "Colin", "Joel")
    assert time_str == "18:00", f"Expected 18:00, got {time_str}"
    print("✓ 4pm PDT → 6pm CDT conversion correct")


def test_task_processing():
    """Test full task processing with timezone conversion."""
    print("\nTesting full task processing...")

    # Sample task from Colin to Joel
    task_json = {
        "assigner": "Colin",
        "assignee": "Joel",
        "task": "Check the backyard for oil",
        "due_date": "2025-07-10",
        "due_time": "16:00",  # 4pm in Colin's timezone
        "reminder_date": "2025-07-10",
        "reminder_time": "15:00",  # 3pm in Colin's timezone
        "status": "pending",
        "created_at": "2025-07-09T08:00",
    }

    # Process with timezone conversion
    processed = process_task_with_timezones(task_json, "Colin")

    # Check conversions
    assert (
        processed["due_time"] == "18:00"
    ), f"Expected due_time 18:00, got {processed['due_time']}"
    assert (
        processed["reminder_time"] == "17:00"
    ), f"Expected reminder_time 17:00, got {processed['reminder_time']}"
    assert "timezone_info" in processed
    assert processed["timezone_info"]["converted"] is True

    print("✓ Task processing with timezone conversion correct")
    print(f"  - Due time: 4pm PDT → {processed['due_time']} CDT")
    print(f"  - Reminder: 3pm PDT → {processed['reminder_time']} CDT")


def test_same_timezone():
    """Test that same timezone doesn't convert."""
    print("\nTesting same timezone (no conversion)...")

    task_json = {
        "assigner": "Colin",
        "assignee": "Colin",  # Same person
        "task": "Check something",
        "due_date": "2025-07-10",
        "due_time": "16:00",
        "status": "pending",
    }

    processed = process_task_with_timezones(task_json, "Colin")

    # Should be unchanged
    assert processed["due_time"] == "16:00"
    assert "timezone_info" not in processed
    print("✓ Same timezone task unchanged")


if __name__ == "__main__":
    print("Running timezone conversion tests...\n")

    try:
        test_timezone_mappings()
        test_time_conversion()
        test_task_processing()
        test_same_timezone()

        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        sys.exit(1)
