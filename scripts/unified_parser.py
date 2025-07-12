#!/usr/bin/env python3
"""
Unified parser that supports multiple model providers with fallback.
Primary: Local Ollama models
Fallback: OpenAI API
"""

import json
import requests
import os
import sys
import time
import logging
from dotenv import load_dotenv
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.timezone_config import get_user_timezone
from utils.timezone_converter import process_task_with_timezones
from utils.temporal_processor import TemporalProcessor

# Load environment variables
load_dotenv(override=True)

# Model configuration from .env
PRIMARY_PROVIDER = os.getenv("PRIMARY_MODEL_PROVIDER", "ollama")
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL_NAME", "llama3:8b-instruct-q4_0")
PRIMARY_TIMEOUT = int(os.getenv("PRIMARY_MODEL_TIMEOUT", "30"))

FALLBACK_PROVIDER = os.getenv("FALLBACK_MODEL_PROVIDER", "openai")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL_NAME", "gpt-4o-mini")
FALLBACK_TIMEOUT = int(os.getenv("FALLBACK_MODEL_TIMEOUT", "30"))

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "1"))

# Load prompts
SYSTEM_PROMPT_FILE = os.path.join(
    os.path.dirname(__file__), "..", "prompts", "system_prompt.txt"
)
FEW_SHOT_EXAMPLES_FILE = os.path.join(
    os.path.dirname(__file__), "..", "prompts", "few_shot_examples.txt"
)

# Set up logging
logger = logging.getLogger(__name__)


def load_prompts() -> Tuple[str, str]:
    """Load system prompt and few-shot examples."""
    try:
        with open(SYSTEM_PROMPT_FILE, "r") as f:
            system_prompt = f.read()
        with open(FEW_SHOT_EXAMPLES_FILE, "r") as f:
            few_shot_examples = f.read()
        return system_prompt, few_shot_examples
    except Exception as e:
        logger.error(f"Error loading prompt files: {e}")
        raise


def check_ollama_available() -> bool:
    """Check if Ollama is running and model is available."""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            available_models = [m["name"] for m in models]
            return PRIMARY_MODEL in available_models
    except:
        return False
    return False


def parse_with_ollama(prompt: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
    """Parse using local Ollama model."""
    if not check_ollama_available():
        logger.warning(f"Ollama model {PRIMARY_MODEL} not available")
        return None
    
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": PRIMARY_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                }
            },
            timeout=timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            assistant_response = result.get("response", "").strip()
            
            # Extract JSON from response
            if "```json" in assistant_response:
                json_str = assistant_response.split("```json")[1].split("```")[0].strip()
            else:
                json_str = assistant_response
            
            return json.loads(json_str)
        else:
            logger.error(f"Ollama API error: {response.status_code} - {response.text}")
            return None
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error from Ollama: {e}")
        return None
    except Exception as e:
        logger.error(f"Ollama parsing error: {e}")
        return None


def parse_with_openai(prompt: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
    """Parse using OpenAI API."""
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not configured")
        return None
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": FALLBACK_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a task parser. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 500,
            },
            timeout=timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            assistant_response = result["choices"][0]["message"]["content"].strip()
            
            # Extract JSON from response
            if "```json" in assistant_response:
                json_str = assistant_response.split("```json")[1].split("```")[0].strip()
            else:
                json_str = assistant_response
            
            return json.loads(json_str)
        else:
            logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
            return None
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error from OpenAI: {e}")
        return None
    except Exception as e:
        logger.error(f"OpenAI parsing error: {e}")
        return None


def parse_task(input_text: str, assigner: str = "Colin") -> Optional[Dict[str, Any]]:
    """
    Parse task using configured model with fallback.
    
    Args:
        input_text: The task description to parse
        assigner: The person assigning the task
        
    Returns:
        Parsed task JSON or None if parsing fails
    """
    logger.info(f"parse_task called with input: {input_text}")
    
    # Load prompts
    system_prompt, few_shot_examples = load_prompts()
    combined_prompt = f"{system_prompt}\n\n## Examples:\n\n{few_shot_examples}"
    
    # Get assigner's timezone and current time
    assigner_tz = get_user_timezone(assigner)
    today_in_tz = datetime.now(assigner_tz)
    today_str = today_in_tz.strftime("%Y-%m-%d")
    current_time_str = today_in_tz.strftime("%H:%M")
    
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
            f"(Context: It is currently {current_time_str} on {today_str} where {assigner} is located)",
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
        
        task_input = "\n".join(prompt_parts)
    else:
        # Low confidence - fall back to original approach
        task_input = f"(Context: It is currently {current_time_str} on {today_str} where {assigner} is located) {input_text}"
    
    # Combine system prompt with task
    full_prompt = f"{combined_prompt}\n\n{task_input}"
    
    # Try primary model
    parsed_json = None
    api_start = time.time()
    
    if PRIMARY_PROVIDER == "ollama":
        logger.info(f"Trying primary model: Ollama {PRIMARY_MODEL}")
        parsed_json = parse_with_ollama(full_prompt, PRIMARY_TIMEOUT)
    elif PRIMARY_PROVIDER == "openai":
        logger.info(f"Trying primary model: OpenAI {PRIMARY_MODEL}")
        parsed_json = parse_with_openai(full_prompt, PRIMARY_TIMEOUT)
    
    # If primary failed, try fallback
    if not parsed_json and FALLBACK_PROVIDER:
        logger.warning("Primary model failed, trying fallback")
        if FALLBACK_PROVIDER == "openai":
            parsed_json = parse_with_openai(full_prompt, FALLBACK_TIMEOUT)
        elif FALLBACK_PROVIDER == "ollama":
            parsed_json = parse_with_ollama(full_prompt, FALLBACK_TIMEOUT)
    
    api_time = time.time() - api_start
    
    if not parsed_json:
        logger.error("All models failed to parse task")
        return None
    
    # Post-process the parsed JSON
    parsed_json["created_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    
    # Apply timezone conversions
    parsed_json = process_task_with_timezones(parsed_json, assigner)
    
    # Add original prompt and performance metrics
    parsed_json["original_prompt"] = input_text
    parsed_json["corrections_history"] = ""
    parsed_json["_performance"] = {
        "total_time": time.time() - start_time,
        "preprocessing_time": preprocess_time,
        "api_time": api_time,
    }
    
    logger.info(
        f"Total parse_task time: {time.time() - start_time:.2f}s "
        f"(preprocessing: {preprocess_time:.3f}s, API: {api_time:.3f}s)"
    )
    
    return parsed_json


def format_task_for_confirmation(parsed_json: Dict[str, Any]) -> str:
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


def send_to_google_sheets(parsed_json: Dict[str, Any]) -> bool:
    """
    Sends parsed task to Google Sheets via Apps Script webhook.
    """
    webhook_url = os.getenv("GOOGLE_APPS_SCRIPT_WEB_APP_URL")
    if not webhook_url:
        logger.error("Google Apps Script webhook URL not configured")
        return False
    
    try:
        response = requests.post(
            webhook_url,
            json=parsed_json,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("Successfully sent task to Google Sheets")
            return True
        else:
            logger.error(f"Failed to send to Google Sheets: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending to Google Sheets: {e}")
        return False


if __name__ == "__main__":
    # Test the parser
    test_input = "Remind Joel at the top of the hour to check oil"
    if len(sys.argv) > 1:
        test_input = " ".join(sys.argv[1:])
    
    print(f"Testing with: {test_input}")
    print(f"Primary model: {PRIMARY_PROVIDER} - {PRIMARY_MODEL}")
    print(f"Fallback model: {FALLBACK_PROVIDER} - {FALLBACK_MODEL}")
    print()
    
    result = parse_task(test_input)
    if result:
        print("Parsed successfully:")
        print(format_task_for_confirmation(result))
        print("\nJSON:")
        print(json.dumps(result, indent=2))
    else:
        print("Failed to parse task")
