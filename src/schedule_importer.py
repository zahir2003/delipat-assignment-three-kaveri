"""Primavera P6 XER schedule importer.

The parser is intentionally independent from ClickUp so that the XER data
can be validated before any API write takes place.

Supported XER sections:
- PROJECT
- CALENDAR
- PROJWBS
- TASK
- TASKPRED

The importer preserves source identifiers, dates, durations, milestones,
WBS relationships, dependency types and dependency lags.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
XER_FILE = PROJECT_ROOT / "data" / "raw" / "SCP2_schedule.xer"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "schedule_import.json"


@dataclass(frozen=True)
class Project:
    proj_id: str
    proj_short_name: str
    plan_start_date: str
    last_recalc_date: str
    clndr_id: str


@dataclass(frozen=True)
class Calendar:
    clndr_id: str
    clndr_name: str
    day_hr_cnt: float
    week_hr_cnt: float


@dataclass(frozen=True)
class WBS:
    wbs_id: str
    proj_id: str
    parent_wbs_id: str | None
    wbs_short_name: str
    wbs_name: str
    proj_node_flag: str
    seq_num: int


@dataclass(frozen=True)
class Task:
    task_id: str
    proj_id: str
    wbs_id: str
    clndr_id: str
    task_code: str
    task_name: str
    task_type: str
    status_code: str
    target_duration_hours: float
    target_start_date: str
    target_end_date: str
    actual_start_date: str | None
    actual_end_date: str | None
    physical_complete_pct: float


@dataclass(frozen=True)
class Dependency:
    task_pred_id: str
    task_id: str
    pred_task_id: str
    proj_id: str
    pred_proj_id: str
    pred_type: str
    lag_hours: float


@dataclass
class Schedule:
    project: Project | None
    calendars: list[Calendar]
    wbs: list[WBS]
    tasks: list[Task]
    dependencies: list[Dependency]


def parse_date(value: str) -> str | None:
    """Validate and normalize an XER date."""
    value = value.strip()

    if not value:
        return None

    datetime.strptime(value, "%Y-%m-%d %H:%M")

    return value


def parse_number(value: str) -> float:
    """Parse a numeric XER field."""
    return float(value.strip())


def split_xer_line(line: str) -> list[str]:
    """Split an XER record while preserving empty fields."""
    return line.rstrip("\r\n").split("\t")


def parse_xer(path: Path) -> Schedule:
    """Parse the supported XER sections into typed records."""
    if not path.exists():
        raise FileNotFoundError(f"XER file not found: {path}")

    sections: dict[str, list[str]] = {}
    current_section: str | None = None
    fields: list[str] = []

    with path.open("r", encoding="utf-8-sig") as file:
        for raw_line in file:
            line = raw_line.rstrip("\r\n")

            if not line:
                continue

            if line.startswith("ERMHDR"):
                continue

            parts = split_xer_line(line)

            if parts[0] == "%T":
                current_section = parts[1].strip()
                sections[current_section] = []
                fields = []
                continue

            if parts[0] == "%F":
                if current_section is None:
                    raise ValueError("%F encountered before %T")
                fields = [field.strip() for field in parts[1:]]
                continue

            if parts[0] == "%R":
                if current_section is None:
                    raise ValueError("%R encountered before %T")

                if not fields:
                    raise ValueError(
                        f"%R encountered without %F in {current_section}"
                    )

                values = parts[1:]

                if len(values) != len(fields):
                    raise ValueError(
                        f"{current_section}: expected {len(fields)} fields, "
                        f"received {len(values)}"
                    )

                record = dict(zip(fields, values))
                sections[current_section].append(record)
                continue

            if parts[0] == "%E":
                break

    return build_schedule(sections)


def build_schedule(sections: dict[str, list[dict[str, str]]]) -> Schedule:
    """Convert parsed XER dictionaries into typed schedule objects."""

    project_rows = sections.get("PROJECT", [])
    calendar_rows = sections.get("CALENDAR", [])
    wbs_rows = sections.get("PROJWBS", [])
    task_rows = sections.get("TASK", [])
    dependency_rows = sections.get("TASKPRED", [])

    if len(project_rows) != 1:
        raise ValueError(
            f"Expected exactly one PROJECT row, found {len(project_rows)}"
        )

    project_row = project_rows[0]

    project = Project(
        proj_id=project_row["proj_id"],
        proj_short_name=project_row["proj_short_name"],
        plan_start_date=parse_date(project_row["plan_start_date"])
        or "",
        last_recalc_date=parse_date(project_row["last_recalc_date"])
        or "",
        clndr_id=project_row["clndr_id"],
    )

    calendars = [
        Calendar(
            clndr_id=row["clndr_id"],
            clndr_name=row["clndr_name"],
            day_hr_cnt=parse_number(row["day_hr_cnt"]),
            week_hr_cnt=parse_number(row["week_hr_cnt"]),
        )
        for row in calendar_rows
    ]

    wbs = [
        WBS(
            wbs_id=row["wbs_id"],
            proj_id=row["proj_id"],
            parent_wbs_id=row["parent_wbs_id"] or None,
            wbs_short_name=row["wbs_short_name"],
            wbs_name=row["wbs_name"],
            proj_node_flag=row["proj_node_flag"],
            seq_num=int(row["seq_num"]),
        )
        for row in wbs_rows
    ]

    tasks = [
        Task(
            task_id=row["task_id"],
            proj_id=row["proj_id"],
            wbs_id=row["wbs_id"],
            clndr_id=row["clndr_id"],
            task_code=row["task_code"],
            task_name=row["task_name"],
            task_type=row["task_type"],
            status_code=row["status_code"],
            target_duration_hours=parse_number(
                row["target_drtn_hr_cnt"]
            ),
            target_start_date=parse_date(row["target_start_date"]) or "",
            target_end_date=parse_date(row["target_end_date"]) or "",
            actual_start_date=parse_date(row["act_start_date"]),
            actual_end_date=parse_date(row["act_end_date"]),
            physical_complete_pct=parse_number(
                row["phys_complete_pct"]
            ),
        )
        for row in task_rows
    ]

    dependencies = [
        Dependency(
            task_pred_id=row["task_pred_id"],
            task_id=row["task_id"],
            pred_task_id=row["pred_task_id"],
            proj_id=row["proj_id"],
            pred_proj_id=row["pred_proj_id"],
            pred_type=row["pred_type"],
            lag_hours=parse_number(row["lag_hr_cnt"]),
        )
        for row in dependency_rows
    ]

    return Schedule(
        project=project,
        calendars=calendars,
        wbs=wbs,
        tasks=tasks,
        dependencies=dependencies,
    )


def validate_schedule(schedule: Schedule) -> list[str]:
    """Return validation errors without modifying source data."""
    errors: list[str] = []

    if schedule.project is None:
        errors.append("Missing project")
        return errors

    wbs_ids = {item.wbs_id for item in schedule.wbs}
    task_ids = {item.task_id for item in schedule.tasks}
    task_codes = [item.task_code for item in schedule.tasks]

    if len(task_codes) != len(set(task_codes)):
        errors.append("Duplicate task_code detected")

    for item in schedule.wbs:
        if item.parent_wbs_id and item.parent_wbs_id not in wbs_ids:
            errors.append(
                f"WBS {item.wbs_id} references missing parent "
                f"{item.parent_wbs_id}"
            )

    for task in schedule.tasks:
        if task.wbs_id not in wbs_ids:
            errors.append(
                f"Task {task.task_code} references missing WBS "
                f"{task.wbs_id}"
            )

        if not 0 <= task.physical_complete_pct <= 100:
            errors.append(
                f"Task {task.task_code} has invalid completion percentage"
            )

    dependency_ids: set[str] = set()

    for dependency in schedule.dependencies:
        if dependency.task_id not in task_ids:
            errors.append(
                f"Dependency {dependency.task_pred_id} references missing "
                f"successor task {dependency.task_id}"
            )

        if dependency.pred_task_id not in task_ids:
            errors.append(
                f"Dependency {dependency.task_pred_id} references missing "
                f"predecessor task {dependency.pred_task_id}"
            )

        if dependency.task_pred_id in dependency_ids:
            errors.append(
                f"Duplicate dependency ID {dependency.task_pred_id}"
            )

        dependency_ids.add(dependency.task_pred_id)

    return errors


def build_source_keys(schedule: Schedule) -> dict[str, list[str]]:
    """Build deterministic source keys for idempotent ClickUp imports.

    The same XER source identifiers always produce the same keys.
    """
    if schedule.project is None:
        raise ValueError("Cannot build source keys without a project")

    return {
        "project": [
            f"xer:project:{schedule.project.proj_id}"
        ],
        "wbs": [
            f"xer:wbs:{item.wbs_id}"
            for item in schedule.wbs
        ],
        "tasks": [
            f"xer:task:{item.task_id}"
            for item in schedule.tasks
        ],
        "dependencies": [
            f"xer:dependency:{item.task_pred_id}"
            for item in schedule.dependencies
        ],
    }

def schedule_to_dict(schedule: Schedule) -> dict[str, Any]:
    """Serialize the parsed schedule."""
    return {
        "project": asdict(schedule.project)
        if schedule.project
        else None,
        "calendars": [asdict(item) for item in schedule.calendars],
        "wbs": [asdict(item) for item in schedule.wbs],
        "tasks": [asdict(item) for item in schedule.tasks],
        "dependencies": [
            asdict(item)
            for item in schedule.dependencies
        ],
        "source_keys": build_source_keys(schedule),
    }



def main() -> None:
    """Parse, validate and save the schedule locally."""
    schedule = parse_xer(XER_FILE)
    errors = validate_schedule(schedule)

    if errors:
        print("Schedule validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    result = schedule_to_dict(schedule)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    print("Schedule import validation successful.")
    print(f"Project: {schedule.project.proj_short_name}")
    print(f"Calendars: {len(schedule.calendars)}")
    print(f"WBS rows: {len(schedule.wbs)}")
    print(f"Tasks: {len(schedule.tasks)}")
    print(
        f"Milestones: "
        f"{sum(task.task_type == 'TT_FinMile' for task in schedule.tasks)}"
    )
    print(f"Dependencies: {len(schedule.dependencies)}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()