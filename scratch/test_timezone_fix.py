#!/usr/bin/env python3
"""Test timezone parsing fix directly"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.temporal_processor import TemporalProcessor
from config.timezone_config import get_user_timezone

# Test the timezone config
print("\n=== Testing Timezone Config ===")
for user in ["colin", "Colin", "COLIN"]:
    tz = get_user_timezone(user)
    print(f"get_user_timezone('{user}') = {tz}")

# Test temporal processing
print("\n=== Testing Temporal Processing ===")

# Test case that was failing
test_input = "do my homework tomorrow at 4"
assignee = "colin"

# Get the user's timezone
user_tz = get_user_timezone(assignee)
processor = TemporalProcessor(default_timezone=str(user_tz))

print(f"\nInput: '{test_input}'")
print(f"Assignee: '{assignee}'")
print(f"User timezone: {user_tz}")

# Process with assignee timezone
result = processor.preprocess(test_input)
print("\nProcessed result:")
print(f"  Full result: {result}")
if "error" not in result:
    print(f"  Modified text: {result.get('modified_text', 'N/A')}")
    print(f"  Due date found: {result.get('due_date', 'N/A')}")
    print(f"  Original was modified: {result.get('was_modified', False)}")
else:
    print(f"  Error: {result['error']}")

# Also test directly with dateparser
import dateparser

print("\n=== Direct dateparser test ===")
test_times = ["tomorrow at 4", "tomorrow at 4pm", "tomorrow at 16:00"]
for test in test_times:
    parsed = dateparser.parse(test, settings={"TIMEZONE": "America/Los_Angeles"})
    print(f"'{test}' -> {parsed}")
