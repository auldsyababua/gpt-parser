#!/usr/bin/env python3
"""
Run timezone test cases automatically and analyze reasoning.
"""

import sys
import os
import json
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.assistants_api_runner import (
    get_or_create_assistant,
    parse_task,
    send_to_google_sheets,
)


def load_test_cases(filename):
    """Load test cases from file, extracting just the prompts."""
    test_cases = []

    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Extract just the prompt part (before the first |)
            if "|" in line:
                prompt = line.split("|")[0].strip()
                test_cases.append(prompt)

    return test_cases


def run_tests():
    """Run all test cases and send to Google Sheets."""
    # Initialize assistant
    print("Initializing assistant...")
    assistant = get_or_create_assistant()
    if not assistant:
        print("Failed to initialize assistant.")
        return

    # Load test cases
    test_file = os.path.join(os.path.dirname(__file__), "timezone_test_cases.txt")
    test_cases = load_test_cases(test_file)

    print(f"\nLoaded {len(test_cases)} test cases.")
    print("=" * 60)

    # Run each test
    for i, test_prompt in enumerate(test_cases, 1):
        print(f"\nTest {i}/{len(test_cases)}: {test_prompt}")
        print("-" * 40)

        try:
            # Parse the task
            parsed_json = parse_task(assistant, test_prompt)

            if parsed_json:
                # Display key results
                print(f"Assignee: {parsed_json.get('assignee')}")
                print(f"Reminder Time: {parsed_json.get('reminder_time', 'N/A')}")
                print(f"Due Time: {parsed_json.get('due_time', 'N/A')}")
                print(
                    f"Reasoning: {parsed_json.get('reasoning', 'No reasoning provided')}"
                )

                # Add test number to the task for tracking
                parsed_json["task"] = f"[TEST {i}] {parsed_json.get('task', '')}"

                # Send to Google Sheets
                print("Sending to Google Sheets...")
                success = send_to_google_sheets(parsed_json)

                if success:
                    print("✅ Sent successfully")
                else:
                    print("❌ Failed to send to sheets")

            else:
                print("❌ Failed to parse task")

        except Exception as e:
            print(f"❌ Error: {e}")

        # Small delay between tests
        time.sleep(2)

    print("\n" + "=" * 60)
    print("All tests completed! Check Google Sheets for results.")


if __name__ == "__main__":
    print("Starting Timezone Test Runner")
    print("This will send all test cases to Google Sheets with auto-confirmation.")
    print("Check the 'reasoning' column to analyze parsing decisions.\n")

    response = input("Continue? (y/n): ")
    if response.lower() == "y":
        run_tests()
    else:
        print("Cancelled.")
