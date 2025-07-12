import json
import requests
import os
import sys
import time
import logging
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.timezone_config import get_user_timezone
from utils.timezone_converter import process_task_with_timezones
from utils.temporal_processor import TemporalProcessor

# --- Configuration ---
OLLAMA_BASE_URL = "http://localhost:11434/api/chat"
GOOGLE_APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzZZkhc3f9nP4IcllbuH24c22D-nlsWrlOEAWc0sr-VNxuiWKLKhsx96W1-6koShzsxTg/exec"

# Model variants
MODEL_VARIANTS = {
    "fp16": "llama3:8b-instruct-fp16",
    "q8": "llama3:8b-instruct-q8_0",
    "q4": "llama3:8b-instruct-q4_0",
}

# Default model (can be overridden)
DEFAULT_MODEL = "q4"

SYSTEM_PROMPT_FILE = os.path.join(
    os.path.dirname(__file__), "..", "prompts", "system_prompt.txt"
)
FEW_SHOT_EXAMPLES_FILE = os.path.join(
    os.path.dirname(__file__), "..", "prompts", "few_shot_examples.txt"
)
LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "local_llama_log.txt")

# --- Logging ---
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def log_interaction(message):
    """Appends a message to the log file with a timestamp."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"--- {datetime.now().isoformat()} ---\n{message}\n\n")


def api_request(method, url, **kwargs):
    """Wrapper for requests to log the interaction."""
    log_interaction(
        f"Request: {method.upper()} {url}\nHeaders: {kwargs.get('headers')}\nPayload: {kwargs.get('json')}"
    )
    response = requests.request(method, url, **kwargs)
    log_interaction(f"Response: {response.status_code}\nBody: {response.text}")
    return response


def load_prompts():
    """Load and combine system prompt and few-shot examples."""
    try:
        with open(SYSTEM_PROMPT_FILE, "r") as f:
            system_prompt = f.read()

        with open(FEW_SHOT_EXAMPLES_FILE, "r") as f:
            few_shot_examples = f.read()

        # Combine prompts with clear separation
        combined_prompt = f"{system_prompt}\n\n## Examples:\n\n{few_shot_examples}"
        return combined_prompt

    except Exception as e:
        print(f"Error loading prompt files: {e}")
        sys.exit(1)


def check_model_available(model_name):
    """Check if a model is available in Ollama."""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            available_models = [m["name"] for m in models]
            return model_name in available_models
    except:
        return False
    return False


def parse_task(input_text, assigner="Colin", model_variant=None):
    """
    Uses local Ollama Llama3 model to parse input text and returns the parsed JSON.

    Args:
        input_text: The natural language task description
        assigner: The person assigning the task (default: Colin)
        model_variant: Which model variant to use (fp16, q8, q4). Default: q4
    """
    logger.info(f"parse_task called with input: {input_text}")

    # Select model
    if model_variant is None:
        model_variant = DEFAULT_MODEL

    if model_variant not in MODEL_VARIANTS:
        print(
            f"Error: Invalid model variant '{model_variant}'. Options: {list(MODEL_VARIANTS.keys())}"
        )
        return None

    model_name = MODEL_VARIANTS[model_variant]

    # Check if model is available
    if not check_model_available(model_name):
        print(
            f"Error: Model '{model_name}' is not available. Please run: ollama pull {model_name}"
        )
        return None

    print(f"Using model: {model_name}")

    # Get assigner's timezone
    assigner_tz = get_user_timezone(assigner)
    today_in_tz = datetime.now(assigner_tz)
    today_str = today_in_tz.strftime("%Y-%m-%d")
    tz_abbr = today_in_tz.strftime("%Z")

    # Pre-process temporal expressions
    processor = TemporalProcessor(default_timezone=str(assigner_tz))
    start_time = time.time()
    preprocessed = processor.preprocess(input_text, reference_time=today_in_tz)
    preprocess_time = time.time() - start_time

    logger.info(
        f"Preprocessing took {preprocess_time:.3f}s, confidence: {preprocessed['confidence']}"
    )

    # Build prompt based on preprocessing results
    if preprocessed["confidence"] >= 0.7 and preprocessed["temporal_data"]:
        # High confidence - send structured data
        temporal_info = preprocessed["temporal_data"]
        prompt_parts = [
            f"(Today's date is {today_str} in {assigner}'s timezone: {tz_abbr})",
            f"Task: {preprocessed['processed_text']}",
        ]

        # Add pre-parsed temporal data
        if "due_date" in temporal_info:
            prompt_parts.append(f"Pre-parsed due date: {temporal_info['due_date']}")
        if "due_time" in temporal_info:
            prompt_parts.append(f"Pre-parsed due time: {temporal_info['due_time']}")
        if "reminder_time" in temporal_info and temporal_info.get(
            "reminder_time"
        ) != temporal_info.get("due_time"):
            prompt_parts.append(
                f"Pre-parsed reminder time: {temporal_info['reminder_time']}"
            )
        if "timezone_context" in temporal_info:
            prompt_parts.append(
                f"Detected timezone: {temporal_info['timezone_context']}"
            )

        prompt_with_date = "\n".join(prompt_parts)
        print(f"\nHigh-confidence preprocessing ({preprocessed['confidence']:.1%})")
    else:
        # Low confidence - fall back to original approach
        prompt_with_date = f"(Today's date is {today_str} in {assigner}'s timezone: {tz_abbr}) {input_text}"
        print(f"\nLow-confidence preprocessing, using original approach")

    print(f"Processing input: '{prompt_with_date}'")

    # Load combined prompt
    system_prompt = load_prompts()

    try:
        # Build chat completion request
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_with_date},
            ],
            "stream": False,
            "options": {"temperature": 0, "num_predict": 1000},
        }

        # Make API request
        api_start_time = time.time()
        response = api_request("post", OLLAMA_BASE_URL, json=payload)
        api_duration = time.time() - api_start_time

        if response.status_code != 200:
            print(f"Error: API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None

        # Parse response
        response_data = response.json()
        assistant_response = response_data["message"]["content"]
        print(f"Assistant response received (in {api_duration:.2f}s)")

        # Parse JSON from response
        # Extract JSON if wrapped in text
        json_str = assistant_response
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "{" in json_str:
            # Find the JSON object in the response
            start = json_str.find("{")
            end = json_str.rfind("}") + 1
            if start != -1 and end > start:
                json_str = json_str[start:end]

        # Remove JSON comments (// style) that Llama sometimes adds
        import re

        json_str = re.sub(r"//.*$", "", json_str, flags=re.MULTILINE)

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

        # Add original prompt (without the date injection)
        parsed_json["original_prompt"] = input_text

        # Initialize corrections_history as empty
        if "corrections_history" not in parsed_json:
            parsed_json["corrections_history"] = ""

        # Add preprocessing metadata if high confidence was used
        if preprocessed["confidence"] >= 0.7:
            parsed_json["_preprocessing"] = {
                "used": True,
                "confidence": preprocessed["confidence"],
                "time_saved": preprocess_time,
            }

        # Add performance metrics
        parsed_json["_performance"] = {
            "model": model_name,
            "model_variant": model_variant,
            "preprocessing_time": round(preprocess_time, 3),
            "api_time": round(api_duration, 3),
            "total_time": round(time.time() - start_time, 3),
        }

        # Log total processing time
        total_time = time.time() - start_time
        logger.info(
            f"Total parse_task time: {total_time:.2f}s (preprocessing: {preprocess_time:.3f}s, API: {api_duration:.3f}s)"
        )
        print(
            f"\n⏱️  Performance: Model={model_name}, Total={total_time:.2f}s "
            f"(preprocessing={preprocess_time:.3f}s, API={api_duration:.3f}s)"
        )

        return parsed_json

    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON from assistant response. {e}")
        print(f"Response was: {assistant_response}")
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
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending data to Google Apps Script: {e}")
        return False


def main():
    """Provides a command-line interface for the script."""
    # Check for model variant argument
    model_variant = None
    args = sys.argv[1:]

    # Check if --model flag is used
    if "--model" in args:
        model_idx = args.index("--model")
        if model_idx + 1 < len(args):
            model_variant = args[model_idx + 1]
            # Remove the flag and value from args
            args = args[:model_idx] + args[model_idx + 2 :]

    if args:
        user_input = " ".join(args)
        parsed_json = parse_task(user_input, model_variant=model_variant)
        if parsed_json:
            print("\nFormatted task:")
            print(format_task_for_confirmation(parsed_json))
            print("\nJSON output:")
            print(json.dumps(parsed_json, indent=2))
    else:
        print("\nNo input provided. Running with a default test case.")
        default_input = "Remind Joel tomorrow at 8am to check the solar battery charge."
        parsed_json = parse_task(default_input, model_variant=model_variant)
        if parsed_json:
            print("\nFormatted task:")
            print(format_task_for_confirmation(parsed_json))
            print("\nJSON output:")
            print(json.dumps(parsed_json, indent=2))


if __name__ == "__main__":
    main()
