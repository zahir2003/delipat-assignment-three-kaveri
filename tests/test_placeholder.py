from pathlib import Path

from src.schedule_importer import parse_xer, validate_schedule


PROJECT_ROOT = Path(__file__).resolve().parents[1]
XER_FILE = PROJECT_ROOT / "data" / "raw" / "SCP2_schedule.xer"


def test_xer_parses_expected_structure() -> None:
    schedule = parse_xer(XER_FILE)

    assert schedule.project is not None
    assert schedule.project.proj_short_name == "SCP2"

    assert len(schedule.calendars) == 1
    assert len(schedule.wbs) == 11
    assert len(schedule.tasks) == 12
    assert len(schedule.dependencies) == 13


def test_milestones_are_preserved() -> None:
    schedule = parse_xer(XER_FILE)

    milestones = [
        task for task in schedule.tasks
        if task.task_type == "TT_FinMile"
    ]

    assert len(milestones) == 2

    milestone_codes = {
        task.task_code for task in milestones
    }

    assert milestone_codes == {"A1010", "A4010"}


def test_commissioning_milestone_is_not_started() -> None:
    schedule = parse_xer(XER_FILE)

    milestone = next(
        task for task in schedule.tasks
        if task.task_code == "A4010"
    )

    assert milestone.status_code == "TK_NotStart"
    assert milestone.physical_complete_pct == 0
    assert milestone.target_start_date == "2026-11-07 08:00"
    assert milestone.target_end_date == "2026-11-07 16:00"


def test_dependency_lags_are_preserved() -> None:
    schedule = parse_xer(XER_FILE)

    dependency = next(
        item
        for item in schedule.dependencies
        if item.task_id == "1070"
        and item.pred_task_id == "1060"
    )

    assert dependency.pred_type == "PR_SS"
    assert dependency.lag_hours == 360


def test_schedule_validation_has_no_errors() -> None:
    schedule = parse_xer(XER_FILE)

    errors = validate_schedule(schedule)

    assert errors == []

def test_source_keys_are_deterministic() -> None:
    schedule_one = parse_xer(XER_FILE)
    schedule_two = parse_xer(XER_FILE)

    from src.schedule_importer import build_source_keys

    keys_one = build_source_keys(schedule_one)
    keys_two = build_source_keys(schedule_two)

    assert keys_one == keys_two

    assert len(keys_one["project"]) == 1
    assert len(keys_one["wbs"]) == 11
    assert len(keys_one["tasks"]) == 12
    assert len(keys_one["dependencies"]) == 13

    assert keys_one["project"][0] == "xer:project:10"
    assert "xer:task:1010" in keys_one["tasks"]
    assert "xer:dependency:5012" in keys_one["dependencies"]