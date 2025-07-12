#!/usr/bin/env python3
"""
Benchmark local Ollama models with 30 unique task prompts.
"""

import time
import json
import requests
import os
import sys
from typing import List, Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.unified import load_prompts

# 30 unique test cases for apples-to-apples comparison
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
    # Edge cases and natural language (21-30)
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


def test_model(
    model_name: str, prompts: List[str], sleep_between: float = 1.0
) -> List[Dict[str, Any]]:
    """Test a model with all prompts."""
    print(f"\n{'='*60}")
    print(f"Testing: {model_name}")
    print(f"{'='*60}")

    # Load system prompt once
    system_prompt, few_shot_examples = load_prompts()
    combined_prompt = f"{system_prompt}\n\n## Examples:\n\n{few_shot_examples}"

    results = []
    successful = 0

    for i, test_prompt in enumerate(prompts, 1):
        print(f"\n[{i}/{len(prompts)}] {test_prompt[:50]}...", end="")

        # Build full prompt
        full_prompt = f"{combined_prompt}\n\n(Context: It is currently 16:00 on 2025-07-11 where Colin is located) {test_prompt}"

        try:
            start_time = time.time()

            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "num_predict": 1000,  # Limit response length
                    },
                },
                timeout=60,
            )

            elapsed = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                assistant_response = result.get("response", "").strip()

                # Extract JSON
                if "```json" in assistant_response:
                    json_str = (
                        assistant_response.split("```json")[1].split("```")[0].strip()
                    )
                else:
                    # Try to find JSON in response
                    import re

                    json_match = re.search(r"\{[^{}]*\}", assistant_response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                    else:
                        json_str = assistant_response

                try:
                    parsed = json.loads(json_str)
                    # Validate required fields
                    required = ["assignee", "task", "due_date"]
                    if all(field in parsed for field in required):
                        print(f" ✓ {elapsed:.2f}s")
                        successful += 1
                        results.append(
                            {
                                "prompt": test_prompt,
                                "success": True,
                                "time": elapsed,
                                "parsed": parsed,
                            }
                        )
                    else:
                        print(f" ✗ {elapsed:.2f}s (missing fields)")
                        results.append(
                            {
                                "prompt": test_prompt,
                                "success": False,
                                "time": elapsed,
                                "error": "Missing required fields",
                                "response": json_str[:200],
                            }
                        )
                except json.JSONDecodeError as e:
                    print(f" ✗ {elapsed:.2f}s (JSON error)")
                    results.append(
                        {
                            "prompt": test_prompt,
                            "success": False,
                            "time": elapsed,
                            "error": f"JSON parse error: {e}",
                            "response": assistant_response[:200],
                        }
                    )
            else:
                print(f" ✗ API error {response.status_code}")
                results.append(
                    {
                        "prompt": test_prompt,
                        "success": False,
                        "time": elapsed,
                        "error": f"API error {response.status_code}",
                    }
                )

        except requests.exceptions.Timeout:
            print(" ✗ Timeout after 60s")
            results.append(
                {
                    "prompt": test_prompt,
                    "success": False,
                    "time": 60.0,
                    "error": "Timeout",
                }
            )
        except Exception as e:
            elapsed = time.time() - start_time
            print(f" ✗ Error: {str(e)[:50]}")
            results.append(
                {
                    "prompt": test_prompt,
                    "success": False,
                    "time": elapsed,
                    "error": str(e),
                }
            )

        # Sleep between requests
        if i < len(prompts):
            time.sleep(sleep_between)

    print(f"\n{model_name} Summary: {successful}/{len(prompts)} successful")
    return results


def print_comparison(results_dict: Dict[str, List[Dict[str, Any]]]):
    """Print comparison table and statistics."""
    print(f"\n\n{'='*80}")
    print("BENCHMARK RESULTS")
    print(f"{'='*80}")

    models = list(results_dict.keys())

    # Summary statistics
    print("\nSUMMARY:")
    for model in models:
        results = results_dict[model]
        successful = [r for r in results if r["success"]]
        if successful:
            times = [r["time"] for r in successful]
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            success_rate = len(successful) / len(results) * 100

            print(f"\n{model}:")
            print(
                f"  Success rate: {success_rate:.1f}% ({len(successful)}/{len(results)})"
            )
            print(f"  Average time: {avg_time:.2f}s")
            print(f"  Min time: {min_time:.2f}s")
            print(f"  Max time: {max_time:.2f}s")

    # Detailed comparison by category
    categories = [
        ("Basic reminders (1-10)", 0, 10),
        ("Complex temporal (11-20)", 10, 20),
        ("Edge cases (21-30)", 20, 30),
    ]

    print("\n\nCATEGORY BREAKDOWN:")
    for cat_name, start, end in categories:
        print(f"\n{cat_name}:")
        for model in models:
            cat_results = results_dict[model][start:end]
            successful = sum(1 for r in cat_results if r["success"])
            avg_time = sum(r["time"] for r in cat_results if r["success"]) / max(
                successful, 1
            )
            print(f"  {model}: {successful}/10 successful, avg {avg_time:.2f}s")

    # Failed prompts analysis
    print("\n\nFAILED PROMPTS:")
    for model in models:
        failed = [
            (i + 1, r) for i, r in enumerate(results_dict[model]) if not r["success"]
        ]
        if failed:
            print(f"\n{model} failures ({len(failed)}):")
            for idx, result in failed[:5]:  # Show first 5 failures
                print(f"  #{idx}: {result['prompt'][:50]}... - {result['error']}")
            if len(failed) > 5:
                print(f"  ... and {len(failed)-5} more")


def main():
    print("Local Model Benchmark: 30 Unique Task Parsing Prompts")
    print("Models: llama3:8b-instruct-q4_0, phi3:latest")
    print("Sleep between requests: 1 second")

    # Test both models
    results = {}

    # Test Llama3
    results["llama3:8b-instruct-q4_0"] = test_model(
        "llama3:8b-instruct-q4_0", TEST_CASES, sleep_between=1.0
    )

    # Test Phi-3
    results["phi3:latest"] = test_model("phi3:latest", TEST_CASES, sleep_between=1.0)

    # Print comparison
    print_comparison(results)

    # Save results to file
    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to benchmark_results.json")


if __name__ == "__main__":
    main()
