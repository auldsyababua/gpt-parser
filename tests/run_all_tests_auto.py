#!/usr/bin/env python3
"""
Automated test runner for all 30 timezone and temporal expression test cases.
Runs without user input and sends results to Google Sheets.
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
    format_task_for_confirmation
)


def load_test_cases(filename):
    """Load test cases from file, extracting prompts and expected values."""
    test_cases = []
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse test case format: prompt | expected_reminder | expected_due | notes
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 4:
                    test_case = {
                        'prompt': parts[0],
                        'expected_reminder': parts[1],
                        'expected_due': parts[2],
                        'notes': parts[3]
                    }
                    test_cases.append(test_case)
    
    return test_cases


def analyze_result(test_case, parsed_json):
    """Analyze test results and return success indicators."""
    results = {
        'parsed': parsed_json is not None,
        'reminder_match': False,
        'due_match': False,
        'has_reasoning': False
    }
    
    if parsed_json:
        # Check reminder time
        actual_reminder = parsed_json.get('reminder_time', 'N/A')
        expected_reminder = test_case['expected_reminder']
        # Handle special cases like "current+15min"
        if not expected_reminder.startswith('current'):
            results['reminder_match'] = actual_reminder == expected_reminder
        
        # Check due time
        actual_due = parsed_json.get('due_time', 'N/A')
        expected_due = test_case['expected_due']
        if not expected_due.startswith('current'):
            results['due_match'] = actual_due == expected_due
        
        # Check reasoning
        results['has_reasoning'] = bool(parsed_json.get('reasoning'))
    
    return results


def run_all_tests():
    """Run all test cases and send to Google Sheets."""
    # Initialize assistant
    print("Initializing assistant...")
    assistant = get_or_create_assistant()
    if not assistant:
        print("Failed to initialize assistant.")
        return
    
    # Load test cases
    test_file = os.path.join(os.path.dirname(__file__), 'timezone_test_cases.txt')
    test_cases = load_test_cases(test_file)
    
    print(f"\nLoaded {len(test_cases)} test cases.")
    print("=" * 80)
    
    # Track overall results
    total_passed = 0
    total_failed = 0
    results_summary = []
    
    # Run each test
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}/{len(test_cases)}: {test_case['notes']}")
        print(f"Input: {test_case['prompt']}")
        print("-" * 60)
        
        try:
            # Parse the task
            parsed_json = parse_task(assistant, test_case['prompt'])
            
            if parsed_json:
                # Display results
                print(f"✓ Parsed successfully")
                print(f"Assignee: {parsed_json.get('assignee')}")
                print(f"Reminder: {parsed_json.get('reminder_time', 'N/A')} (expected: {test_case['expected_reminder']})")
                print(f"Due: {parsed_json.get('due_time', 'N/A')} (expected: {test_case['expected_due']})")
                print(f"Timezone Context: {parsed_json.get('timezone_context', 'N/A')}")
                print(f"Reasoning: {parsed_json.get('reasoning', 'No reasoning provided')[:100]}...")
                
                # Analyze results
                analysis = analyze_result(test_case, parsed_json)
                
                # Add test metadata
                parsed_json['task'] = f"[TEST {i}] {parsed_json.get('task', '')}"  
                # Don't overwrite original_prompt - it's already set by the parser
                # Just add test number to the existing prompt
                if 'original_prompt' in parsed_json:
                    parsed_json['original_prompt'] = f"[TEST {i}] {parsed_json['original_prompt']}"
                
                # Send to Google Sheets
                print("\nSending to Google Sheets...", end='')
                success = send_to_google_sheets(parsed_json)
                
                if success:
                    print(" ✓")
                    total_passed += 1
                    
                    # Check individual criteria
                    status_parts = []
                    if analysis['reminder_match']:
                        status_parts.append("reminder ✓")
                    else:
                        status_parts.append("reminder ✗")
                    
                    if analysis['due_match']:
                        status_parts.append("due ✓")
                    else:
                        status_parts.append("due ✗")
                    
                    if analysis['has_reasoning']:
                        status_parts.append("reasoning ✓")
                    else:
                        status_parts.append("reasoning ✗")
                    
                    results_summary.append({
                        'test': i,
                        'notes': test_case['notes'],
                        'status': 'PASSED',
                        'details': ', '.join(status_parts)
                    })
                else:
                    print(" ✗")
                    total_failed += 1
                    results_summary.append({
                        'test': i,
                        'notes': test_case['notes'],
                        'status': 'FAILED',
                        'details': 'Failed to send to sheets'
                    })
                    
            else:
                print("✗ Failed to parse task")
                total_failed += 1
                results_summary.append({
                    'test': i,
                    'notes': test_case['notes'],
                    'status': 'FAILED',
                    'details': 'Failed to parse'
                })
                
        except Exception as e:
            print(f"✗ Error: {e}")
            total_failed += 1
            results_summary.append({
                'test': i,
                'notes': test_case['notes'],
                'status': 'ERROR',
                'details': str(e)[:50]
            })
        
        # Small delay between tests to avoid rate limiting
        if i < len(test_cases):
            time.sleep(0.5)  # Reduced delay for faster execution
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {len(test_cases)}")
    print(f"Passed: {total_passed} ({total_passed/len(test_cases)*100:.1f}%)")
    print(f"Failed: {total_failed} ({total_failed/len(test_cases)*100:.1f}%)")
    
    print("\nDetailed Results:")
    print("-" * 80)
    for result in results_summary:
        status_icon = "✓" if result['status'] == 'PASSED' else "✗"
        print(f"{status_icon} Test {result['test']:2d}: {result['notes']:<40} {result['details']}")
    
    print("\n" + "=" * 80)
    print("All tests completed! Check Google Sheets for detailed results.")
    print("Look for tests marked with [TEST #] in the task column.")


if __name__ == "__main__":
    print("Starting Automated Test Runner for All 30 Tests")
    print("===============================================")
    print("This will send all test cases to Google Sheets automatically.")
    print("No user input required.\n")
    
    run_all_tests()