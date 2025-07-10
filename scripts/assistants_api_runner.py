import json
import requests
import os
import sys
import time
import logging
from dotenv import load_dotenv
from datetime import datetime, timezone

# --- Configuration ---
load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY not found in .env file or environment.")
    sys.exit(1)

GOOGLE_APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzZZkhc3f9nP4IcllbuH24c22D-nlsWrlOEAWc0sr-VNxuiWKLKhsx96W1-6koShzsxTg/exec"
ASSISTANT_NAME = "Task Parser"
ASSISTANT_MODEL = "gpt-4-turbo-preview"
SYSTEM_PROMPT_FILE = os.path.join(
    os.path.dirname(__file__), "..", "prompts", "system_prompt.txt"
)
FEW_SHOT_EXAMPLES_FILE = os.path.join(
    os.path.dirname(__file__), "..", "prompts", "few_shot_examples.txt"
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
def log_interaction(message):
    """Appends a message to the log file with a timestamp."""
    with open(LOG_FILE, "a") as f:
        f.write(f"--- {datetime.now().isoformat()} ---\n{message}\n\n")


def handle_api_error(response, context=""):
    """Helper function to log and print API errors."""
    error_message = (
        f"Error: API request failed for {context} with status {response.status_code}."
    )
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
    Retrieves an existing assistant or creates a new one, managing files and vector stores.
    """
    # 1. Upload knowledge file
    files_url = f"{OPENAI_API_BASE_URL}/files"
    try:
        with open(FEW_SHOT_EXAMPLES_FILE, "rb") as f:
            files = {
                "file": (
                    os.path.basename(FEW_SHOT_EXAMPLES_FILE),
                    f,
                    "application/octet-stream",
                )
            }
            params = {"purpose": "assistants"}
            upload_headers = {k: v for k, v in HEADERS.items() if k != "Content-Type"}
            response = api_request(
                "post", files_url, headers=upload_headers, files=files, data=params
            )
            if response.status_code != 200:
                return handle_api_error(response, "file upload")
            knowledge_file = response.json()
            file_id = knowledge_file["id"]
            print(f"Uploaded knowledge file with ID: {file_id}")
    except Exception as e:
        print(f"Error uploading knowledge file: {e}")
        sys.exit(1)

    # 2. Create a Vector Store
    vector_stores_url = f"{OPENAI_API_BASE_URL}/vector_stores"
    vs_payload = {"name": "Task Parsing Examples"}
    vs_response = api_request(
        "post", vector_stores_url, headers=HEADERS, json=vs_payload
    )
    if vs_response.status_code != 200:
        return handle_api_error(vs_response, "vector store creation")
    vector_store = vs_response.json()
    vector_store_id = vector_store["id"]
    print(f"Created vector store with ID: {vector_store_id}")

    # 3. Add file to Vector Store
    vs_files_url = f"{vector_stores_url}/{vector_store_id}/files"
    vs_file_payload = {"file_id": file_id}
    vs_file_response = api_request(
        "post", vs_files_url, headers=HEADERS, json=vs_file_payload
    )
    if vs_file_response.status_code != 200:
        return handle_api_error(vs_file_response, "adding file to vector store")
    print(f"Added file {file_id} to vector store {vector_store_id}")

    # 4. Check for existing assistant
    assistants_url = f"{OPENAI_API_BASE_URL}/assistants"
    response = api_request(
        "get", assistants_url, headers=HEADERS, params={"limit": 100}
    )
    if response.status_code == 200:
        assistants = response.json().get("data", [])
        for assistant in assistants:
            if assistant.get("name") == ASSISTANT_NAME:
                print(f"Found existing assistant with ID: {assistant['id']}")
                update_url = f"{OPENAI_API_BASE_URL}/assistants/{assistant['id']}"
                update_payload = {
                    "tool_resources": {
                        "file_search": {"vector_store_ids": [vector_store_id]}
                    }
                }
                update_response = api_request(
                    "post", update_url, headers=HEADERS, json=update_payload
                )
                if update_response.status_code == 200:
                    print(f"Updated assistant {assistant['id']} with new vector store.")
                    return update_response.json()
                else:
                    return handle_api_error(update_response, "assistant update")

    # 5. Create a new assistant
    print(f"No existing assistant named '{ASSISTANT_NAME}'. Creating a new one.")
    try:
        with open(SYSTEM_PROMPT_FILE, "r") as f:
            system_prompt = f.read()

        payload = {
            "name": ASSISTANT_NAME,
            "instructions": system_prompt,
            "model": ASSISTANT_MODEL,
            "tools": [{"type": "file_search"}],
            "tool_resources": {"file_search": {"vector_store_ids": [vector_store_id]}},
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


def parse_and_send(assistant, input_text):
    """
    Uses the assistant to parse input text via direct HTTP calls.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"parse_and_send called with input: {input_text}")
    
    # Inject current date into the prompt
    today_str = datetime.now().strftime("%Y-%m-%d")
    prompt_with_date = f"(Today's date is {today_str}) {input_text}"
    print(f"\nProcessing input: '{prompt_with_date}'")

    assistant_id = assistant["id"]
    vector_store_id = (
        assistant.get("tool_resources", {})
        .get("file_search", {})
        .get("vector_store_ids", [None])[0]
    )
    if not vector_store_id:
        print("Error: Assistant is not configured with a vector store.")
        return

    try:
        # 1. Create a thread
        threads_url = f"{OPENAI_API_BASE_URL}/threads"
        thread_payload = {
            "messages": [{"role": "user", "content": prompt_with_date}],
            "tool_resources": {"file_search": {"vector_store_ids": [vector_store_id]}},
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

        # 6. POST to Google Apps Script
        print(f"Sending JSON to Google Apps Script URL: {GOOGLE_APPS_SCRIPT_URL}")
        gs_headers = {"Content-Type": "application/json"}
        log_interaction(
            f"Request: POST {GOOGLE_APPS_SCRIPT_URL}\nPayload: {json.dumps(parsed_json, indent=2)}"
        )
        response = requests.post(
            GOOGLE_APPS_SCRIPT_URL, json=parsed_json, headers=gs_headers
        )
        log_interaction(f"Response: {response.status_code}\nBody: {response.text}")
        response.raise_for_status()
        print(
            f"Successfully sent data. Response from Google Apps Script ({response.status_code}):"
        )
        print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"Error sending data to Google Apps Script: {e}")
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON from assistant response. {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def main():
    """Provides a command-line interface for the script."""
    task_parser_assistant = get_or_create_assistant()
    if task_parser_assistant:
        if len(sys.argv) > 1:
            user_input = " ".join(sys.argv[1:])
            parse_and_send(task_parser_assistant, user_input)
        else:
            print("\nNo input provided. Running with a default test case.")
            default_input = (
                "Remind Joel tomorrow at 8am to check the solar battery charge."
            )
            parse_and_send(task_parser_assistant, default_input)


if __name__ == "__main__":
    main()
