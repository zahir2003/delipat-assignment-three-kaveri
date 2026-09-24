"""Idempotent XER schedule importer for ClickUp.

Current implementation:
- imports WBS nodes
- imports activities
- imports milestones
- preserves XER dates and durations
- uses deterministic source keys for idempotency
- applies XER activity -> WBS parent relationships

Dependencies are handled separately after task import.
"""

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

    parsed = datetime.strptime(
        value,
        "%Y-%m-%d %H:%M",
    )

    parsed = parsed.replace(
        tzinfo=timezone.utc,
    )

    return int(parsed.timestamp() * 1000)


def find_existing_task(
    tasks: list[dict],
    source_key: str,
) -> dict | None:
    """Find an existing ClickUp task by deterministic source key."""

    for task in tasks:
        description = task.get("description") or ""

        if source_key in description:
            return task

    return None


def build_wbs_description(wbs) -> str:
    """Build a traceable ClickUp description for a WBS node."""

    source_key = f"xer:wbs:{wbs.wbs_id}"

    return (
        "Source: Primavera P6 XER\n"
        f"Source Key: {source_key}\n"
        f"XER WBS ID: {wbs.wbs_id}\n"
        f"Project ID: {wbs.proj_id}\n"
        f"Parent WBS ID: {wbs.parent_wbs_id or 'None'}"
    )


def build_task_description(task) -> str:
    """Build a traceable ClickUp description for an XER task."""

    source_key = f"xer:task:{task.task_id}"

    actual_start = task.actual_start_date or "Not stated"
    actual_end = task.actual_end_date or "Not stated"

    return (
        "Source: Primavera P6 XER\n"
        f"Source Key: {source_key}\n"
        f"XER Task ID: {task.task_id}\n"
        f"XER Task Code: {task.task_code}\n"
        f"WBS ID: {task.wbs_id}\n"
        f"Task Type: {task.task_type}\n"
        f"Status Code: {task.status_code}\n"
        f"Target Duration: {task.target_duration_hours} hours\n"
        f"Target Start: {task.target_start_date}\n"
        f"Target End: {task.target_end_date}\n"
        f"Actual Start: {actual_start}\n"
        f"Actual End: {actual_end}\n"
        f"Physical Completion: {task.physical_complete_pct}%"
    )


def import_wbs(
    client: ClickUpClient,
    schedule,
    existing_tasks: list[dict],
) -> tuple[int, int]:
    """Import WBS nodes."""

    created_count = 0
    existing_count = 0

    for wbs in schedule.wbs:
        source_key = f"xer:wbs:{wbs.wbs_id}"

        existing = find_existing_task(
            existing_tasks,
            source_key,
        )

        if existing:
            existing_count += 1

            print(
                f"EXISTS | WBS {wbs.wbs_id} | "
                f"{wbs.wbs_name} | "
                f"ClickUp ID: {existing.get('id')}"
            )

            continue

        created = client.create_task(
            list_id=LIST_ID,
            name=f"WBS — {wbs.wbs_name}",
            description=build_wbs_description(wbs),
        )

        created_count += 1
        existing_tasks.append(created)

        print(
            f"CREATED | WBS {wbs.wbs_id} | "
            f"{wbs.wbs_name} | "
            f"ClickUp ID: {created.get('id')}"
        )

    return created_count, existing_count


def import_tasks(
    client: ClickUpClient,
    schedule,
    existing_tasks: list[dict],
) -> tuple[int, int]:
    """Import XER activities and milestones."""

    created_count = 0
    existing_count = 0

    for task in schedule.tasks:
        source_key = f"xer:task:{task.task_id}"

        existing = find_existing_task(
            existing_tasks,
            source_key,
        )

        if existing:
            existing_count += 1

            task_kind = (
                "MILESTONE"
                if task.task_type in {"TT_FinMile", "TT_Mile"}
                else "ACTIVITY"
            )

            print(
                f"EXISTS | {task_kind} {task.task_code} | "
                f"{task.task_name} | "
                f"ClickUp ID: {existing.get('id')}"
            )

            continue

        start_date = to_epoch_ms(
            task.target_start_date,
        )

        due_date = to_epoch_ms(
            task.target_end_date,
        )

        time_estimate = int(
            task.target_duration_hours
            * 60
            * 60
            * 1000
        )

        task_kind = (
            "MILESTONE"
            if task.task_type in {"TT_FinMile", "TT_Mile"}
            else "ACTIVITY"
        )

        created = client.create_task(
            list_id=LIST_ID,
            name=f"{task.task_code} — {task.task_name}",
            description=build_task_description(task),
            start_date=start_date,
            due_date=due_date,
            time_estimate=time_estimate,
        )

        created_count += 1
        existing_tasks.append(created)

        print(
            f"CREATED | {task_kind} {task.task_code} | "
            f"{task.task_name} | "
            f"ClickUp ID: {created.get('id')}"
        )

    return created_count, existing_count


def apply_wbs_parents(
    client: ClickUpClient,
    schedule,
    existing_tasks: list[dict],
) -> tuple[int, int]:
    """Apply XER activity -> WBS parent relationships in ClickUp."""

    wbs_clickup_ids: dict[str, str] = {}
    task_clickup_ids: dict[str, str] = {}

    for task in existing_tasks:
        description = task.get("description") or ""
        task_id = task.get("id")

        if not task_id:
            continue

        for wbs in schedule.wbs:
            if f"xer:wbs:{wbs.wbs_id}" in description:
                wbs_clickup_ids[wbs.wbs_id] = task_id
                break

        for xer_task in schedule.tasks:
            if f"xer:task:{xer_task.task_id}" in description:
                task_clickup_ids[xer_task.task_id] = task_id
                break

    updated_count = 0
    skipped_count = 0

    for task in schedule.tasks:
        child_clickup_id = task_clickup_ids.get(task.task_id)
        parent_clickup_id = wbs_clickup_ids.get(task.wbs_id)

        if not child_clickup_id:
            print(
                f"SKIP | {task.task_code} | "
                "ClickUp task not found"
            )
            skipped_count += 1
            continue

        if not parent_clickup_id:
            print(
                f"SKIP | {task.task_code} | "
                f"WBS {task.wbs_id} ClickUp task not found"
            )
            skipped_count += 1
            continue

        client.update_task_parent(
            task_id=child_clickup_id,
            parent=parent_clickup_id,
        )

        updated_count += 1

        print(
            f"PARENT SET | {task.task_code} | "
            f"WBS {task.wbs_id} | "
            f"Parent ClickUp ID: {parent_clickup_id}"
        )

    return updated_count, skipped_count


def main() -> None:
    load_dotenv()

    if not os.getenv("CLICKUP_API_TOKEN"):
        raise ValueError(
            "CLICKUP_API_TOKEN is not configured"
        )

    schedule = parse_xer(XER_PATH)

    print("XER schedule loaded.")
    print(f"Project: {schedule.project.proj_short_name}")
    print(f"WBS nodes: {len(schedule.wbs)}")
    print(f"Tasks: {len(schedule.tasks)}")
    print()

    client = ClickUpClient()

    existing_result = client.get_list_tasks(
        LIST_ID,
        subtasks=True,
    )
    existing_tasks = existing_result.get(
        "tasks",
        [],
    )

    wbs_created, wbs_existing = import_wbs(
        client,
        schedule,
        existing_tasks,
    )

    print()

    task_created, task_existing = import_tasks(
        client,
        schedule,
        existing_tasks,
    )

    print()

    parent_updated, parent_skipped = apply_wbs_parents(
        client,
        schedule,
        existing_tasks,
    )

    print()
    print("Schedule task import completed.")
    print()
    print(f"WBS created: {wbs_created}")
    print(f"WBS already existed: {wbs_existing}")
    print(f"Tasks/milestones created: {task_created}")
    print(
        f"Tasks/milestones already existed: "
        f"{task_existing}"
    )
    print(f"WBS parent relationships set: {parent_updated}")
    print(f"WBS parent relationships skipped: {parent_skipped}")
    print(
        f"Total XER tasks processed: "
        f"{len(schedule.tasks)}"
    )


if __name__ == "__main__":
    main()
