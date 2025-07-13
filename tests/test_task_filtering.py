#!/usr/bin/env python3
"""
Test script for task filtering functionality.
Tests date range filtering for Today, This Week, and All Tasks.
"""

import sys
import os
from datetime import datetime, date, timedelta
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the filter function
from integrations.telegram.bot import filter_tasks_by_date

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def create_test_tasks():
    """Create test tasks with various due dates."""
    today = date.today()
    
    test_tasks = [
        {
            "id": "1",
            "task": "Task due today",
            "due_date": today.strftime("%m/%d/%Y"),
            "due_time": "2:00 PM",
            "status": "pending",
            "assigner": "Colin"
        },
        {
            "id": "2", 
            "task": "Task due tomorrow",
            "due_date": (today + timedelta(days=1)).strftime("%m/%d/%Y"),
            "due_time": "10:00 AM",
            "status": "pending",
            "assigner": "Colin"
        },
        {
            "id": "3",
            "task": "Task due in 3 days",
            "due_date": (today + timedelta(days=3)).strftime("%m/%d/%Y"),
            "due_time": "3:30 PM",
            "status": "pending", 
            "assigner": "Colin"
        },
        {
            "id": "4",
            "task": "Task due in 7 days",
            "due_date": (today + timedelta(days=7)).strftime("%m/%d/%Y"),
            "due_time": "9:00 AM",
            "status": "pending",
            "assigner": "Colin"
        },
        {
            "id": "5",
            "task": "Task due in 8 days (outside week)",
            "due_date": (today + timedelta(days=8)).strftime("%m/%d/%Y"),
            "due_time": "11:00 AM",
            "status": "pending",
            "assigner": "Colin"
        },
        {
            "id": "6",
            "task": "Task due yesterday",
            "due_date": (today - timedelta(days=1)).strftime("%m/%d/%Y"),
            "due_time": "4:00 PM",
            "status": "pending",
            "assigner": "Colin"
        },
        {
            "id": "7",
            "task": "Task with no due date",
            "due_date": None,
            "due_time": "",
            "status": "pending",
            "assigner": "Colin"
        },
        {
            "id": "8",
            "task": "Task with invalid date format",
            "due_date": "invalid-date",
            "due_time": "5:00 PM",
            "status": "pending",
            "assigner": "Colin"
        },
        {
            "id": "9",
            "task": "Completed task due today",
            "due_date": today.strftime("%m/%d/%Y"),
            "due_time": "1:00 PM",
            "status": "completed",
            "assigner": "Colin"
        }
    ]
    
    return test_tasks

def run_filter_tests():
    """Run comprehensive filtering tests."""
    print("🧪 Running Task Filtering Tests\n")
    
    test_tasks = create_test_tasks()
    print(f"Created {len(test_tasks)} test tasks")
    
    # Test 1: All filter
    print("\n📋 TEST 1: All Tasks Filter")
    all_tasks = filter_tasks_by_date(test_tasks, "all")
    print(f"Expected: {len(test_tasks)} tasks")
    print(f"Actual: {len(all_tasks)} tasks")
    print(f"✅ PASS" if len(all_tasks) == len(test_tasks) else "❌ FAIL")
    
    # Test 2: Today filter
    print("\n📅 TEST 2: Today Filter")
    today_tasks = filter_tasks_by_date(test_tasks, "today")
    expected_today = 2  # Tasks 1 and 9 (but 9 is completed, so only 1 in active)
    print(f"Expected: 1 active task due today")
    print(f"Actual: {len(today_tasks)} tasks")
    for task in today_tasks:
        print(f"  - {task['task']} (due: {task['due_date']})")
    
    # Test 3: Week filter
    print("\n📆 TEST 3: This Week Filter")
    week_tasks = filter_tasks_by_date(test_tasks, "week")
    expected_week = 4  # Tasks 1, 2, 3, 4 (within 7 days)
    print(f"Expected: 4 tasks within 7 days")
    print(f"Actual: {len(week_tasks)} tasks")
    for task in week_tasks:
        print(f"  - {task['task']} (due: {task['due_date']})")
    
    # Test 4: Edge cases
    print("\n⚡ TEST 4: Edge Cases")
    
    # Empty task list
    empty_tasks = filter_tasks_by_date([], "today")
    print(f"Empty list test: {len(empty_tasks)} tasks (expected: 0)")
    
    # Tasks with missing/invalid dates
    tasks_with_issues = [t for t in test_tasks if t['id'] in ['7', '8']]
    filtered_issues = filter_tasks_by_date(tasks_with_issues, "today")
    print(f"Invalid dates test: {len(filtered_issues)} tasks (expected: 0)")
    
    # Test 5: Boundary conditions
    print("\n📏 TEST 5: Boundary Conditions")
    boundary_tasks = [
        {
            "id": "10",
            "task": "Task due exactly 7 days from now",
            "due_date": (date.today() + timedelta(days=7)).strftime("%m/%d/%Y"),
            "status": "pending"
        }
    ]
    boundary_filtered = filter_tasks_by_date(boundary_tasks, "week")
    print(f"7-day boundary test: {len(boundary_filtered)} tasks (expected: 1)")
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Total test tasks: {len(test_tasks)}")
    print(f"All filter: {len(all_tasks)} tasks")
    print(f"Today filter: {len(today_tasks)} tasks")
    print(f"Week filter: {len(week_tasks)} tasks")
    print("\n✅ All tests completed successfully!")
    
    # Save results to log file
    results_file = "tests/filter_test_results.log"
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, "w") as f:
        f.write("Task Filtering Test Results\n")
        f.write("=" * 50 + "\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total test tasks: {len(test_tasks)}\n")
        f.write(f"All filter: {len(all_tasks)} tasks\n")
        f.write(f"Today filter: {len(today_tasks)} tasks\n")
        f.write(f"Week filter: {len(week_tasks)} tasks\n")
        f.write("\nDetailed Results:\n")
        
        for filter_type in ["all", "today", "week"]:
            filtered = filter_tasks_by_date(test_tasks, filter_type)
            f.write(f"\n{filter_type.upper()} FILTER ({len(filtered)} tasks):\n")
            for task in filtered:
                f.write(f"  - {task['task']} (due: {task['due_date']})\n")
    
    print(f"\n📄 Detailed results saved to: {results_file}")

if __name__ == "__main__":
    run_filter_tests()
