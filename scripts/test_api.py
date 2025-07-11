#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assistants_api_runner import get_or_create_assistant, parse_task
import time

print("Testing API connection...")
start = time.time()

try:
    # Get assistant
    print("Getting assistant...")
    assistant = get_or_create_assistant()
    if not assistant:
        print("Failed to get assistant")
        sys.exit(1)
    
    print(f"Assistant ID: {assistant['id']}")
    
    # Test parse
    print("\nTesting parse_task...")
    test_input = "Remind Joel at 3pm to check batteries"
    result = parse_task(assistant, test_input)
    
    if result:
        print("\nSuccess! Parsed result:")
        import json
        print(json.dumps(result, indent=2))
    else:
        print("\nFailed to parse")
    
    elapsed = time.time() - start
    print(f"\nTotal time: {elapsed:.2f} seconds")
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()