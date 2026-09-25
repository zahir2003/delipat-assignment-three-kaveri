from pathlib import Path
from decimal import Decimal
from pathlib import Path

from src.ra_bill_engine import (
    calculate_bill,
    load_boq,
    load_bill_register,
    load_cumulative,
    load_measurements,
    load_production,
)
from src.schedule_importer import parse_xer, validate_schedule


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "raw"
XER_FILE = DATA_DIR / "SCP2_schedule.xer"


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
        task
        for task in schedule.tasks
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
        task
        for task in schedule.tasks
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


def build_ra04_bill():
    boq = load_boq(
        DATA_DIR / "boq.csv"
    )

    measurements = load_measurements(
        DATA_DIR / "measurement_sheet_RA04.csv"
    )

    production = load_production(
        DATA_DIR / "production_orders_sep2026.csv"
    )

    cumulative = load_cumulative(
        DATA_DIR / "cumulative_billed_to_RA03.csv"
    )

    bill_register = load_bill_register(
        DATA_DIR / "bill_register.csv"
    )

    schedule = parse_xer(XER_FILE)

    return calculate_bill(
        boq=boq,
        measurements=measurements,
        production=production,
        cumulative=cumulative,
        bill_register=bill_register,
        schedule=schedule,
    )


def test_ra04_billable_quantities() -> None:
    bill = build_ra04_bill()

    quantities = {
        line.boq_item: line.period_billable_qty
        for line in bill.lines
    }

    assert quantities["B01"] == 0
    assert quantities["B02"] == 1500
    assert quantities["B03"] == 24
    assert quantities["B04"] == Decimal("4.9")
    assert quantities["B05"] == 700
    assert quantities["B06"] == 12
    assert quantities["B07"] == 0


def test_ra04_gross_gst_retention_and_net() -> None:
    bill = build_ra04_bill()
    totals = bill.totals

    assert totals.gross_value_inr == 3883500
    assert totals.gst_inr == 699030
    assert totals.retention_inr == 194175
    assert totals.advance_recovery_inr == 324650
    assert totals.net_payable_inr == 4063705


def test_ra04_b05_contract_cap_is_applied() -> None:
    bill = build_ra04_bill()

    b05 = next(
        line
        for line in bill.lines
        if line.boq_item == "B05"
    )

    assert b05.previously_billed_qty == 3300
    assert b05.period_certified_qty == 950
    assert b05.period_billable_qty == 700
    assert b05.variation_qty == 250

    assert any(
        "B05" in exception
        and "variation" in exception
        for exception in bill.exceptions
    )


def test_ra04_disputed_quantities_are_not_billed() -> None:
    bill = build_ra04_bill()

    b04 = next(
        line
        for line in bill.lines
        if line.boq_item == "B04"
    )

    b06 = next(
        line
        for line in bill.lines
        if line.boq_item == "B06"
    )

    assert b04.period_certified_qty == Decimal("4.9")
    assert b04.period_disputed_qty == Decimal("0.3")
    assert b04.period_billable_qty == Decimal("4.9")

    assert b06.period_certified_qty == Decimal("12")
    assert b06.period_disputed_qty == Decimal("2")
    assert b06.period_billable_qty == Decimal("12")


def test_ra04_delivery_qc_excludes_failed_production() -> None:
    bill = build_ra04_bill()

    b02 = next(
        line
        for line in bill.lines
        if line.boq_item == "B02"
    )

    b03 = next(
        line
        for line in bill.lines
        if line.boq_item == "B03"
    )

    assert b02.period_billable_qty == 1500
    assert b03.period_billable_qty == 24

    assert "failed QC" in b02.exclusion_reason
    assert "failed QC" in b03.exclusion_reason


def test_ra04_milestone_items_not_completed_are_not_billed() -> None:
    bill = build_ra04_bill()

    b01 = next(
        line
        for line in bill.lines
        if line.boq_item == "B01"
    )

    b07 = next(
        line
        for line in bill.lines
        if line.boq_item == "B07"
    )

    assert b01.period_billable_qty == 0
    assert b07.period_billable_qty == 0