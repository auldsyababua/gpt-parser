#!/usr/bin/env python3
"""
Automated timezone test runner - runs all tests without user input
"""
import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.assistants_api_runner import (
    get_or_create_assistant,
    parse_task,
    send_to_google_sheets,
)

# Test cases specifically for timezone handling
TIMEZONE_TEST_CASES = [
    # Basic timezone tests
    {
        "input": "at 4pm CST tomorrow, remind Joel to check the oil cans by 5pm",
        "expected_timezone_context": "CST",
        "expected_times": {"reminder_time": "16:00", "due_time": "17:00"},
        "description": "Explicit CST timezone",
    },
    {
        "input": "remind Bryan at 9am EST on Friday to restart the miners",
        "expected_timezone_context": "EST",
        "expected_times": {"reminder_time": "09:00", "due_time": "09:00"},
        "description": "Explicit EST timezone",
    },
    {
        "input": "tell Joel to perform maintenance at 5pm PST at Site A, remind him at 3pm PST",
        "expected_timezone_context": "PST",
        "expected_times": {"reminder_time": "15:00", "due_time": "17:00"},
        "description": "Explicit PST timezone with separate reminder",
    },
    {
        "input": "remind Joel tomorrow at 8am to check the solar battery charge",
        "expected_timezone_context": "assigner_local",
        "expected_times": {"reminder_time": "08:00", "due_time": "08:00"},
        "description": "No timezone specified (should use assigner's)",
    },
    {
        "input": "Bryan needs to update the firewall at 10am Central time tomorrow",
        "expected_timezone_context": "Central",
        "expected_times": {"reminder_time": "10:00", "due_time": "10:00"},
        "description": "Informal timezone reference",
    },
    {
        "input": "at 2pm Houston time, remind Joel to check the generators",
        "expected_timezone_context": "Houston time",
        "expected_times": {"reminder_time": "14:00", "due_time": "14:00"},
        "description": "City-based timezone reference",
    },
]


def run_test(assistant, test_case, test_num):
    """Run a single test case"""
    print(f"\n{'='*60}")
    print(f"Test {test_num}: {test_case['description']}")
    print(f"Input: {test_case['input']}")
    print(f"Expected timezone_context: {test_case['expected_timezone_context']}")

    try:
        # Parse the task
        parsed_json = parse_task(assistant, test_case["input"])

        if parsed_json:
            # Check timezone context
            actual_tz_context = parsed_json.get("timezone_context", "Not found")
            tz_match = actual_tz_context == test_case["expected_timezone_context"]

            print(f"\nTimezone context: {actual_tz_context} {'✓' if tz_match else '✗'}")

            # Check times
            for time_field, expected in test_case["expected_times"].items():
                actual = parsed_json.get(time_field, "Not found")
                time_match = actual == expected
                print(
                    f"{time_field}: {actual} (expected {expected}) {'✓' if time_match else '✗'}"
                )

            # Show reasoning
            print(
                f"\nReasoning: {parsed_json.get('reasoning', 'No reasoning provided')}"
            )

            # Send to Google Sheets
            print("\nSending to Google Sheets...")
            success = send_to_google_sheets(parsed_json)
            if success:
                print("✓ Successfully sent to Google Sheets")
            else:
                print("✗ Failed to send to Google Sheets")

            return parsed_json
        else:
            print("✗ Failed to parse task")
            return None

    except Exception as e:
        print(f"✗ Error during test: {e}")
        return None


def main():
    print("Starting Automated Timezone Test Runner")
    print("======================================")
    print(f"Running {len(TIMEZONE_TEST_CASES)} test cases")
    print("Results will be sent to Google Sheets")

    # Get or create assistant
    print("\nInitializing assistant...")
    assistant = get_or_create_assistant()
    if not assistant:
        print("Failed to initialize assistant. Exiting.")
        return

    # Run all tests
    results = []
    for i, test_case in enumerate(TIMEZONE_TEST_CASES, 1):
        result = run_test(assistant, test_case, i)
        results.append(
            {"test_case": test_case, "result": result, "success": result is not None}
        )

        # Small delay between tests
        if i < len(TIMEZONE_TEST_CASES):
            time.sleep(2)

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")

    successful = sum(1 for r in results if r["success"])
    print(f"Total tests: {len(TIMEZONE_TEST_CASES)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(TIMEZONE_TEST_CASES) - successful}")

    # Detailed results
    print("\nDetailed Results:")
    for i, result in enumerate(results, 1):
        status = "✓" if result["success"] else "✗"
        desc = result["test_case"]["description"]
        print(f"{status} Test {i}: {desc}")

        if result["result"]:
            tz_context = result["result"].get("timezone_context", "Not found")
            expected_tz = result["test_case"]["expected_timezone_context"]
            tz_match = tz_context == expected_tz
            print(
                f"  - Timezone: {tz_context} (expected: {expected_tz}) {'✓' if tz_match else '✗'}"
            )


if __name__ == "__main__":
    main()
