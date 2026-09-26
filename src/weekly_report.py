from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.approval_router import (
    load_approval_matrix,
    load_purchase_requests,
    route_requests,
)
from src.cashflow_forecaster import (
    build_activity_map,
    build_forecast_lines,
    build_existing_cash_receipts,
    forecast_cashflow,
    load_boq as load_cashflow_boq,
    load_cumulative_billed,
    load_paid_or_due_bill_payments,
)
from src.ra_bill_engine import (
    calculate_bill,
    load_bill_register,
    load_boq,
    load_cumulative,
    load_measurements,
    load_production,
)
from src.schedule_importer import parse_xer, validate_schedule

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"


@dataclass(frozen=True)
class WeeklyReport:
    reporting_date: str
    project: str
    schedule_status: str
    progress_pct: float
    completed_tasks: int
    total_tasks: int
    completed_milestones: int
    total_milestones: int
    ra04_gross: Decimal
    ra04_net: Decimal
    ra04_advance_recovery: Decimal
    disputed_value: Decimal
    purchase_request_count: int
    escalated_request_count: int
    anti_splitting_count: int
    cash_oct: Decimal
    cash_nov: Decimal
    cash_dec: Decimal
    key_exceptions: tuple[str, ...]


def load_schedule_report():
    schedule = parse_xer(RAW / "SCP2_schedule.xer")
    errors = validate_schedule(schedule)
    return schedule, errors


def calculate_progress(schedule) -> tuple[float, int, int, int, int]:
    tasks = schedule.tasks

    activity_tasks = [
        task for task in tasks if task.task_type not in {"TT_Mile", "TT_WBS"}
    ]

    milestones = [task for task in tasks if task.task_type in {"TT_Mile", "TT_FinMile"}]

    completed_tasks = sum(
        1
        for task in activity_tasks
        if task.actual_end_date is not None or task.physical_complete_pct >= 100
    )

    completed_milestones = sum(
        1
        for task in milestones
        if task.actual_end_date is not None or task.physical_complete_pct >= 100
    )

    if activity_tasks:
        progress_pct = sum(task.physical_complete_pct for task in activity_tasks) / len(
            activity_tasks
        )
    else:
        progress_pct = 0.0

    return (
        progress_pct,
        completed_tasks,
        len(activity_tasks),
        completed_milestones,
        len(milestones),
    )


def calculate_ra04():
    boq = load_boq(RAW / "boq.csv")
    measurements = load_measurements(RAW / "measurement_sheet_RA04.csv")
    production = load_production(RAW / "production_orders_sep2026.csv")
    cumulative = load_cumulative(RAW / "cumulative_billed_to_RA03.csv")
    bill_register = load_bill_register(RAW / "bill_register.csv")

    schedule = parse_xer(RAW / "SCP2_schedule.xer")

    return calculate_bill(
        boq,
        measurements,
        production,
        cumulative,
        bill_register,
        schedule,
        "2026-09",
    )


def calculate_approvals():
    levels = load_approval_matrix(RAW / "approval_matrix.csv")
    requests = load_purchase_requests(RAW / "purchase_requests_sep2026.csv")

    return route_requests(levels, requests)


def calculate_cashflow():
    boq = load_cashflow_boq(RAW / "boq.csv")
    cumulative = load_cumulative_billed(RAW / "cumulative_billed_to_RA03.csv")

    from src.cashflow_forecaster import load_schedule

    activities = load_schedule(RAW / "SCP2_schedule.xer")

    forecast_lines = build_forecast_lines(
        boq,
        cumulative,
        activities,
    )

    existing_receipts = build_existing_cash_receipts()

    return forecast_cashflow(
        forecast_lines,
        existing_receipts,
    )


def money(value: Decimal) -> str:
    return f"INR {value:,.2f}"


def build_report() -> WeeklyReport:
    schedule, schedule_errors = load_schedule_report()

    (
        progress_pct,
        completed_tasks,
        total_tasks,
        completed_milestones,
        total_milestones,
    ) = calculate_progress(schedule)

    ra04 = calculate_ra04()
    approvals = calculate_approvals()
    cashflow = calculate_cashflow()

    cash_by_month = {row.month: row.amount_inr for row in cashflow}

    disputed_value = sum(
        (
            line.period_disputed_qty * line.rate_inr
            for line in ra04.lines
            if line.period_disputed_qty > 0
        ),
        Decimal("0"),
    )

    escalated = sum(1 for route in approvals if route.escalated)

    anti_splitting = sum(1 for route in approvals if route.anti_splitting_flag)

    exceptions = list(ra04.exceptions)

    if schedule_errors:
        exceptions.extend(f"Schedule validation: {error}" for error in schedule_errors)

    for route in approvals:
        if route.escalated:
            exceptions.append(
                f"{route.pr_no} escalated to {route.required_level} "
                f"because the assigned approver was unavailable."
            )

        if route.anti_splitting_flag:
            exceptions.append(
                f"{route.pr_no} triggered the anti-splitting " f"aggregation rule."
            )

    return WeeklyReport(
        reporting_date="2026-09-30",
        project=(schedule.project.proj_short_name if schedule.project else "SCP2"),
        schedule_status=("PASS" if not schedule_errors else "EXCEPTIONS"),
        progress_pct=progress_pct,
        completed_tasks=completed_tasks,
        total_tasks=total_tasks,
        completed_milestones=completed_milestones,
        total_milestones=total_milestones,
        ra04_gross=ra04.totals.gross_value_inr,
        ra04_net=ra04.totals.net_payable_inr,
        ra04_advance_recovery=ra04.totals.advance_recovery_inr,
        disputed_value=disputed_value,
        purchase_request_count=len(approvals),
        escalated_request_count=escalated,
        anti_splitting_count=anti_splitting,
        cash_oct=cash_by_month.get("2026-10", Decimal("0")),
        cash_nov=cash_by_month.get("2026-11", Decimal("0")),
        cash_dec=cash_by_month.get("2026-12", Decimal("0")),
        key_exceptions=tuple(exceptions),
    )


def render_report(report: WeeklyReport) -> str:
    lines = [
        "KAVERI INFRASYSTEMS — WEEKLY MANAGEMENT REPORT",
        "=" * 52,
        "",
        f"Reporting date: {report.reporting_date}",
        f"Project: {report.project}",
        "",
        "1. SCHEDULE & PROGRESS",
        "-" * 30,
        f"Schedule validation: {report.schedule_status}",
        (f"Activity progress: {report.progress_pct:.2f}%"),
        (f"Completed activities: " f"{report.completed_tasks}/{report.total_tasks}"),
        (
            f"Completed milestones: "
            f"{report.completed_milestones}/"
            f"{report.total_milestones}"
        ),
        "",
        "2. RA-04 BILLING",
        "-" * 30,
        f"Gross value: {money(report.ra04_gross)}",
        f"Advance recovery: {money(report.ra04_advance_recovery)}",
        f"Net payable: {money(report.ra04_net)}",
        f"Disputed value excluded: {money(report.disputed_value)}",
        "",
        "3. PURCHASE APPROVALS",
        "-" * 30,
        f"Purchase requests routed: {report.purchase_request_count}",
        f"Escalated requests: {report.escalated_request_count}",
        f"Anti-splitting flags: {report.anti_splitting_count}",
        "",
        "4. CASH-FLOW FORECAST",
        "-" * 30,
        f"October 2026: {money(report.cash_oct)}",
        f"November 2026: {money(report.cash_nov)}",
        f"December 2026: {money(report.cash_dec)}",
        "",
        "5. KEY EXCEPTIONS / MANAGEMENT ATTENTION",
        "-" * 30,
    ]

    if report.key_exceptions:
        for exception in report.key_exceptions:
            lines.append(f"- {exception}")
    else:
        lines.append("- No exceptions generated by the controlled checks.")

    lines.extend(
        [
            "",
            "SOURCE / CONTROL NOTE",
            "-" * 30,
            (
                "All numerical values are generated from controlled project "
                "data and deterministic program calculations. No external "
                "AI or external data source is used for the calculations."
            ),
        ]
    )

    return "\n".join(lines)


def main() -> None:
    report = build_report()
    print(render_report(report))


if __name__ == "__main__":
    main()
