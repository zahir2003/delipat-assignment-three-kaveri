"""Create one controlled ClickUp task from the parsed XER schedule."""

import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from src.clickup.client import ClickUpClient
from src.schedule_importer import parse_xer


LIST_ID = "1300410000039999"
XER_PATH = Path("data/raw/SCP2_schedule.xer")


def to_epoch_ms(value: str) -> int:
    """Convert an XER date string to Unix epoch milliseconds."""

    parsed = datetime.strptime(value, "%Y-%m-%d %H:%M")

    parsed = parsed.replace(tzinfo=timezone.utc)

    return int(parsed.timestamp() * 1000)


def main() -> None:
    load_dotenv()

    if not os.getenv("CLICKUP_API_TOKEN"):
        raise ValueError("CLICKUP_API_TOKEN is not configured")

    schedule = parse_xer(XER_PATH)

    task = next(
        item for item in schedule.tasks
        if item.task_code == "A1000"
    )

    print("XER task selected:")
    print(f"  Code: {task.task_code}")
    print(f"  Name: {task.task_name}")
    print(f"  Start: {task.target_start_date}")
    print(f"  Finish: {task.target_end_date}")
    print(f"  Duration: {task.target_duration_hours} hours")
    print(f"  Progress: {task.physical_complete_pct}%")
    print(f"  Status code: {task.status_code}")
    print(f"  Task type: {task.task_type}")
    print(f"  WBS ID: {task.wbs_id}")
    print()

    client = ClickUpClient()

    existing_result = client.get_list_tasks(LIST_ID)
    existing_tasks = existing_result.get("tasks", [])

    source_key = f"xer:task:{task.task_id}"

    for existing in existing_tasks:
        description = existing.get("description") or ""

        if source_key in description:
            print("Task already exists.")
            print(f"ClickUp Task ID: {existing.get('id')}")
            print(f"Task Name: {existing.get('name')}")
            return

    start_date = to_epoch_ms(task.target_start_date)
    due_date = to_epoch_ms(task.target_end_date)

    time_estimate = int(
        task.target_duration_hours * 60 * 60 * 1000
    )

    description = (
        "Source: Primavera P6 XER\n"
        f"Source Key: {source_key}\n"
        f"XER Task Code: {task.task_code}\n"
        f"WBS ID: {task.wbs_id}\n"
        f"Task Type: {task.task_type}\n"
        f"Status Code: {task.status_code}\n"
        f"Duration: {task.target_duration_hours} hours\n"
        f"Completion: {task.physical_complete_pct}%"
    )

    created = client.create_task(
        list_id=LIST_ID,
        name=f"{task.task_code} — {task.task_name}",
        description=description,
        start_date=start_date,
        due_date=due_date,
        time_estimate=time_estimate,
    )

    print("ClickUp task created successfully.")
    print(f"ClickUp Task ID: {created.get('id')}")
    print(f"Task Name: {created.get('name')}")
    print(f"Source Key: {source_key}")
    print(f"Start Date: {created.get('start_date')}")
    print(f"Due Date: {created.get('due_date')}")
    print(f"Time Estimate: {created.get('time_estimate')}")


if __name__ == "__main__":
    main()