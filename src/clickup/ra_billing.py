"""Create and maintain RA billing records in ClickUp."""

from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv

from src.clickup.client import ClickUpClient
from src.ra_bill_engine import (
    calculate_bill,
    load_bill_register,
    load_boq,
    load_cumulative,
    load_measurements,
    load_production,
)
from src.schedule_importer import parse_xer


LIST_ID = "1300410000043629"
DATA_DIR = Path("data/raw")
XER_FILE = DATA_DIR / "SCP2_schedule.xer"
SOURCE_KEY = "ra:RA-04:2026-09"


def money(value: Decimal) -> str:
    return f"INR{value:,.2f}"


def build_description(bill) -> str:
    totals = bill.totals

    lines = [
        f"source_key: {SOURCE_KEY}",
        "",
        "Kaveri Infrasystems — SCP2",
        "RA-04 Billing Record",
        "Work month: September 2026",
        "",
        "COMMERCIAL SUMMARY",
        f"Contract value: {money(totals.contract_value_inr)}",
        f"Gross value: {money(totals.gross_value_inr)}",
        f"GST @ 18%: {money(totals.gst_inr)}",
        f"Retention @ 5%: {money(totals.retention_inr)}",
        f"Advance recovery: {money(totals.advance_recovery_inr)}",
        f"Net payable: {money(totals.net_payable_inr)}",
        "",
        "ADVANCE",
        f"Mobilisation advance @ 8%: "
        f"{money(totals.mobilisation_advance_inr)}",
        f"Previous advance recovered: "
        f"{money(totals.previous_advance_recovered_inr)}",
        f"Outstanding before RA-04: "
        f"{money(totals.outstanding_advance_before_ra04_inr)}",
        "",
        "BILL LINES",
    ]

    boq_activity_map = {
        "B01": "A1010",
        "B02": "A2020",
        "B03": "A2030",
        "B04": "A3000 | A3010",
        "B05": "A3020",
        "B06": "A3030",
        "B07": "A4010",
    }

    for line in bill.lines:
        activity = boq_activity_map.get(
            line.boq_item,
            "NOT MAPPED",
        )

        lines.append(
            f"{line.boq_item} | "
            f"{line.description} | "
            f"WBS/activity={activity} | "
            f"billable={line.period_billable_qty} {line.unit} | "
            f"rate={money(line.rate_inr)} | "
            f"gross={money(line.gross_value_inr)}"
        )

        if line.period_disputed_qty:
            lines.append(
                f"  disputed={line.period_disputed_qty} {line.unit}"
            )

        if line.variation_qty:
            lines.append(
                f"  variation={line.variation_qty} {line.unit}"
            )

        if line.exclusion_reason:
            lines.append(
                f"  note={line.exclusion_reason}"
            )

    if bill.exceptions:
        lines.extend(
            [
                "",
                "EXCEPTIONS",
                *[f"- {item}" for item in bill.exceptions],
            ]
        )

    return "\n".join(lines)


def load_ra04_bill():
    boq = load_boq(DATA_DIR / "boq.csv")
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


def find_existing_task(client: ClickUpClient) -> dict | None:
    result = client.get_list_tasks(
        LIST_ID,
        subtasks=True,
    )

    for task in result.get("tasks", []):
        description = task.get("description") or ""

        if SOURCE_KEY in description:
            return task

    return None


def create_or_update_ra04(client: ClickUpClient) -> dict:
    bill = load_ra04_bill()

    description = build_description(bill)

    existing = find_existing_task(client)

    if existing:
        return client.update_task(
            existing["id"],
            name="RA-04 — September 2026",
            description=description,
        )

    return client.create_task(
        LIST_ID,
        name="RA-04 — September 2026",
        description=description,
        notify_all=False,
    )


def main() -> None:
    load_dotenv()

    client = ClickUpClient()

    task = create_or_update_ra04(client)

    print("RA-04 ClickUp record ready.")
    print(f"Task ID: {task.get('id')}")
    print(f"Task name: {task.get('name')}")
    print(f"List ID: {LIST_ID}")


if __name__ == "__main__":
    main()