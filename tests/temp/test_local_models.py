#!/usr/bin/env python3
"""
Compare local Ollama models for task parsing.
"""

import time
import json
import requests
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unified_parser import load_prompts

# Test cases
TEST_CASES = [
    "Remind Joel at the top of the hour to check oil",
    "Tell Bryan at 2PM CST tomorrow to restart servers",
    "Have Joel check the telemetry readings at 5:30pm",
    "Every weekday at 6:45am, Joel needs to check VPN tunnels",
    "Bryan needs to replace the bolts at Site B this weekend",
]


def test_model(model_name: str, test_cases: list):
    """Test a specific Ollama model."""
    print(f"\n=== Testing {model_name} ===")

    # Load prompts
    system_prompt, few_shot_examples = load_prompts()
    combined_prompt = f"{system_prompt}\n\n## Examples:\n\n{few_shot_examples}"

    results = []
    for test in test_cases:
        print(f"\nTesting: {test[:60]}...")

        # Build full prompt
        full_prompt = f"{combined_prompt}\n\n(Context: It is currently 16:00 on 2025-07-11 where Colin is located) {test}"

        try:
            start = time.time()

            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9,
                    },
                },
                timeout=30,
            )

            elapsed = time.time() - start

            if response.status_code == 200:
                result = response.json()
                assistant_response = result.get("response", "").strip()

                # Extract JSON
                if "```json" in assistant_response:
                    json_str = (
                        assistant_response.split("```json")[1].split("```")[0].strip()
                    )
                else:
                    json_str = assistant_response

                try:
                    parsed = json.loads(json_str)
                    print(f"✓ Success in {elapsed:.2f}s")
                    results.append(
                        {
                            "test": test,
                            "success": True,
                            "time": elapsed,
                            "parsed": parsed,
                        }
                    )
                except json.JSONDecodeError:
                    print(f"✗ JSON parse error in {elapsed:.2f}s")
                    print(f"Response: {assistant_response[:200]}...")
                    results.append(
                        {
                            "test": test,
                            "success": False,
                            "time": elapsed,
                            "error": "JSON parse error",
                        }
                    )
            else:
                print(f"✗ API error: {response.status_code}")
                results.append(
                    {
                        "test": test,
                        "success": False,
                        "time": elapsed,
                        "error": f"API error {response.status_code}",
                    }
                )

        except Exception as e:
            elapsed = time.time() - start
            print(f"✗ Error: {e}")
            results.append(
                {"test": test, "success": False, "time": elapsed, "error": str(e)}
            )

    return results


def main():
    # Test models
    models = [
        "llama3:8b-instruct-q4_0",
        "phi3:latest",
    ]

    all_results = {}

    for model in models:
        results = test_model(model, TEST_CASES)
        all_results[model] = results

    # Compare results
    print("\n\n=== COMPARISON RESULTS ===")
    print(f"{'Test Case':<60} {'Llama3-Q4':<15} {'Phi-3':<15}")
    print("=" * 90)

    for i, test in enumerate(TEST_CASES):
        test_short = test[:57] + "..." if len(test) > 57 else test

        llama_result = all_results["llama3:8b-instruct-q4_0"][i]
        phi_result = all_results["phi3:latest"][i]

        llama_time = (
            f"{llama_result['time']:.2f}s" if llama_result["success"] else "Failed"
        )
        phi_time = f"{phi_result['time']:.2f}s" if phi_result["success"] else "Failed"

        print(f"{test_short:<60} {llama_time:<15} {phi_time:<15}")

    # Calculate averages
    for model_name, results in all_results.items():
        success_times = [r["time"] for r in results if r["success"]]
        if success_times:
            avg_time = sum(success_times) / len(success_times)
            success_rate = len(success_times) / len(results) * 100
            print(f"\n{model_name}:")
            print(f"  Average time: {avg_time:.2f}s")
            print(f"  Success rate: {success_rate:.0f}%")


if __name__ == "__main__":
    main()
