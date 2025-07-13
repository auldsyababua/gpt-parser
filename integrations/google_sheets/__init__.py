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
    
    # Generate diverse test data - 3 tasks per day for next 2 weeks
    from datetime import timedelta
    today = datetime.now()
    
    task_templates = [
        {"task": "Check oil levels at {site}", "times": ["08:00", "14:00", "20:00"]},
        {"task": "Inspect coolant system at {site}", "times": ["09:00", "15:00", "21:00"]},
        {"task": "Monitor temperature readings at {site}", "times": ["10:00", "16:00", "22:00"]},
        {"task": "Test backup generators at {site}", "times": ["07:00", "13:00", "19:00"]},
        {"task": "Review maintenance logs for {site}", "times": ["11:00", "17:00", "23:00"]},
        {"task": "Check flare skid operation at {site}", "times": ["06:00", "12:00", "18:00"]},
        {"task": "Verify node connectivity at {site}", "times": ["08:30", "14:30", "20:30"]},
        {"task": "Inspect electrical systems at {site}", "times": ["09:30", "15:30", "21:30"]},
        {"task": "Test telemetry systems at {site}", "times": ["10:30", "16:30", "22:30"]},
        {"task": "Clean air filters at {site}", "times": ["07:30", "13:30", "19:30"]},
    ]
    
    sites = ["Site A", "Site B", "Site C", "Site D"]
    assigners = ["Colin", "Bryan", "Joel"]
    
    example_tasks = []
    task_id = 1
    
    # Generate tasks for the next 14 days
    for day_offset in range(14):
        task_date = today + timedelta(days=day_offset)
        
        # Pick 3 random task templates for this day
        import random
        daily_templates = random.sample(task_templates, 3)
        
        for idx, template in enumerate(daily_templates):
            site = sites[idx % len(sites)]
            assigner = assigners[(day_offset + idx) % len(assigners)]
            
            task = {
                "id": f"task_{task_id:03d}",
                "task": template["task"].format(site=site),
                "assignee": "Colin",  # All tasks assigned to Colin for testing
                "assigner": assigner,
                "due_date": task_date.strftime("%m/%d/%Y"),  # MM/DD/YYYY format
                "due_time": template["times"][idx % 3],
                "status": "pending",
                "site": site,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            example_tasks.append(task)
            task_id += 1
    
    # Add some tasks without dates
    example_tasks.extend([
        {
            "id": f"task_{task_id:03d}",
            "task": "Update equipment inventory",
            "assignee": "Colin",
            "assigner": "Bryan",
            "due_date": None,
            "due_time": "",
            "status": "pending",
            "site": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": f"task_{task_id + 1:03d}",
            "task": "Review contractor agreements",
            "assignee": "Colin",
            "assigner": "Joel",
            "due_date": None,
            "due_time": "",
            "status": "pending",
            "site": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    ])

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
