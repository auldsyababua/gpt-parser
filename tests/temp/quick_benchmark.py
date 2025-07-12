#!/usr/bin/env python3
"""
Quick benchmark of local models with simplified prompts.
"""

import time
import json
import requests
import logging
import os
import sys
from typing import List, Dict, Any

# Set up logging to match telegram_bot.py
LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "quick_benchmark.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# 30 unique test cases
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

# Simplified prompt template
SIMPLE_PROMPT = """You are a task parser. Convert the task to JSON.

Required fields:
- assignee: Colin, Bryan, or Joel
- assigner: Always "Colin"
- task: Brief description
- due_date: YYYY-MM-DD format
- due_time: HH:MM format (optional)
- status: Always "pending"

Today is 2025-07-11, current time 16:00 PST.

Task: {}

Return only valid JSON:"""


def test_model(model_name: str, prompts: List[str]) -> List[Dict[str, Any]]:
    """Test a model with all prompts."""
    logger.info(f"Starting benchmark for model: {model_name}")
    print(f"\n{'='*60}")
    print(f"Testing: {model_name}")
    print(f"{'='*60}")

    results = []
    successful = 0
    total_time = 0

    for i, test_prompt in enumerate(prompts, 1):
        logger.info(f"[{i}/{len(prompts)}] Starting test for: {test_prompt}")
        print(f"\n[{i}/{len(prompts)}] Testing: {test_prompt[:50]}...")

        # Build prompt
        full_prompt = SIMPLE_PROMPT.format(test_prompt)
        logger.debug(f"Full prompt: {full_prompt[:200]}...")

        try:
            start_time = time.time()
            logger.info(f"Sending request to Ollama API for prompt {i}")

            # Build request payload
            request_payload = {
                "model": model_name,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 500,
                },
            }

            logger.debug("Request URL: http://localhost:11434/api/generate")
            logger.debug(f"Request model: {model_name}")
            logger.debug("Request timeout: 10 seconds")
            logger.debug(f"Prompt length: {len(full_prompt)} characters")
            logger.debug("Temperature: 0.1, Max tokens: 500")

            response = requests.post(
                "http://localhost:11434/api/generate",
                json=request_payload,
                timeout=10,  # Reduced timeout
            )

            elapsed = time.time() - start_time
            total_time += elapsed
            logger.info(
                f"Received response in {elapsed:.2f}s, status: {response.status_code}"
            )

            if response.status_code == 200:
                result = response.json()
                assistant_response = result.get("response", "").strip()
                logger.debug(f"Assistant response: {assistant_response[:200]}...")

                # Extract JSON
                if "```json" in assistant_response:
                    json_str = (
                        assistant_response.split("```json")[1].split("```")[0].strip()
                    )
                    logger.debug("Found JSON in markdown code block")
                elif "```" in assistant_response:
                    json_str = (
                        assistant_response.split("```")[1].split("```")[0].strip()
                    )
                    logger.debug("Found JSON in code block")
                else:
                    # Try to find JSON
                    import re

                    json_match = re.search(r"\{[^}]+\}", assistant_response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        logger.debug("Found JSON using regex")
                    else:
                        json_str = assistant_response
                        logger.debug("Using raw response as JSON")

                try:
                    parsed = json.loads(json_str)
                    logger.debug(f"Successfully parsed JSON: {parsed}")
                    # Check required fields
                    required = ["assignee", "task", "due_date"]
                    missing = [f for f in required if f not in parsed]
                    if not missing:
                        successful += 1
                        logger.info("✅ Success! All required fields present")
                        results.append(
                            {
                                "prompt": test_prompt,
                                "success": True,
                                "time": elapsed,
                            }
                        )
                    else:
                        logger.warning(f"❌ Missing required fields: {missing}")
                        results.append(
                            {
                                "prompt": test_prompt,
                                "success": False,
                                "time": elapsed,
                                "error": f"Missing fields: {missing}",
                            }
                        )
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON decode error: {e}")
                    logger.debug(f"Failed to parse: {json_str[:200]}...")
                    results.append(
                        {
                            "prompt": test_prompt,
                            "success": False,
                            "time": elapsed,
                            "error": "JSON error",
                        }
                    )
            else:
                logger.error(f"❌ API returned non-200 status: {response.status_code}")
                logger.error(f"Response headers: {dict(response.headers)}")
                try:
                    logger.error(f"Response body: {response.text[:500]}...")
                except:
                    logger.error("Could not read response body")
                results.append(
                    {
                        "prompt": test_prompt,
                        "success": False,
                        "time": elapsed,
                        "error": f"API {response.status_code}",
                    }
                )

        except requests.exceptions.Timeout:
            elapsed = time.time() - start_time
            logger.error(f"❌ TIMEOUT after {elapsed:.2f}s waiting for Ollama")
            logger.error(f"Model: {model_name}")
            logger.error(f"Prompt #{i} of {len(prompts)}: {test_prompt}")
            logger.error(f"Prompt length: {len(full_prompt)} chars")
            logger.error("Consider: Is Ollama overloaded? Is the model loaded?")
            results.append(
                {
                    "prompt": test_prompt,
                    "success": False,
                    "time": 10.0,
                    "error": "Timeout",
                }
            )
        except requests.exceptions.ConnectionError as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ CONNECTION ERROR after {elapsed:.2f}s")
            logger.error("Could not connect to Ollama at http://localhost:11434")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {str(e)}")
            logger.error("Is Ollama running? Try: ollama serve")
            results.append(
                {
                    "prompt": test_prompt,
                    "success": False,
                    "time": elapsed,
                    "error": "Connection failed",
                }
            )
        except json.JSONDecodeError as e:
            elapsed = time.time() - start_time
            logger.error("❌ JSON DECODE ERROR in response parsing")
            logger.error("This shouldn't happen here - check code logic")
            logger.error(f"Error: {e}")
            results.append(
                {
                    "prompt": test_prompt,
                    "success": False,
                    "time": elapsed,
                    "error": "Response parse fail",
                }
            )
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ UNEXPECTED ERROR: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.error(f"This happened after {elapsed:.2f}s")
            logger.error(f"On prompt #{i}: {test_prompt[:100]}...")
            logger.error(f"Model: {model_name}")
            logger.error("Full stack trace:", exc_info=True)
            results.append(
                {
                    "prompt": test_prompt,
                    "success": False,
                    "time": elapsed,
                    "error": str(e)[:50],
                }
            )

        # Progress tracking
        logger.info(f"Completed {i}/{len(prompts)} tests")
        logger.info(
            f"Success so far: {successful}/{i} ({successful/i*100:.1f}% success rate)"
        )
        logger.info(f"Average time so far: {total_time/i:.2f}s per request")
        logger.debug("Sleeping 0.5s before next request...")
        time.sleep(0.5)
        logger.debug("Sleep complete, moving to next test")

    logger.info(f"=== FINAL RESULTS for {model_name} ===")
    logger.info(f"Total tests: {len(prompts)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {len(prompts) - successful}")
    logger.info(f"Success rate: {successful/len(prompts)*100:.1f}%")
    logger.info(f"Total time: {total_time:.2f}s")
    logger.info(f"Average time per request: {total_time/len(prompts):.2f}s")

    print(
        f"\n{model_name}: {successful}/{len(prompts)} successful, avg {total_time/len(prompts):.2f}s/request"
    )
    return results


def main():
    logger.info("=" * 80)
    logger.info("STARTING QUICK LOCAL MODEL BENCHMARK")
    logger.info("=" * 80)
    logger.info(f"Script started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Number of test cases: {len(TEST_CASES)}")
    logger.info("Models to test: llama3:8b-instruct-q4_0, phi3:latest")

    print("Quick Local Model Benchmark")
    print("30 unique task parsing prompts, simplified prompt template")

    # Check if Ollama is running
    logger.info("Checking if Ollama is running...")
    try:
        test_response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if test_response.status_code == 200:
            logger.info("✅ Ollama is running!")
            models_data = test_response.json()
            available_models = [m["name"] for m in models_data.get("models", [])]
            logger.info(f"Available models: {available_models}")

            # Check if our test models are available
            if "llama3:8b-instruct-q4_0" not in available_models:
                logger.warning(
                    "⚠️  llama3:8b-instruct-q4_0 not found in available models!"
                )
            if "phi3:latest" not in available_models:
                logger.warning("⚠️  phi3:latest not found in available models!")
        else:
            logger.error(f"Ollama API returned status {test_response.status_code}")
    except Exception as e:
        logger.error(f"❌ Cannot connect to Ollama: {e}")
        logger.error("Please ensure Ollama is running with: ollama serve")
        print("\n❌ ERROR: Cannot connect to Ollama. Please run: ollama serve")
        return

    # Test both models
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 1: Testing Llama3")
    logger.info("=" * 60)
    llama_results = test_model("llama3:8b-instruct-q4_0", TEST_CASES)

    logger.info("\n" + "=" * 60)
    logger.info("PHASE 2: Testing Phi-3")
    logger.info("=" * 60)
    phi_results = test_model("phi3:latest", TEST_CASES)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("GENERATING FINAL SUMMARY")
    logger.info("=" * 60)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for name, results in [("Llama3 Q4", llama_results), ("Phi-3", phi_results)]:
        logger.info(f"\nAnalyzing results for {name}...")
        logger.info(f"Total results: {len(results)}")

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        logger.info(f"Successful: {len(successful)}")
        logger.info(f"Failed: {len(failed)}")

        if successful:
            times = [r["time"] for r in successful]
            logger.info(
                f"Response times for successful requests: {[f'{t:.2f}' for t in times]}"
            )
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            logger.info(f"Average time: {avg_time:.2f}s")
            logger.info(f"Min time: {min_time:.2f}s")
            logger.info(f"Max time: {max_time:.2f}s")
            logger.info(f"Time variance: {max_time - min_time:.2f}s")

            print(f"\n{name}:")
            print(
                f"  Success rate: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)"
            )
            print(f"  Average time: {avg_time:.2f}s")
            print(f"  Min/Max time: {min_time:.2f}s / {max_time:.2f}s")
        else:
            logger.error(f"❌ {name} had ZERO successful parses!")
            print(f"\n{name}: 0% success rate")

    # Category breakdown
    categories = [
        ("Basic (1-10)", 0, 10),
        ("Complex (11-20)", 10, 20),
        ("Edge cases (21-30)", 20, 30),
    ]

    logger.info("\n" + "=" * 40)
    logger.info("CATEGORY ANALYSIS")
    logger.info("=" * 40)

    print("\nCategory Success Rates:")
    print(f"{'Category':<20} {'Llama3':<15} {'Phi-3':<15}")
    print("-" * 50)

    for cat_name, start, end in categories:
        logger.info(f"\nAnalyzing category: {cat_name}")
        logger.info(f"Test cases {start+1} to {end}")

        llama_cat_results = llama_results[start:end]
        phi_cat_results = phi_results[start:end]

        llama_cat = sum(1 for r in llama_cat_results if r["success"])
        phi_cat = sum(1 for r in phi_cat_results if r["success"])

        logger.info(f"Llama3 success in {cat_name}: {llama_cat}/10")
        logger.info(f"Phi-3 success in {cat_name}: {phi_cat}/10")

        # Log which specific prompts failed in this category
        llama_cat_failures = [
            i + start + 1 for i, r in enumerate(llama_cat_results) if not r["success"]
        ]
        phi_cat_failures = [
            i + start + 1 for i, r in enumerate(phi_cat_results) if not r["success"]
        ]

        if llama_cat_failures:
            logger.info(f"Llama3 failed on prompts: {llama_cat_failures}")
        if phi_cat_failures:
            logger.info(f"Phi-3 failed on prompts: {phi_cat_failures}")

        print(
            f"{cat_name:<20} {llama_cat}/10 ({llama_cat*10}%)  {phi_cat}/10 ({phi_cat*10}%)"
        )

    # Show failures
    logger.info("\n" + "=" * 40)
    logger.info("FAILURE ANALYSIS")
    logger.info("=" * 40)

    print("\nSample Failures:")
    for name, results in [("Llama3", llama_results), ("Phi-3", phi_results)]:
        failures = [(i + 1, r) for i, r in enumerate(results) if not r["success"]]

        logger.info(f"\n{name} failure analysis:")
        logger.info(f"Total failures: {len(failures)}")

        if failures:
            # Group failures by error type
            error_types = {}
            for idx, r in failures:
                error = r.get("error", "Unknown")
                if error not in error_types:
                    error_types[error] = []
                error_types[error].append(idx)

            logger.info("Failure breakdown by error type:")
            for error, indices in error_types.items():
                logger.info(
                    f"  {error}: {len(indices)} failures (prompts: {indices[:5]}{'...' if len(indices) > 5 else ''})"
                )

            print(f"\n{name} failed on:")
            for idx, r in failures[:3]:
                logger.info(f"Showing failure #{idx}: {r['prompt']}")
                logger.info(f"  Error: {r['error']}")
                logger.info(f"  Time taken: {r.get('time', 'N/A')}s")
                print(f"  #{idx}: {r['prompt'][:40]}... ({r['error']})")
            if len(failures) > 3:
                print(f"  ... and {len(failures)-3} more")


if __name__ == "__main__":
    logger.info("Script quick_benchmark.py starting...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current working directory: {os.getcwd()}")

    try:
        main()
        logger.info("\n" + "=" * 80)
        logger.info("BENCHMARK COMPLETED SUCCESSFULLY")
        logger.info(f"Script ended at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Script interrupted by user (Ctrl+C)")
        print("\n\nBenchmark interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ FATAL ERROR: {type(e).__name__}: {e}", exc_info=True)
        print(f"\n\n❌ Fatal error: {e}")
        raise
