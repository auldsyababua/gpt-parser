#!/usr/bin/env python3
"""
Compare GPT-4.1-nano vs GPT-4.1-mini on 30 test cases.
"""

import time
import json
import requests
import os
import sys
from typing import List, Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 30 test cases from quick_benchmark.py
TEST_CASES = [
    # Basic reminders (1-10)
    "Remind Joel at the top of the hour to check oil",
    "Tell Bryan at 2PM CST tomorrow to restart servers",
    "Have Joel check the telemetry readings at 5:30pm",
    "Ask Bryan to inspect Site B at 9am Monday",
    "Tell Joel to call the contractor before noon",
    "Remind Bryan about the maintenance report by Friday",
    "Have Joel verify the bitcoin nodes are running at 3pm",
    "Tell Bryan to order replacement parts by end of day",
    "Remind Joel to submit timesheets before 5pm Friday",
    "Have Bryan check the generator fuel levels at 8am",
    # Complex temporal (11-20)
    "Every weekday at 6:45am, Joel needs to check VPN tunnels",
    "First Monday of each month, Bryan should test backup systems",
    "Have Joel do maintenance every other Tuesday at 10am",
    "Remind Bryan on the 15th and 30th to process invoices",
    "Every 3 days have someone check the mining pool stats",
    "Joel needs to rotate logs weekly on Sunday nights",
    "Have Bryan update documentation every quarter",
    "Remind Joel daily at 7am and 7pm to check temperatures",
    "Every weekday except Friday, Bryan checks mail at 2pm",
    "Have Joel inspect all sites monthly on the last Friday",
    # Edge cases (21-30)
    "yo joel tmrw morning check if the generator needs oil",
    "Bryan needs to replace the bolts at Site B this weekend",
    "sometime next week have joel audit the security logs",
    "ASAP tell bryan the server at site C is overheating",
    "when joel gets in tomorrow have him call me about repairs",
    "next time bryan is at site A get him to photo the damage",
    "if it's not raining tomorrow joel should paint the shed",
    "have bryan or joel whoever is closer check site D",
    "the contractor is coming tuesday make sure someones there",
    "before end of Q1 remind bryan about budget proposals",
]


def load_prompts():
    """Load the system prompt and few-shot examples."""
    with open("config/prompts/system_prompt.txt", "r") as f:
        system_prompt = f.read()
    with open("config/prompts/few_shot_examples.txt", "r") as f:
        few_shot_examples = f.read()
    return system_prompt, few_shot_examples


def test_model(
    model_name: str, api_key: str, prompts: List[str]
) -> List[Dict[str, Any]]:
    """Test a model with all prompts."""
    print(f"\n{'='*60}")
    print(f"Testing: {model_name}")
    print(f"{'='*60}")

    # Load system prompt once
    system_prompt, few_shot_examples = load_prompts()

    results = []
    successful = 0
    total_time = 0

    for i, test_prompt in enumerate(prompts, 1):
        print(f"\n[{i}/{len(prompts)}] {test_prompt[:50]}...", end=" ")

        # Build the message with context
        user_message = f"(Context: It is currently 17:00 on 2025-07-11 where Colin is located) {test_prompt}"

        try:
            start_time = time.time()

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": [
                        {
                            "role": "system",
                            "content": f"{system_prompt}\n\n## Examples:\n\n{few_shot_examples}",
                        },
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 500,
                },
                timeout=30,
            )

            elapsed = time.time() - start_time
            total_time += elapsed

            if response.status_code == 200:
                data = response.json()
                assistant_response = data["choices"][0]["message"]["content"].strip()

                # Extract JSON
                if "```json" in assistant_response:
                    json_str = (
                        assistant_response.split("```json")[1].split("```")[0].strip()
                    )
                elif "```" in assistant_response:
                    json_str = (
                        assistant_response.split("```")[1].split("```")[0].strip()
                    )
                else:
                    json_str = assistant_response

                try:
                    parsed = json.loads(json_str)
                    # Check required fields
                    required = ["assignee", "task", "due_date"]
                    if all(field in parsed for field in required):
                        successful += 1
                        print(f"✓ {elapsed:.2f}s")
                        results.append(
                            {
                                "prompt": test_prompt,
                                "success": True,
                                "time": elapsed,
                                "parsed": parsed,
                            }
                        )
                    else:
                        missing = [f for f in required if f not in parsed]
                        print(f"✗ {elapsed:.2f}s (missing: {missing})")
                        results.append(
                            {
                                "prompt": test_prompt,
                                "success": False,
                                "time": elapsed,
                                "error": f"Missing fields: {missing}",
                            }
                        )
                except json.JSONDecodeError:
                    print(f"✗ {elapsed:.2f}s (JSON error)")
                    results.append(
                        {
                            "prompt": test_prompt,
                            "success": False,
                            "time": elapsed,
                            "error": "JSON parse error",
                        }
                    )
            else:
                print(f"✗ API error {response.status_code}")
                error_msg = (
                    response.json().get("error", {}).get("message", "Unknown error")
                )
                results.append(
                    {
                        "prompt": test_prompt,
                        "success": False,
                        "time": elapsed,
                        "error": f"API {response.status_code}: {error_msg}",
                    }
                )

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"✗ Error: {str(e)[:50]}")
            results.append(
                {
                    "prompt": test_prompt,
                    "success": False,
                    "time": elapsed,
                    "error": str(e)[:100],
                }
            )

        # Small sleep between requests
        if i < len(prompts):
            time.sleep(0.5)

    print(f"\n\n{model_name} Summary:")
    print(
        f"Success rate: {successful}/{len(prompts)} ({successful/len(prompts)*100:.1f}%)"
    )
    print(f"Average time: {total_time/len(prompts):.2f}s")

    return results


def main():
    # Load API key
    with open(".env") as f:
        for line in f:
            if line.startswith("OPENAI_API_KEY="):
                api_key = line.strip().split("=")[1]
                break

    print("GPT-4.1 Model Comparison: 30 Task Parsing Tests")
    print("Models: gpt-4.1-nano vs gpt-4.1-mini")

    # Test both models
    nano_results = test_model("gpt-4.1-nano", api_key, TEST_CASES)
    mini_results = test_model("gpt-4.1-mini", api_key, TEST_CASES)

    # Summary comparison
    print("\n" + "=" * 80)
    print("FINAL COMPARISON")
    print("=" * 80)

    # Calculate statistics
    nano_success = [r for r in nano_results if r["success"]]
    mini_success = [r for r in mini_results if r["success"]]

    if nano_success:
        nano_times = [r["time"] for r in nano_success]
        nano_avg = sum(nano_times) / len(nano_times)
        print(f"\ngpt-4.1-nano:")
        print(
            f"  Success rate: {len(nano_success)}/{len(nano_results)} ({len(nano_success)/len(nano_results)*100:.1f}%)"
        )
        print(f"  Average time (successful): {nano_avg:.2f}s")
        print(f"  Min/Max time: {min(nano_times):.2f}s / {max(nano_times):.2f}s")

    if mini_success:
        mini_times = [r["time"] for r in mini_success]
        mini_avg = sum(mini_times) / len(mini_times)
        print(f"\ngpt-4.1-mini:")
        print(
            f"  Success rate: {len(mini_success)}/{len(mini_results)} ({len(mini_success)/len(mini_results)*100:.1f}%)"
        )
        print(f"  Average time (successful): {mini_avg:.2f}s")
        print(f"  Min/Max time: {min(mini_times):.2f}s / {max(mini_times):.2f}s")

    # Category breakdown
    categories = [
        ("Basic (1-10)", 0, 10),
        ("Complex (11-20)", 10, 20),
        ("Edge cases (21-30)", 20, 30),
    ]

    print("\nCategory Success Rates:")
    print(f"{'Category':<20} {'GPT-4.1-nano':<20} {'GPT-4.1-mini':<20}")
    print("-" * 60)

    for cat_name, start, end in categories:
        nano_cat = sum(1 for r in nano_results[start:end] if r["success"])
        mini_cat = sum(1 for r in mini_results[start:end] if r["success"])
        print(
            f"{cat_name:<20} {nano_cat}/10 ({nano_cat*10}%)      {mini_cat}/10 ({mini_cat*10}%)"
        )

    # Speed comparison
    if nano_success and mini_success:
        speed_diff = (mini_avg - nano_avg) / nano_avg * 100
        if speed_diff > 0:
            print(f"\nSpeed: gpt-4.1-nano is {speed_diff:.1f}% faster")
        else:
            print(f"\nSpeed: gpt-4.1-mini is {abs(speed_diff):.1f}% faster")

    # Show failures
    print("\nSample Failures:")
    for name, results in [
        ("gpt-4.1-nano", nano_results),
        ("gpt-4.1-mini", mini_results),
    ]:
        failures = [(i + 1, r) for i, r in enumerate(results) if not r["success"]]
        if failures:
            print(f"\n{name} failed on:")
            for idx, r in failures[:3]:
                print(f"  #{idx}: {r['prompt'][:40]}... ({r['error']})")
            if len(failures) > 3:
                print(f"  ... and {len(failures)-3} more")


if __name__ == "__main__":
    main()
