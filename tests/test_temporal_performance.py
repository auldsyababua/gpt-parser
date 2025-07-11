#!/usr/bin/env python3
"""
Test the performance improvement from temporal preprocessing.
"""

import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.assistants_api_runner import get_or_create_assistant, parse_task


def test_performance():
    """Test parsing performance with various inputs."""

    # Test cases that should benefit from preprocessing
    test_cases = [
        "Remind Joel tomorrow at 3pm to check batteries",
        "Tell Bryan at 2PM CST tomorrow to restart servers",
        "Check telemetry at end of the hour",
        "Submit report by end of day",
        "Do maintenance this weekend",
        "Meeting at top of the hour",
        "Remind Joel 30 minutes before the 4pm meeting",
    ]

    # Complex cases that might still need full LLM
    complex_cases = [
        "Every weekday at 6:45am, Joel needs to check VPN tunnels",
        "Have Bryan replace the rusted bolts on the Site B flare rig sometime this weekend",
        "Make sure to remind Joel 30 minutes before he needs to reset the firewall script at 4pm",
    ]

    print("=== Temporal Preprocessing Performance Test ===\n")

    # Get assistant
    print("Initializing assistant...")
    assistant = get_or_create_assistant()
    if not assistant:
        print("Failed to initialize assistant")
        return

    print(f"Assistant ready: {assistant['id']}\n")

    # Test simple cases (should be faster with preprocessing)
    print("--- Testing Simple Temporal Expressions ---")
    for test_input in test_cases:
        print(f"\nInput: '{test_input}'")

        start_time = time.time()
        try:
            result = parse_task(assistant, test_input)
            elapsed = time.time() - start_time

            if result and "_preprocessing" in result:
                preprocess_info = result["_preprocessing"]
                print(
                    f"✓ Preprocessed (confidence: {preprocess_info['confidence']:.1%})"
                )
                print(f"  Preprocessing time: {preprocess_info['time_saved']:.3f}s")
            else:
                print("✗ Not preprocessed (fell back to full LLM)")

            print(f"  Total time: {elapsed:.2f}s")

            if result:
                print(
                    f"  Result: {result.get('due_date')} {result.get('due_time', 'no time')}"
                )

        except Exception as e:
            print(f"✗ Error: {e}")

    # Test complex cases
    print("\n--- Testing Complex Expressions ---")
    for test_input in complex_cases:
        print(f"\nInput: '{test_input}'")

        start_time = time.time()
        try:
            result = parse_task(assistant, test_input)
            elapsed = time.time() - start_time

            if result and "_preprocessing" in result:
                print(f"✓ Preprocessed (unexpected)")
            else:
                print("✓ Full LLM parsing (as expected)")

            print(f"  Total time: {elapsed:.2f}s")

        except Exception as e:
            print(f"✗ Error: {e}")

    print("\n=== Performance Test Complete ===")


if __name__ == "__main__":
    test_performance()
