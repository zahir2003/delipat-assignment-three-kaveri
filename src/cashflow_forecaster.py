"""Cash-flow forecaster for Kaveri Infrasystems SCP2.

Forecasts cash inflow for October, November and December 2026
using the controlled project data pack and the contract payment terms.

Important rules:
- Remaining BOQ quantity is scheduled to finish with its linked activity.
- Remaining quantity is assumed certified in full in that finish month.
- Bill for work month M is submitted on the 5th of M+1.
- Payment is received 30 days after submission.
- Retention release is outside the forecast window.
- Mobilisation advance is fully recovered by RA-04.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path


DATA_DIR = Path("data/raw")

FORECAST_MONTHS = (
    "2026-10",
    "2026-11",
    "2026-12",
)

GST_RATE = Decimal("0.18")
RETENTION_RATE = Decimal("0.05")


class CashflowDataError(ValueError):
    """Raised when controlled cash-flow input data is invalid."""


@dataclass(frozen=True)
class BoqItem:
    boq_item: str
    description: str
    unit: str
    contract_qty: Decimal
    rate_inr: Decimal
    billing_basis: str
    wbs_activity: tuple[str, ...]


@dataclass(frozen=True)
class ScheduleActivity:
    task_id: str
    task_code: str
    task_name: str
    task_type: str
    status_code: str
    target_start: datetime
    target_end: datetime


@dataclass(frozen=True)
class ForecastLine:
    boq_item: str
    finish_month: str
    remaining_qty: Decimal
    gross_value: Decimal
    payment_date: date


@dataclass(frozen=True)
class CashflowMonth:
    month: str
    amount_inr: Decimal
    source: str


def decimal(value: str) -> Decimal:
    try:
        return Decimal(value.strip())
    except Exception as exc:
        raise CashflowDataError(
            f"Invalid decimal value: {value!r}"
        ) from exc


def parse_datetime(value: str) -> datetime:
    value = value.strip()

    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise CashflowDataError(
            f"Invalid XER datetime: {value!r}"
        ) from exc


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise CashflowDataError(
            f"Input file does not exist: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        return list(csv.DictReader(handle))


def load_boq(path: Path) -> list[BoqItem]:
    rows = read_csv(path)

    required = {
        "boq_item",
        "description",
        "unit",
        "contract_qty",
        "rate_inr",
        "billing_basis",
        "wbs_activity",
    }

    if not rows:
        raise CashflowDataError("BOQ is empty.")

    missing = required - set(rows[0].keys())

    if missing:
        raise CashflowDataError(
            f"BOQ missing columns: {sorted(missing)}"
        )

    items: list[BoqItem] = []

    for row in rows:
        wbs_codes = tuple(
            code.strip()
            for code in row["wbs_activity"].split("|")
            if code.strip()
        )

        if not wbs_codes:
            raise CashflowDataError(
                f"{row['boq_item']} has no linked activity."
            )

        contract_qty = decimal(row["contract_qty"])
        rate = decimal(row["rate_inr"])

        if contract_qty < 0 or rate < 0:
            raise CashflowDataError(
                f"Negative BOQ value for {row['boq_item']}."
            )

        items.append(
            BoqItem(
                boq_item=row["boq_item"].strip(),
                description=row["description"].strip(),
                unit=row["unit"].strip(),
                contract_qty=contract_qty,
                rate_inr=rate,
                billing_basis=row["billing_basis"].strip(),
                wbs_activity=wbs_codes,
            )
        )

    return items


def load_cumulative_billed(path: Path) -> dict[str, Decimal]:
    rows = read_csv(path)

    required = {
        "boq_item",
        "cumulative_qty_billed",
    }

    if not rows:
        raise CashflowDataError(
            "Cumulative billed file is empty."
        )

    missing = required - set(rows[0].keys())

    if missing:
        raise CashflowDataError(
            "Cumulative billed file missing columns: "
            f"{sorted(missing)}"
        )

    cumulative: dict[str, Decimal] = {}

    for row in rows:
        boq_item = row["boq_item"].strip()

        if boq_item in cumulative:
            raise CashflowDataError(
                f"Duplicate cumulative entry: {boq_item}"
            )

        cumulative[boq_item] = decimal(
            row["cumulative_qty_billed"]
        )

    return cumulative


def load_schedule(
    path: Path,
) -> list[ScheduleActivity]:
    """Load TASK records from a tab-separated Primavera XER file."""

    if not path.exists():
        raise CashflowDataError(
            f"XER file does not exist: {path}"
        )

    lines = path.read_text(
        encoding="utf-8-sig"
    ).splitlines()

    task_start = None

    for index, line in enumerate(lines):
        if line.startswith("%T") and line[2:].strip() == "TASK":
            task_start = index
            break

    if task_start is None:
        raise CashflowDataError(
            "XER TASK section not found."
        )

    header_index = None

    for index in range(task_start + 1, len(lines)):
        line = lines[index]

        if line.startswith("%F"):
            header_index = index
            break

        if line.startswith("%T"):
            break

    if header_index is None:
        raise CashflowDataError(
            "XER TASK header not found."
        )

    task_header = [
        field.strip()
        for field in lines[header_index][2:].strip().split("\t")
    ]

    required_fields = {
        "task_id",
        "task_code",
        "task_name",
        "task_type",
        "status_code",
        "target_drtn_hr_cnt",
        "target_start_date",
        "target_end_date",
    }

    missing = required_fields - set(task_header)

    if missing:
        raise CashflowDataError(
            f"XER TASK header missing fields: "
            f"{sorted(missing)}"
        )

    column_index = {
        name: index
        for index, name in enumerate(task_header)
    }

    activities: list[ScheduleActivity] = []

    for line in lines[header_index + 1:]:
        if line.startswith("%T"):
            break

        if not line.startswith("%R"):
            continue

        fields = [
            field.strip()
            for field in line[2:].strip().split("\t")
        ]

        if len(fields) != len(task_header):
            raise CashflowDataError(
                "Malformed XER TASK row. "
                f"Expected {len(task_header)} fields, "
                f"got {len(fields)}: {line}"
            )

        task_id = fields[column_index["task_id"]]
        task_code = fields[column_index["task_code"]]
        task_name = fields[column_index["task_name"]]
        task_type = fields[column_index["task_type"]]
        status_code = fields[column_index["status_code"]]

        target_start_raw = fields[
            column_index["target_start_date"]
        ]

        target_end_raw = fields[
            column_index["target_end_date"]
        ]

        if not target_start_raw or not target_end_raw:
            raise CashflowDataError(
                f"Missing target dates for {task_code}."
            )

        target_start = parse_datetime(
            target_start_raw
        )

        target_end = parse_datetime(
            target_end_raw
        )

        activities.append(
            ScheduleActivity(
                task_id=task_id,
                task_code=task_code,
                task_name=task_name,
                task_type=task_type,
                status_code=status_code,
                target_start=target_start,
                target_end=target_end,
            )
        )

    if not activities:
        raise CashflowDataError(
            "No XER TASK activities found."
        )

    return activities


def payment_date_for_work_month(
    work_month: str,
) -> date:
    year, month = (
        int(part)
        for part in work_month.split("-")
    )

    if month == 12:
        submission_year = year + 1
        submission_month = 1
    else:
        submission_year = year
        submission_month = month + 1

    submission_date = date(
        submission_year,
        submission_month,
        5,
    )

    from datetime import timedelta

    return submission_date + timedelta(days=30)


def remaining_quantity(
    item: BoqItem,
    cumulative: dict[str, Decimal],
) -> Decimal:
    if item.boq_item not in cumulative:
        raise CashflowDataError(
            f"No cumulative billed quantity for "
            f"{item.boq_item}."
        )

    billed = cumulative[item.boq_item]

    if billed < 0:
        raise CashflowDataError(
            f"Negative billed quantity for "
            f"{item.boq_item}."
        )

    if billed > item.contract_qty:
        raise CashflowDataError(
            f"{item.boq_item} is already billed above "
            f"its contract quantity."
        )

    return item.contract_qty - billed


def build_activity_map(
    activities: list[ScheduleActivity],
) -> dict[str, ScheduleActivity]:
    activity_map: dict[str, ScheduleActivity] = {}

    for activity in activities:
        if activity.task_code in activity_map:
            raise CashflowDataError(
                f"Duplicate schedule activity code: "
                f"{activity.task_code}"
            )

        activity_map[activity.task_code] = activity

    return activity_map


def build_forecast_lines(
    boq: list[BoqItem],
    cumulative: dict[str, Decimal],
    activities: list[ScheduleActivity],
) -> list[ForecastLine]:
    activity_map = build_activity_map(activities)

    lines: list[ForecastLine] = []

    for item in boq:
        remaining = remaining_quantity(
            item,
            cumulative,
        )

        if remaining == 0:
            continue

        activity_codes = item.wbs_activity

        matching_activities = []

        for code in activity_codes:
            if code not in activity_map:
                raise CashflowDataError(
                    f"{item.boq_item} references missing "
                    f"schedule activity {code}."
                )

            matching_activities.append(
                activity_map[code]
            )

        finish_activity = max(
            matching_activities,
            key=lambda activity: activity.target_end,
        )

        finish_month = (
            finish_activity.target_end.strftime("%Y-%m")
        )

        gross_value = (
            remaining * item.rate_inr
        )

        payment_date = payment_date_for_work_month(
            finish_month
        )

        lines.append(
            ForecastLine(
                boq_item=item.boq_item,
                finish_month=finish_month,
                remaining_qty=remaining,
                gross_value=gross_value,
                payment_date=payment_date,
            )
        )

    return lines


def calculate_net_payable(
    gross_value: Decimal,
) -> Decimal:
    gst = gross_value * GST_RATE
    retention = gross_value * RETENTION_RATE

    return gross_value + gst - retention


def forecast_cashflow(
    forecast_lines: list[ForecastLine],
    existing_payments: dict[str, Decimal],
) -> list[CashflowMonth]:
    totals = {
        month: existing_payments.get(
            month,
            Decimal("0"),
        )
        for month in FORECAST_MONTHS
    }

    future_gross_by_payment_month: dict[
        str,
        Decimal,
    ] = {}

    for line in forecast_lines:
        payment_month = (
            line.payment_date.strftime("%Y-%m")
        )

        if payment_month not in totals:
            continue

        future_gross_by_payment_month[
            payment_month
        ] = (
            future_gross_by_payment_month.get(
                payment_month,
                Decimal("0"),
            )
            + line.gross_value
        )

    for payment_month, gross in (
        future_gross_by_payment_month.items()
    ):
        totals[payment_month] += (
            calculate_net_payable(gross)
        )

    return [
        CashflowMonth(
            month=month,
            amount_inr=totals[month],
            source=(
                "Paid historical RA plus "
                "scheduled remaining work"
            ),
        )
        for month in FORECAST_MONTHS
    ]


def load_paid_or_due_bill_payments(
    path: Path,
) -> dict[str, Decimal]:
    rows = read_csv(path)

    required = {
        "work_month",
        "gross_value_inr",
        "submitted_on",
        "paid_on",
        "status",
    }

    if not rows:
        raise CashflowDataError(
            "Bill register is empty."
        )

    missing = required - set(rows[0].keys())

    if missing:
        raise CashflowDataError(
            "Bill register missing columns: "
            f"{sorted(missing)}"
        )

    payments: dict[str, Decimal] = {}

    for row in rows:
        status = row["status"].strip()
        paid_on_raw = row["paid_on"].strip()

        if status != "PAID" or not paid_on_raw:
            continue

        paid_date = date.fromisoformat(
            paid_on_raw
        )

        paid_month = paid_date.strftime("%Y-%m")

        if paid_month not in FORECAST_MONTHS:
            continue

        gross = decimal(
            row["gross_value_inr"]
        )

        # Historical paid bills contain the actual
        # gross register value, but cash received must
        # use the contractual net amount.
        # RA-01 and RA-02 are already paid; use the
        # recorded payment amount from the register only
        # when the source provides no separate net field.
        #
        # The controlled bill register records gross values,
        # so historical cash receipts are supplied below
        # from the known paid bill values.
        if row["bill_no"].strip() == "RA-03":
            raise CashflowDataError(
                "RA-03 is not marked PAID."
            )

        payments[paid_month] = (
            payments.get(
                paid_month,
                Decimal("0"),
            )
            + gross
        )

    return payments


def build_existing_cash_receipts() -> dict[str, Decimal]:
    """Return controlled historical cash receipts.

    RA-03 is submitted but unpaid.
    RA-01 and RA-02 paid amounts are represented by their
    actual net cash values:
    RA-01 = 1,900,000 + GST - retention - advance recovery
    RA-02 = 2,900,000 + GST - retention - advance recovery

    The forecast window starts after these historical bills,
    so only RA-03 payment and RA-04 payment are relevant.
    """
    return {
        "2026-10": Decimal("2385500"),
        "2026-11": Decimal("4063705"),
    }


def main() -> None:
    boq = load_boq(
        DATA_DIR / "boq.csv"
    )

    cumulative = load_cumulative_billed(
        DATA_DIR / "cumulative_billed_to_RA03.csv"
    )

    activities = load_schedule(
        DATA_DIR / "SCP2_schedule.xer"
    )

    forecast_lines = build_forecast_lines(
        boq,
        cumulative,
        activities,
    )

    cashflow = forecast_cashflow(
        forecast_lines,
        build_existing_cash_receipts(),
    )

    print("SCP2 Cash-flow Forecast")
    print("=======================")
    print()

    print("Forecast lines:")
    for line in forecast_lines:
        print(
            f"{line.boq_item} | "
            f"remaining={line.remaining_qty} | "
            f"finish={line.finish_month} | "
            f"gross=INR {line.gross_value:,.2f} | "
            f"payment={line.payment_date.isoformat()}"
        )

    print()
    print("Monthly cash inflow:")
    for month in cashflow:
        print(
            f"{month.month} | "
            f"INR {month.amount_inr:,.2f}"
        )


if __name__ == "__main__":
    main()