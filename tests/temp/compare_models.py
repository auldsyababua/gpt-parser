#!/usr/bin/env python3
"""
Compare performance between OpenAI and Groq models for task parsing.
"""

import time
import json
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Also add scripts directory for imports
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
)

from assistants_api_runner import get_or_create_assistant, parse_task as parse_openai
from groq_parser import parse_task as parse_groq
from local_llama_parser import parse_task as parse_llama


# Load comprehensive test cases
def load_test_cases():
    """Load test cases from comprehensive test file."""
    test_file = os.path.join(
        os.path.dirname(__file__), "fixtures", "comprehensive_test_cases.txt"
    )
    test_cases = []

    try:
        with open(test_file, "r") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith("#"):
                    test_cases.append(line)
    except FileNotFoundError:
        print(f"Warning: {test_file} not found. Using default test cases.")
        # Fallback to simple test cases
        test_cases = [
            "Remind Joel tomorrow at 3pm to check the oil levels at Site A",
            "Tell Bryan at 2PM CST tomorrow to restart servers",
            "Check telemetry at end of the hour",
            "Every weekday at 6:45am, Joel needs to check VPN tunnels",
            "Have Bryan replace the rusted bolts on the Site B flare rig sometime this weekend",
        ]

    return test_cases


TEST_CASES = load_test_cases()


def test_model(name, parse_func, test_cases, assistant=None, show_progress=True):
    """Test a model with given test cases."""
    results = []
    total_tests = len(test_cases)

    for i, test_input in enumerate(test_cases, 1):
        if show_progress:
            print(f"\n  [{i}/{total_tests}] Testing: '{test_input[:60]}...'")

        try:
            start_time = time.time()

            if assistant:
                # OpenAI needs assistant object
                result = parse_func(assistant, test_input)
            else:
                # Groq doesn't need assistant
                result = parse_func(test_input)

            elapsed = time.time() - start_time

            if result:
                perf = result.get("_performance", {})
                results.append(
                    {
                        "input": test_input,
                        "total_time": elapsed,
                        "api_time": perf.get("api_time", elapsed),
                        "preprocessing_time": perf.get("preprocessing_time", 0),
                        "success": True,
                        "assignee": result.get("assignee"),
                        "due_date": result.get("due_date"),
                        "due_time": result.get("due_time"),
                        "preprocessing_confidence": result.get(
                            "_preprocessing", {}
                        ).get("confidence", 0),
                    }
                )
                if show_progress:
                    print(
                        f"  ✓ Success in {elapsed:.2f}s (API: {perf.get('api_time', elapsed):.2f}s)"
                    )
            else:
                results.append(
                    {"input": test_input, "total_time": elapsed, "success": False}
                )
                if show_progress:
                    print(f"  ✗ Failed")

        except Exception as e:
            error_msg = str(e)
            if "rate_limit" in error_msg:
                print(f"  ⚠️  Rate limited - waiting 15s...")
                time.sleep(15)  # Wait for rate limit
            results.append(
                {
                    "input": test_input,
                    "total_time": 0,
                    "success": False,
                    "error": error_msg,
                }
            )
            if show_progress:
                print(f"  ✗ Error: {error_msg[:100]}...")

    return results


def analyze_failures(results, model_name):
    """Analyze failure patterns for a model."""
    failures = [r for r in results if not r["success"]]
    if not failures:
        return

    print(f"\n{model_name} Failure Analysis:")
    failure_types = {}
    for f in failures:
        error = f.get("error", "Unknown")
        if "rate_limit" in error:
            failure_types["Rate Limited"] = failure_types.get("Rate Limited", 0) + 1
        elif "JSONDecodeError" in error:
            failure_types["JSON Parse Error"] = (
                failure_types.get("JSON Parse Error", 0) + 1
            )
        elif "timeout" in error.lower():
            failure_types["Timeout"] = failure_types.get("Timeout", 0) + 1
        else:
            failure_types["Other"] = failure_types.get("Other", 0) + 1

    for ftype, count in failure_types.items():
        print(f"  - {ftype}: {count}")


def print_comparison(openai_results, groq_results, llama_results=None):
    """Print comparison table."""
    print("\n" + "=" * 100)
    print("COMPREHENSIVE MODEL COMPARISON - 30 TEST CASES")
    print("=" * 100)

    # Calculate averages
    openai_times = [r["total_time"] for r in openai_results if r["success"]]
    groq_times = [r["total_time"] for r in groq_results if r["success"]]
    llama_times = (
        [r["total_time"] for r in llama_results if r["success"]]
        if llama_results
        else []
    )

    openai_avg = sum(openai_times) / len(openai_times) if openai_times else 0
    groq_avg = sum(groq_times) / len(groq_times) if groq_times else 0
    llama_avg = sum(llama_times) / len(llama_times) if llama_times else 0

    # Success counts
    openai_success = sum(1 for r in openai_results if r["success"])
    groq_success = sum(1 for r in groq_results if r["success"])
    llama_success = (
        sum(1 for r in llama_results if r["success"]) if llama_results else 0
    )

    print(f"\n📊 Performance Summary:")
    print(
        f"\n{'Model':<20} {'Success Rate':<15} {'Avg Time':<12} {'Min Time':<12} {'Max Time':<12}"
    )
    print("-" * 71)

    # OpenAI stats
    if openai_times:
        print(
            f"{'GPT-4o-mini':<20} {f'{openai_success}/{len(openai_results)}':<15} "
            f"{f'{openai_avg:.2f}s':<12} {f'{min(openai_times):.2f}s':<12} {f'{max(openai_times):.2f}s':<12}"
        )
    else:
        print(
            f"{'GPT-4o-mini':<20} {f'{openai_success}/{len(openai_results)}':<15} {'N/A':<12} {'N/A':<12} {'N/A':<12}"
        )

    # Groq stats
    if groq_times:
        print(
            f"{'Groq Llama3-8B':<20} {f'{groq_success}/{len(groq_results)}':<15} "
            f"{f'{groq_avg:.2f}s':<12} {f'{min(groq_times):.2f}s':<12} {f'{max(groq_times):.2f}s':<12}"
        )
    else:
        print(
            f"{'Groq Llama3-8B':<20} {f'{groq_success}/{len(groq_results)}':<15} {'N/A':<12} {'N/A':<12} {'N/A':<12}"
        )

    # Local Llama stats
    if llama_results:
        if llama_times:
            print(
                f"{'Local Llama3-Q4':<20} {f'{llama_success}/{len(llama_results)}':<15} "
                f"{f'{llama_avg:.2f}s':<12} {f'{min(llama_times):.2f}s':<12} {f'{max(llama_times):.2f}s':<12}"
            )
        else:
            print(
                f"{'Local Llama3-Q4':<20} {f'{llama_success}/{len(llama_results)}':<15} {'N/A':<12} {'N/A':<12} {'N/A':<12}"
            )

    # Preprocessing effectiveness
    print(f"\n🔬 Preprocessing Effectiveness:")
    for name, results in [
        ("GPT-4o-mini", openai_results),
        ("Groq", groq_results),
        ("Local", llama_results),
    ]:
        if results:
            high_conf = sum(
                1 for r in results if r.get("preprocessing_confidence", 0) >= 0.7
            )
            if high_conf > 0:
                print(
                    f"  - {name}: {high_conf}/{len(results)} tasks preprocessed with high confidence"
                )

    print(f"\n✅ Success Rate:")
    print(
        f"  - GPT-4o-mini: {sum(1 for r in openai_results if r['success'])}/{len(openai_results)}"
    )
    print(
        f"  - Groq Llama3-8B: {sum(1 for r in groq_results if r['success'])}/{len(groq_results)}"
    )
    if llama_results:
        print(
            f"  - Local Llama3-Q4: {sum(1 for r in llama_results if r['success'])}/{len(llama_results)}"
        )

    # Failure analysis
    if openai_results:
        analyze_failures(openai_results, "GPT-4o-mini")
    if groq_results:
        analyze_failures(groq_results, "Groq")
    if llama_results:
        analyze_failures(llama_results, "Local Llama")

    print(f"\n📋 Top 10 Slowest Tasks (successful only):")
    all_results = []
    for r in openai_results:
        if r["success"]:
            all_results.append(("GPT-4o", r["input"][:60], r["total_time"]))
    for r in groq_results:
        if r["success"]:
            all_results.append(("Groq", r["input"][:60], r["total_time"]))
    if llama_results:
        for r in llama_results:
            if r["success"]:
                all_results.append(("Local", r["input"][:60], r["total_time"]))

    all_results.sort(key=lambda x: x[2], reverse=True)
    print(f"\n{'Model':<10} {'Test':<62} {'Time':<10}")
    print("-" * 82)
    for model, test, time in all_results[:10]:
        print(f"{model:<10} {test:<62} {time:.2f}s")

    # Success rate by test complexity (first 10 = complex temporal, 11-20 = ambiguous, 21-30 = edge cases)
    print(f"\n🎯 Success Rate by Test Category:")
    categories = [
        ("Complex Temporal (1-10)", 0, 10),
        ("Ambiguous Context (11-20)", 10, 20),
        ("Edge Cases (21-30)", 20, 30),
    ]

    for cat_name, start, end in categories:
        print(f"\n{cat_name}:")
        for name, results in [
            ("GPT-4o-mini", openai_results),
            ("Groq", groq_results),
            ("Local", llama_results),
        ]:
            if results and len(results) >= end:
                cat_results = results[start:end]
                success = sum(1 for r in cat_results if r["success"])
                print(
                    f"  - {name}: {success}/{len(cat_results)} ({success/len(cat_results)*100:.0f}%)"
                )


def main():
    """Run the comparison."""
    import argparse

    parser = argparse.ArgumentParser(description="Compare model performance")
    parser.add_argument(
        "--include-local", action="store_true", help="Include local Llama model tests"
    )
    parser.add_argument(
        "--local-only", action="store_true", help="Test only local Llama model"
    )
    parser.add_argument(
        "--model-variant",
        default="q4",
        choices=["fp16", "q8", "q4"],
        help="Local model variant",
    )
    args = parser.parse_args()

    print(f"🔄 Initializing models...\n")
    print(f"Loaded {len(TEST_CASES)} test cases from comprehensive suite.")

    openai_results = []
    groq_results = []
    llama_results = None

    if not args.local_only:
        # Test OpenAI
        print("\n1️⃣ Testing GPT-4o-mini (OpenAI):")
        assistant = get_or_create_assistant()
        if not assistant:
            print("Failed to initialize OpenAI assistant")
            return

        openai_results = test_model(
            "GPT-4o-mini", parse_openai, TEST_CASES, assistant, show_progress=True
        )

        # Test Groq
        print("\n\n2️⃣ Testing Llama3-8B (Groq):")
        groq_results = test_model("Groq", parse_groq, TEST_CASES, show_progress=True)

    # Test Local Llama if requested
    if args.include_local or args.local_only:
        print(f"\n\n3️⃣ Testing Local Llama3 ({args.model_variant.upper()}):")

        # Wrapper to pass model variant
        def parse_llama_wrapper(text):
            return parse_llama(text, model_variant=args.model_variant)

        llama_results = test_model(
            "Local Llama", parse_llama_wrapper, TEST_CASES, show_progress=True
        )

    # Print comparison
    if not args.local_only:
        print_comparison(openai_results, groq_results, llama_results)

        # Get averages for recommendation
        openai_times = [r["total_time"] for r in openai_results if r["success"]]
        groq_times = [r["total_time"] for r in groq_results if r["success"]]
        openai_avg = sum(openai_times) / len(openai_times) if openai_times else 0
        groq_avg = sum(groq_times) / len(groq_times) if groq_times else 0

        print("\n💡 Recommendations:")

        # Speed recommendation
        if groq_success > len(groq_results) * 0.8 and groq_avg < openai_avg * 0.5:
            print(
                "  • Groq is the clear winner for speed with good accuracy (when not rate limited)"
            )
        elif llama_results and llama_success > len(llama_results) * 0.8:
            print("  • Local Llama provides consistent performance without rate limits")
        else:
            print("  • GPT-4o-mini provides the best accuracy but at higher latency")

        # Rate limit consideration
        groq_rate_limited = sum(
            1
            for r in groq_results
            if not r["success"] and "rate_limit" in r.get("error", "")
        )
        if groq_rate_limited > 5:
            print(f"  • Warning: Groq hit rate limits on {groq_rate_limited} tests")
            print(
                "    Consider: Paid Groq tier, request batching, or local models for high volume"
            )

        # Local model recommendation
        if llama_results:
            if llama_avg < 5.0:
                print("  • Local Llama is fast enough for real-time use (<5s average)")
            else:
                print(
                    "  • Consider GPU acceleration or smaller models for better local performance"
                )
    else:
        # Local only results
        llama_times = [r["total_time"] for r in llama_results if r["success"]]
        llama_avg = sum(llama_times) / len(llama_times) if llama_times else 0
        print(
            f"\n📊 Local Llama3-{args.model_variant.upper()} Average: {llama_avg:.2f}s"
        )
        print(
            f"✅ Success Rate: {sum(1 for r in llama_results if r['success'])}/{len(llama_results)}"
        )


if __name__ == "__main__":
    main()
