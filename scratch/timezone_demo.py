#!/usr/bin/env python3
"""Demo script showing timezone conversion in action."""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.assistants_api_runner import (
    get_or_create_assistant,
    parse_task,
    format_task_for_confirmation,
)
from config.timezone_config import get_timezone_abbreviation

# Example inputs from Colin to different assignees
examples = [
    "At 3pm tomorrow, remind Joel to check the backyard for oil at 4pm",
    "Bryan needs to inspect Site A at 9am tomorrow",
    "Colin should review the reports at 5pm today",
]

print("=" * 60)
print("Timezone Conversion Demo")
print("=" * 60)
print()

# Create or get the assistant
print("Initializing assistant...")
assistant = get_or_create_assistant()
print("Assistant ready!\n")

for i, example in enumerate(examples, 1):
    print(f'Example {i}: "{example}"')
    print("-" * 40)

    try:
        # Parse the task (Colin is the default assigner)
        parsed = parse_task(assistant, example, assigner="Colin")

        # Display results
        assignee = parsed.get("assignee")
        print(f"Assignee: {assignee} ({get_timezone_abbreviation(assignee)})")
        print(f"Due: {parsed.get('due_date')} at {parsed.get('due_time', 'N/A')}")

        if parsed.get("reminder_time"):
            print(
                f"Reminder: {parsed.get('reminder_date')} at {parsed.get('reminder_time')}"
            )

        tz_info = parsed.get("timezone_info", {})
        if tz_info.get("converted"):
            print("\nTimezone conversion applied:")
            print(
                f"  From: Colin (PDT) → {assignee} ({get_timezone_abbreviation(assignee)})"
            )

        print("\nFormatted for confirmation:")
        print(format_task_for_confirmation(parsed))

    except Exception as e:
        print(f"Error parsing task: {e}")

    print("\n" + "=" * 60 + "\n")

print("Demo complete!")
