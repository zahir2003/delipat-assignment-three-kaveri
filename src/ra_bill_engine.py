"""RA-04 bill engine for the Kaveri Infrasystems SCP2 contract.

All commercial calculations are performed in code using Decimal arithmetic.
No AI is involved in billing calculations.

The engine:
- reads BOQ, measurement, production, cumulative and bill-register data
- applies DELIVERY_QC, PROGRESS and MILESTONE rules
- enforces cumulative contract quantity caps
- records QC failures, disputes and variations
- calculates gross, GST, retention, mobilisation recovery and net payable
- fails safely when required source data is inconsistent
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from src.schedule_importer import parse_xer


GST_RATE = Decimal("0.18")
RETENTION_RATE = Decimal("0.05")
MOBILISATION_RATE = Decimal("0.08")
MOBILISATION_RECOVERY_RATE = Decimal("0.10")

REPORTING_MONTH = "2026-09"


class BillingDataError(ValueError):
    """Raised when billing source data is invalid or inconsistent."""


@dataclass(frozen=True)
class BoqItem:
    boq_item: str
    description: str
    unit: str
    contract_qty: Decimal
    rate_inr: Decimal
    billing_basis: str
    wbs_activity: str


@dataclass(frozen=True)
class Measurement:
    boq_item: str
    unit: str
    measured: Decimal
    certified: Decimal
    disputed: Decimal
    certified_by: str


@dataclass(frozen=True)
class ProductionSummary:
    boq_item: str
    dispatched_qty: Decimal
    qc_pass_qty: Decimal
    qc_failed_qty: Decimal
    steel_flags: tuple[str, ...]


@dataclass(frozen=True)
class BillLine:
    boq_item: str
    description: str
    unit: str
    contract_qty: Decimal
    previously_billed_qty: Decimal
    period_certified_qty: Decimal
    period_disputed_qty: Decimal
    period_billable_qty: Decimal
    variation_qty: Decimal
    rate_inr: Decimal
    gross_value_inr: Decimal
    exclusion_reason: str


@dataclass(frozen=True)
class BillTotals:
    gross_value_inr: Decimal
    gst_inr: Decimal
    retention_inr: Decimal
    advance_recovery_inr: Decimal
    net_payable_inr: Decimal
    contract_value_inr: Decimal
    mobilisation_advance_inr: Decimal
    previous_advance_recovered_inr: Decimal
    outstanding_advance_before_ra04_inr: Decimal


@dataclass(frozen=True)
class Ra04Bill:
    bill_no: str
    work_month: str
    lines: tuple[BillLine, ...]
    totals: BillTotals
    exceptions: tuple[str, ...]


def decimal(value: str | int | float | Decimal) -> Decimal:
    """Convert a value to Decimal without silently accepting bad data."""

    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, AttributeError):
        raise BillingDataError(
            f"Invalid numeric value: {value!r}"
        ) from None


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV file and return rows as dictionaries."""

    if not path.exists():
        raise BillingDataError(
            f"Required source file does not exist: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        return list(csv.DictReader(handle))


def load_boq(path: Path) -> dict[str, BoqItem]:
    """Load and validate BOQ master data."""

    rows = read_csv(path)
    result: dict[str, BoqItem] = {}

    for row in rows:
        item = row["boq_item"]

        if item in result:
            raise BillingDataError(
                f"Duplicate BOQ item: {item}"
            )

        result[item] = BoqItem(
            boq_item=item,
            description=row["description"],
            unit=row["unit"],
            contract_qty=decimal(row["contract_qty"]),
            rate_inr=decimal(row["rate_inr"]),
            billing_basis=row["billing_basis"],
            wbs_activity=row["wbs_activity"],
        )

    if not result:
        raise BillingDataError("BOQ is empty.")

    return result


def load_measurements(
    path: Path,
) -> dict[str, Measurement]:
    """Load September measurement and certification data."""

    rows = read_csv(path)
    result: dict[str, Measurement] = {}

    for row in rows:
        item = row["boq_item"]

        if item in result:
            raise BillingDataError(
                f"Duplicate measurement row for {item}"
            )

        measured = decimal(row["measured_this_period"])
        certified = decimal(row["certified_this_period"])
        disputed = decimal(row["disputed_this_period"])

        if measured < 0 or certified < 0 or disputed < 0:
            raise BillingDataError(
                f"Negative measurement quantity for {item}"
            )

        if certified + disputed > measured:
            raise BillingDataError(
                f"Certified + disputed exceeds measured quantity "
                f"for {item}"
            )

        result[item] = Measurement(
            boq_item=item,
            unit=row["unit"],
            measured=measured,
            certified=certified,
            disputed=disputed,
            certified_by=row["certified_by"],
        )

    return result


def load_production(
    path: Path,
) -> dict[str, ProductionSummary]:
    """Summarise September production by BOQ supply item."""

    rows = read_csv(path)

    grouped: dict[str, dict[str, object]] = {}

    for row in rows:
        item = row["boq_item"]

        if item not in grouped:
            grouped[item] = {
                "dispatched_qty": Decimal("0"),
                "qc_pass_qty": Decimal("0"),
                "qc_failed_qty": Decimal("0"),
                "steel_flags": [],
            }

        dispatched = decimal(row["dispatched_qty"])
        produced = decimal(row["produced_qty"])
        failed = decimal(row["qc_failed_qty"])
        steel_issued = decimal(row["steel_issued_kg"])
        standard_per_unit = decimal(row["std_steel_kg_per_unit"])

        if dispatched < 0 or produced < 0 or failed < 0:
            raise BillingDataError(
                f"Negative production quantity for {item}"
            )

        qc_pass = produced - failed

        if qc_pass < 0:
            raise BillingDataError(
                f"QC failed quantity exceeds production for {item}"
            )

        standard_total = produced * standard_per_unit

        if standard_total == 0:
            raise BillingDataError(
                f"Cannot calculate steel variance for {item}"
            )

        variance_ratio = (
            steel_issued - standard_total
        ) / standard_total

        flags = grouped[item]["steel_flags"]

        if variance_ratio > Decimal("0.05"):
            flags.append(
                f"{row['production_order']}: steel usage "
                f"{variance_ratio * Decimal('100'):.2f}% above standard"
            )

        grouped[item]["dispatched_qty"] += dispatched
        grouped[item]["qc_pass_qty"] += qc_pass
        grouped[item]["qc_failed_qty"] += failed

    result: dict[str, ProductionSummary] = {}

    for item, values in grouped.items():
        result[item] = ProductionSummary(
            boq_item=item,
            dispatched_qty=values["dispatched_qty"],
            qc_pass_qty=values["qc_pass_qty"],
            qc_failed_qty=values["qc_failed_qty"],
            steel_flags=tuple(values["steel_flags"]),
        )

    return result


def load_cumulative(
    path: Path,
) -> dict[str, Decimal]:
    """Load quantities billed through RA-03."""

    rows = read_csv(path)
    result: dict[str, Decimal] = {}

    for row in rows:
        item = row["boq_item"]

        if item in result:
            raise BillingDataError(
                f"Duplicate cumulative row for {item}"
            )

        quantity = decimal(row["cumulative_qty_billed"])

        if quantity < 0:
            raise BillingDataError(
                f"Negative cumulative billed quantity for {item}"
            )

        result[item] = quantity

    return result


def load_bill_register(
    path: Path,
) -> list[dict[str, str]]:
    """Load previous RA bills."""

    rows = read_csv(path)

    if not rows:
        raise BillingDataError(
            "Bill register is empty."
        )

    return rows


def previous_advance_recovered(
    bill_register: list[dict[str, str]],
) -> Decimal:
    """Calculate mobilisation recovery from RA-01 through RA-03."""

    # The contract states recovery is 10% of each RA gross value.
    # Use the recorded gross values from the bill register.
    total = Decimal("0")

    for row in bill_register:
        gross = decimal(row["gross_value_inr"])

        if gross < 0:
            raise BillingDataError(
                f"Negative gross value in {row['bill_no']}"
            )

        total += gross * MOBILISATION_RECOVERY_RATE

    return total


def contract_value(
    boq: dict[str, BoqItem],
) -> Decimal:
    """Calculate total contract value from BOQ quantities and rates."""

    return sum(
        (
            item.contract_qty * item.rate_inr
            for item in boq.values()
        ),
        Decimal("0"),
    )


def validate_milestones(
    boq: dict[str, BoqItem],
    schedule,
    cumulative: dict[str, Decimal],
    work_month: str,
) -> dict[str, Decimal]:
    """Determine milestone quantities billable in the requested month."""

    result: dict[str, Decimal] = {}

    for item in boq.values():
        if item.billing_basis != "MILESTONE":
            continue

        previously_billed = cumulative.get(
            item.boq_item,
            Decimal("0"),
        )

        if previously_billed > 0:
            result[item.boq_item] = Decimal("0")
            continue

        activity_codes = [
            code.strip()
            for code in item.wbs_activity.split("|")
            if code.strip()
        ]

        completed_in_month = False

        for task in schedule.tasks:
            if task.task_code not in activity_codes:
                continue

            if task.physical_complete_pct != 100:
                continue

            actual_end = task.actual_end_date or ""

            if actual_end.startswith(work_month):
                completed_in_month = True

        result[item.boq_item] = (
            item.contract_qty
            if completed_in_month
            else Decimal("0")
        )

    return result


def calculate_bill(
    boq: dict[str, BoqItem],
    measurements: dict[str, Measurement],
    production: dict[str, ProductionSummary],
    cumulative: dict[str, Decimal],
    bill_register: list[dict[str, str]],
    schedule,
    work_month: str = REPORTING_MONTH,
) -> Ra04Bill:
    """Calculate RA-04 entirely from source data."""

    if work_month != REPORTING_MONTH:
        raise BillingDataError(
            f"This implementation is for RA-04 September 2026, "
            f"not {work_month}."
        )

    exceptions: list[str] = []
    lines: list[BillLine] = []

    milestone_billable = validate_milestones(
        boq,
        schedule,
        cumulative,
        work_month,
    )

    for item_code, item in boq.items():
        previous = cumulative.get(
            item_code,
            Decimal("0"),
        )

        if previous > item.contract_qty:
            raise BillingDataError(
                f"Cumulative billed quantity exceeds contract "
                f"quantity for {item_code}"
            )

        measurement = measurements.get(item_code)
        production_summary = production.get(item_code)

        period_certified = Decimal("0")
        period_disputed = Decimal("0")
        period_billable = Decimal("0")
        variation = Decimal("0")
        exclusion_reason = ""

        if item.billing_basis == "PROGRESS":
            if measurement is None:
                period_billable = Decimal("0")
                exclusion_reason = (
                    "No September measurement/certification row."
                )
            else:
                period_certified = measurement.certified
                period_disputed = measurement.disputed

                if period_disputed > 0:
                    exclusion_reason = (
                        f"{period_disputed} {item.unit} disputed; "
                        "excluded from billing."
                    )

                remaining_cap = (
                    item.contract_qty - previous
                )

                period_billable = min(
                    period_certified,
                    remaining_cap,
                )

                variation = max(
                    period_certified - remaining_cap,
                    Decimal("0"),
                )

                if variation > 0:
                    exceptions.append(
                        f"{item_code}: {variation} {item.unit} "
                        "certified above contract quantity; "
                        "recorded as variation."
                    )

        elif item.billing_basis == "DELIVERY_QC":
            if production_summary is None:
                period_billable = Decimal("0")
                exclusion_reason = (
                    "No September production/QC data."
                )
            else:
                period_billable = production_summary.qc_pass_qty

                if production_summary.qc_failed_qty > 0:
                    exclusion_reason = (
                        f"{production_summary.qc_failed_qty} "
                        f"{item.unit} failed QC; excluded."
                    )

                remaining_cap = (
                    item.contract_qty - previous
                )

                if period_billable > remaining_cap:
                    variation = (
                        period_billable - remaining_cap
                    )
                    period_billable = remaining_cap

                    exceptions.append(
                        f"{item_code}: {variation} {item.unit} "
                        "above contract quantity; "
                        "recorded as variation."
                    )

        elif item.billing_basis == "MILESTONE":
            period_billable = milestone_billable.get(
                item_code,
                Decimal("0"),
            )

            if period_billable == 0:
                exclusion_reason = (
                    "Milestone not completed in September 2026 "
                    "or already billed."
                )

        else:
            raise BillingDataError(
                f"Unsupported billing basis for {item_code}: "
                f"{item.billing_basis}"
            )

        if period_billable < 0:
            raise BillingDataError(
                f"Negative billable quantity for {item_code}"
            )

        gross = (
            period_billable * item.rate_inr
        )

        lines.append(
            BillLine(
                boq_item=item_code,
                description=item.description,
                unit=item.unit,
                contract_qty=item.contract_qty,
                previously_billed_qty=previous,
                period_certified_qty=period_certified,
                period_disputed_qty=period_disputed,
                period_billable_qty=period_billable,
                variation_qty=variation,
                rate_inr=item.rate_inr,
                gross_value_inr=gross,
                exclusion_reason=exclusion_reason,
            )
        )

    contract_total = contract_value(boq)

    mobilisation_advance = (
        contract_total * MOBILISATION_RATE
    )

    previous_recovered = previous_advance_recovered(
        bill_register,
    )

    outstanding_before = max(
        mobilisation_advance - previous_recovered,
        Decimal("0"),
    )

    gross_total = sum(
        (
            line.gross_value_inr
            for line in lines
        ),
        Decimal("0"),
    )

    gst = gross_total * GST_RATE
    retention = gross_total * RETENTION_RATE

    proposed_recovery = (
        gross_total * MOBILISATION_RECOVERY_RATE
    )

    advance_recovery = min(
        proposed_recovery,
        outstanding_before,
    )

    net_payable = (
        gross_total
        + gst
        - retention
        - advance_recovery
    )

    totals = BillTotals(
        gross_value_inr=gross_total,
        gst_inr=gst,
        retention_inr=retention,
        advance_recovery_inr=advance_recovery,
        net_payable_inr=net_payable,
        contract_value_inr=contract_total,
        mobilisation_advance_inr=mobilisation_advance,
        previous_advance_recovered_inr=previous_recovered,
        outstanding_advance_before_ra04_inr=outstanding_before,
    )

    return Ra04Bill(
        bill_no="RA-04",
        work_month=work_month,
        lines=tuple(lines),
        totals=totals,
        exceptions=tuple(exceptions),
    )


def main() -> None:
    """Calculate and print the RA-04 bill."""

    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data" / "raw"

    boq = load_boq(
        data_dir / "boq.csv"
    )

    measurements = load_measurements(
        data_dir / "measurement_sheet_RA04.csv"
    )

    production = load_production(
        data_dir / "production_orders_sep2026.csv"
    )

    cumulative = load_cumulative(
        data_dir / "cumulative_billed_to_RA03.csv"
    )

    bill_register = load_bill_register(
        data_dir / "bill_register.csv"
    )

    schedule = parse_xer(
        data_dir / "SCP2_schedule.xer"
    )

    bill = calculate_bill(
        boq=boq,
        measurements=measurements,
        production=production,
        cumulative=cumulative,
        bill_register=bill_register,
        schedule=schedule,
    )

    print(f"Bill: {bill.bill_no}")
    print(f"Work month: {bill.work_month}")
    print()

    for line in bill.lines:
        print(
            f"{line.boq_item}: "
            f"billable={line.period_billable_qty} "
            f"{line.unit}, "
            f"gross=₹{line.gross_value_inr:,.2f}"
        )

    print()
    print(f"Gross: ₹{bill.totals.gross_value_inr:,.2f}")
    print(f"GST: ₹{bill.totals.gst_inr:,.2f}")
    print(
        f"Retention: "
        f"₹{bill.totals.retention_inr:,.2f}"
    )
    print(
        f"Advance recovery: "
        f"₹{bill.totals.advance_recovery_inr:,.2f}"
    )
    print(
        f"Net payable: "
        f"₹{bill.totals.net_payable_inr:,.2f}"
    )

    if bill.exceptions:
        print()
        print("Exceptions:")
        for exception in bill.exceptions:
            print(f"- {exception}")


if __name__ == "__main__":
    main()