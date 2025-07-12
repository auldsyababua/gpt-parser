#!/usr/bin/env python3
"""
Compare OpenAI Assistants API vs Chat Completions API performance.
"""

import time
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assistants_api_runner import (
    get_or_create_assistant,
    parse_task as parse_assistants,
)
from unified_parser import parse_task as parse_completions

# Test cases
TEST_CASES = [
    "Remind Joel at the top of the hour to check oil",
    "Tell Bryan at 2PM CST tomorrow to restart servers",
    "Have Joel check the telemetry readings at the top of the next hour, then again 30 minutes later",
    "Every weekday at 6:45am, Joel needs to check VPN tunnels",
    "Have Bryan replace the rusted bolts on the Site B flare rig sometime this weekend",
]


def test_assistants_api():
    """Test using Assistants API."""
    print("\n=== Testing OpenAI Assistants API ===")
    assistant = get_or_create_assistant()
    if not assistant:
        print("Failed to initialize assistant")
        return []

    results = []
    for test in TEST_CASES:
        print(f"\nTesting: {test[:60]}...")
        start = time.time()

        try:
            result = parse_assistants(assistant, test)
            elapsed = time.time() - start

            if result:
                print(f"✓ Success in {elapsed:.2f}s")
                results.append(
                    {
                        "test": test,
                        "success": True,
                        "time": elapsed,
                        "api": "assistants",
                    }
                )
            else:
                print("✗ Failed")
                results.append(
                    {
                        "test": test,
                        "success": False,
                        "time": elapsed,
                        "api": "assistants",
                    }
                )
        except Exception as e:
            elapsed = time.time() - start
            print(f"✗ Error: {e}")
            results.append(
                {
                    "test": test,
                    "success": False,
                    "time": elapsed,
                    "api": "assistants",
                    "error": str(e),
                }
            )

    return results


def test_completions_api():
    """Test using Chat Completions API."""
    print("\n=== Testing OpenAI Chat Completions API ===")

    # Force it to use OpenAI by temporarily changing env
    original_provider = os.environ.get("PRIMARY_MODEL_PROVIDER")
    os.environ["PRIMARY_MODEL_PROVIDER"] = "openai"
    os.environ["PRIMARY_MODEL_NAME"] = "gpt-4o-mini"

    results = []
    for test in TEST_CASES:
        print(f"\nTesting: {test[:60]}...")
        start = time.time()

        try:
            result = parse_completions(test)
            elapsed = time.time() - start

            if result:
                # Extract performance from result
                perf = result.get("_performance", {})
                api_time = perf.get("api_time", elapsed)
                print(f"✓ Success in {elapsed:.2f}s (API: {api_time:.2f}s)")
                results.append(
                    {
                        "test": test,
                        "success": True,
                        "time": elapsed,
                        "api_time": api_time,
                        "api": "completions",
                    }
                )
            else:
                print("✗ Failed")
                results.append(
                    {
                        "test": test,
                        "success": False,
                        "time": elapsed,
                        "api": "completions",
                    }
                )
        except Exception as e:
            elapsed = time.time() - start
            print(f"✗ Error: {e}")
            results.append(
                {
                    "test": test,
                    "success": False,
                    "time": elapsed,
                    "api": "completions",
                    "error": str(e),
                }
            )

    # Restore original provider
    if original_provider:
        os.environ["PRIMARY_MODEL_PROVIDER"] = original_provider

    return results


def main():
    load_dotenv()

    # Test both APIs
    assistants_results = test_assistants_api()
    completions_results = test_completions_api()

    # Compare results
    print("\n\n=== COMPARISON RESULTS ===")
    print(f"{'Test Case':<70} {'Assistants API':<20} {'Completions API':<20}")
    print("=" * 110)

    for i, test in enumerate(TEST_CASES):
        assist = assistants_results[i] if i < len(assistants_results) else None
        complete = completions_results[i] if i < len(completions_results) else None

        test_short = test[:65] + "..." if len(test) > 65 else test

        assist_time = (
            f"{assist['time']:.2f}s" if assist and assist["success"] else "Failed"
        )
        complete_time = (
            f"{complete['time']:.2f}s" if complete and complete["success"] else "Failed"
        )

        print(f"{test_short:<70} {assist_time:<20} {complete_time:<20}")

    # Calculate averages
    assist_times = [r["time"] for r in assistants_results if r["success"]]
    complete_times = [r["time"] for r in completions_results if r["success"]]

    if assist_times:
        print(f"\nAssistants API average: {sum(assist_times)/len(assist_times):.2f}s")
    if complete_times:
        print(
            f"Completions API average: {sum(complete_times)/len(complete_times):.2f}s"
        )

    if assist_times and complete_times:
        speedup = (sum(assist_times) / len(assist_times)) / (
            sum(complete_times) / len(complete_times)
        )
        print(f"\nCompletions API is {speedup:.1f}x faster than Assistants API")


if __name__ == "__main__":
    main()
