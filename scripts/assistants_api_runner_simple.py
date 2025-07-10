import json
import requests
import os
import sys
import time
import logging
from dotenv import load_dotenv
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.timezone_config import get_user_timezone
from utils.timezone_converter import process_task_with_timezones

# --- Configuration ---
load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY not found in .env file or environment.")
    sys.exit(1)

GOOGLE_APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzZZkhc3f9nP4IcllbuH24c22D-nlsWrlOEAWc0sr-VNxuiWKLKhsx96W1-6koShzsxTg/exec"
ASSISTANT_NAME = "Task Parser Simple"
ASSISTANT_MODEL = "gpt-4-turbo-preview"
COMBINED_PROMPT_FILE = os.path.join(
    os.path.dirname(__file__), "..", "prompts", "combined_system_prompt.txt"
)
LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "api_log.txt")

# --- API Details ---
OPENAI_API_BASE_URL = "https://api.openai.com/v1"
HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json",
    "OpenAI-Beta": "assistants=v2",
}

# --- Logging ---
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)


def log_interaction(message):
    logging.info(message)


def handle_api_error(response, error_message):
    log_interaction(f"API Error: {error_message} - Status: {response.status_code}")
    try:
        error_details = response.json()
        log_interaction(
            f"{error_message}\nResponse: {json.dumps(error_details, indent=2)}"
        )
        print(f"{error_message}\nResponse: {error_details}")
    except json.JSONDecodeError:
        error_details = response.text
        log_interaction(f"{error_message}\nResponse: {error_details}")
        print(f"{error_message}\nResponse: {error_details}")
    return None


def api_request(method, url, **kwargs):
    """Wrapper for requests to log the interaction."""
    log_interaction(
        f"Request: {method.upper()} {url}\nHeaders: {kwargs.get('headers')}\nPayload: {kwargs.get('json')}"
    )
    response = requests.request(method, url, **kwargs)
    log_interaction(f"Response: {response.status_code}\nBody: {response.text}")
    return response


def get_or_create_assistant():
    """
    Retrieves an existing assistant or creates a new one with combined prompt.
    """
    # Check for existing assistant
    assistants_url = f"{OPENAI_API_BASE_URL}/assistants"
    response = api_request(
        "get", assistants_url, headers=HEADERS, params={"limit": 100}
    )
    if response.status_code == 200:
        assistants = response.json().get("data", [])
        for assistant in assistants:
            if assistant.get("name") == ASSISTANT_NAME:
                print(f"Found existing assistant with ID: {assistant['id']}")
                # Update with latest prompt
                with open(COMBINED_PROMPT_FILE, "r") as f:
                    system_prompt = f.read()
                
                update_url = f"{OPENAI_API_BASE_URL}/assistants/{assistant['id']}"
                update_payload = {"instructions": system_prompt}
                update_response = api_request(
                    "post", update_url, headers=HEADERS, json=update_payload
                )
                if update_response.status_code == 200:
                    print(f"Updated assistant with latest prompt.")
                    return update_response.json()
                else:
                    return handle_api_error(update_response, "assistant update")

    # Create a new assistant
    print(f"No existing assistant named '{ASSISTANT_NAME}'. Creating a new one.")
    try:
        with open(COMBINED_PROMPT_FILE, "r") as f:
            system_prompt = f.read()

        payload = {
            "name": ASSISTANT_NAME,
            "instructions": system_prompt,
            "model": ASSISTANT_MODEL,
            "tools": [],  # No tools needed - everything is in the prompt
        }
        response = api_request("post", assistants_url, headers=HEADERS, json=payload)
        if response.status_code == 200:
            new_assistant = response.json()
            print(f"Created new assistant with ID: {new_assistant['id']}")
            return new_assistant
        else:
            return handle_api_error(response, "assistant creation")

    except Exception as e:
        print(f"An unexpected error occurred during assistant creation: {e}")
        sys.exit(1)


def parse_task(assistant, input_text, assigner="Colin"):
    """
    Uses the assistant to parse input text and returns the parsed JSON.
    
    Args:
        assistant: The OpenAI assistant object
        input_text: The natural language task description
        assigner: The person assigning the task (default: Colin)
    """
    logger = logging.getLogger(__name__)
    logger.info(f"parse_task called with input: {input_text}")
    
    # Get assigner's timezone
    assigner_tz = get_user_timezone(assigner)
    
    # Inject current date in assigner's timezone into the prompt
    today_in_tz = datetime.now(assigner_tz)
    today_str = today_in_tz.strftime("%Y-%m-%d")
    prompt_with_date = (
        f"(Today's date is {today_str} in {assigner}'s timezone) {input_text}"
    )
    print(f"\nProcessing input: '{prompt_with_date}'")

    assistant_id = assistant["id"]

    try:
        # 1. Create a thread
        threads_url = f"{OPENAI_API_BASE_URL}/threads"
        thread_payload = {
            "messages": [{"role": "user", "content": prompt_with_date}]
        }
        thread_response = api_request(
            "post", threads_url, headers=HEADERS, json=thread_payload
        )
        if thread_response.status_code != 200:
            return handle_api_error(thread_response, "thread creation")
        thread = thread_response.json()
        thread_id = thread["id"]
        print(f"Created new thread with ID: {thread_id}")

        # 2. Run the assistant
        runs_url = f"{threads_url}/{thread_id}/runs"
        run_payload = {"assistant_id": assistant_id}
        run_response = api_request("post", runs_url, headers=HEADERS, json=run_payload)
        if run_response.status_code != 200:
            return handle_api_error(run_response, "run creation")
        run = run_response.json()
        run_id = run["id"]
        print(f"Started run with ID: {run_id}")

        # 3. Poll for completion
        while run.get("status") not in ["completed", "failed"]:
            time.sleep(2)
            run_status_url = f"{runs_url}/{run_id}"
            run_status_response = api_request("get", run_status_url, headers=HEADERS)
            if run_status_response.status_code != 200:
                return handle_api_error(run_status_response, "run status check")
            run = run_status_response.json()
            print(f"Current run status: {run.get('status')}")

        if run.get("status") == "failed":
            print(f"Run failed: {run.get('last_error')}")
            return

        # 4. Retrieve messages
        list_messages_url = f"{threads_url}/{thread_id}/messages"
        messages_response = api_request("get", list_messages_url, headers=HEADERS)
        if messages_response.status_code != 200:
            return handle_api_error(messages_response, "retrieving messages")

        messages_data = messages_response.json().get("data", [])
        assistant_message = next(
            (m for m in messages_data if m["role"] == "assistant"), None
        )
        if not assistant_message:
            print("Error: No assistant response found in the thread.")
            return

        assistant_response_content = assistant_message.get("content", [])[0]
        assistant_response = assistant_response_content.get("text", {}).get("value")
        print(f"Assistant response received:\n{assistant_response}")

        # 5. Extract and parse JSON
        json_str = assistant_response.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:-3].strip()

        parsed_json = json.loads(json_str)
        print("Successfully parsed JSON.")

        # Overwrite created_at with the current UTC timestamp for accuracy
        parsed_json["created_at"] = datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M"
        )
        print(f"Set created_at to: {parsed_json['created_at']}")
        
        # Apply timezone conversions
        parsed_json = process_task_with_timezones(parsed_json, assigner)
        print(
            f"Applied timezone conversions for assignee: {parsed_json.get('assignee')}"
        )

        return parsed_json

    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON from assistant response. {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise


def format_task_for_confirmation(parsed_json):
    """
    Formats the parsed JSON into a human-readable format for user confirmation.
    """
    lines = []
    
    # Task description
    lines.append(f"📋 Task: {parsed_json.get('task', 'N/A')}")
    
    # Assignee
    lines.append(f"👤 Assigned to: {parsed_json.get('assignee', 'N/A')}")
    
    # Get timezone info
    tz_info = parsed_json.get("timezone_info", {})
    assignee = parsed_json.get("assignee", "N/A")
    
    # Due date and time
    due_date = parsed_json.get("due_date", "N/A")
    due_time = parsed_json.get("due_time")
    if due_time:
        lines.append(f"📅 Due by: {due_date} at {due_time} ({assignee}'s local time)")
    else:
        lines.append(f"📅 Due by: {due_date}")
    
    # Reminder date and time
    reminder_date = parsed_json.get("reminder_date")
    reminder_time = parsed_json.get("reminder_time")
    if reminder_date and reminder_time:
        lines.append(
            f"⏰ Reminder set for: {reminder_date} at {reminder_time} ({assignee}'s local time)"
        )
    elif reminder_date:
        lines.append(f"⏰ Reminder set for: {reminder_date}")
    
    # Site (if present)
    site = parsed_json.get("site")
    if site:
        lines.append(f"📍 Site: {site}")
    
    # Repeat interval (if present)
    repeat_interval = parsed_json.get("repeat_interval")
    if repeat_interval:
        lines.append(f"🔄 Repeats: {repeat_interval}")
    
    return "\n".join(lines)


def send_to_google_sheets(parsed_json):
    """
    Sends the parsed JSON to Google Apps Script.
    """
    try:
        response = requests.post(GOOGLE_APPS_SCRIPT_URL, json=parsed_json)
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print("Task successfully sent to Google Sheets.")
                return True
            else:
                print(f"Google Apps Script error: {result.get('message')}")
                return False
        else:
            print(
                f"Failed to send to Google Sheets. Status code: {response.status_code}"
            )
            return False
    except Exception as e:
        print(f"Error sending to Google Sheets: {e}")
        return False


if __name__ == "__main__":
    # Demo/test the simplified version
    test_inputs = [
        "Remind Joel tomorrow at 8am to check the solar battery charge.",
        "At 4pm CST tomorrow, remind Joel to check the oil levels",
        "Bryan needs to update the firewall tomorrow morning. User clarification: make it 10am instead of morning"
    ]
    
    assistant = get_or_create_assistant()
    
    for test_input in test_inputs:
        print("\n" + "=" * 60)
        print(f"Testing: {test_input}")
        print("=" * 60)
        
        try:
            result = parse_task(assistant, test_input)
            print("\nParsed result:")
            print(json.dumps(result, indent=2))
            print("\nFormatted:")
            print(format_task_for_confirmation(result))
        except Exception as e:
            print(f"Error: {e}")