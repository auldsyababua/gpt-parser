"""Google Sheets integration."""

import os
import requests
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Apps Script code is in code.gs


def get_tasks_from_sheets(assignee: str = None) -> List[Dict[str, Any]]:
    """
    Fetch active tasks from Google Sheets.

    Args:
        assignee: Filter tasks by assignee (optional)

    Returns:
        List of task dictionaries
    """
    # TODO: Implement actual Google Sheets API integration
    # For now, return example tasks based on assignee

    example_tasks = [
        {
            "id": "task_001",
            "task": "Check generator oil at Site A",
            "assignee": "Colin",
            "assigner": "Colin",
            "due_date": "2025-07-13",
            "due_time": "16:00",
            "status": "pending",
            "site": "Site A",
            "created_at": "2025-07-12T10:00:00Z",
        },
        {
            "id": "task_002",
            "task": "Inspect coolant levels",
            "assignee": "Colin",
            "assigner": "Bryan",
            "due_date": "2025-07-12",
            "due_time": "17:00",
            "status": "pending",
            "site": "Site B",
            "created_at": "2025-07-12T09:30:00Z",
        },
        {
            "id": "task_003",
            "task": "Review maintenance logs",
            "assignee": "Joel",
            "assigner": "Colin",
            "due_date": "2025-07-12",
            "due_time": "18:00",
            "status": "pending",
            "site": "Site C",
            "created_at": "2025-07-12T08:00:00Z",
        },
        {
            "id": "task_004",
            "task": "Monitor temperature readings",
            "assignee": "Colin",
            "assigner": "Bryan",
            "due_date": "2025-07-14",
            "due_time": "09:00",
            "status": "pending",
            "site": "Site D",
            "created_at": "2025-07-12T07:00:00Z",
        },
    ]

    # Filter by assignee if provided
    if assignee:
        example_tasks = [task for task in example_tasks if task["assignee"] == assignee]

    # Only return pending/active tasks
    active_tasks = [
        task for task in example_tasks if task["status"] in ["pending", "active"]
    ]

    logger.info(f"Retrieved {len(active_tasks)} active tasks for assignee: {assignee}")
    return active_tasks


def complete_task_in_sheets(
    task_id: str, completed_by: str, completion_method: str = "telegram_button"
) -> bool:
    """
    Mark a task as complete in Google Sheets and move to archive.

    Args:
        task_id: ID of the task to complete
        completed_by: Username who completed the task
        completion_method: How the task was completed (telegram_button, manual, etc.)

    Returns:
        True if successful, False otherwise
    """
    # TODO: Implement actual Google Sheets API integration
    # This would:
    # 1. Find the task in the main tasks sheet
    # 2. Update its status to "completed"
    # 3. Add completion metadata (completed_at, completed_by, completion_method)
    # 4. Move/copy the task to the archive tab

    archive_data = {
        "task_id": task_id,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "completed_by": completed_by,
        "completion_method": completion_method,
        "status": "completed",
    }

    logger.info(
        f"Task {task_id} marked as complete by {completed_by} via {completion_method}"
    )

    # For now, return True to simulate success
    return True


def restore_task_in_sheets(task_id: str, restored_by: str) -> bool:
    """
    Restore a completed task back to active status.

    Args:
        task_id: ID of the task to restore
        restored_by: Username who restored the task

    Returns:
        True if successful, False otherwise
    """
    # TODO: Implement actual Google Sheets API integration
    # This would:
    # 1. Find the task in archive
    # 2. Update its status back to "pending"
    # 3. Remove completion metadata or add restoration metadata
    # 4. Move back to main tasks sheet if needed

    logger.info(f"Task {task_id} restored by {restored_by}")

    # For now, return True to simulate success
    return True


def send_task_to_sheets(parsed_json: Dict[str, Any]) -> bool:
    """
    Send a new task to Google Sheets.
    This is the existing function from unified.py
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
            timeout=10,
        )

        if response.status_code == 200:
            logger.info("Successfully sent task to Google Sheets")
            return True
        else:
            logger.error(
                f"Failed to send to Google Sheets: {response.status_code} - {response.text}"
            )
            return False

    except Exception as e:
        logger.error(f"Error sending to Google Sheets: {e}")
        return False
