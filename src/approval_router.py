"""Purchase approval router for Kaveri Infrasystems.

The router applies the approval matrix, inclusive leave dates,
and anti-splitting aggregation rules from the project policy.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path


DATA_DIR = Path("data/raw")
REPORTING_MONTH = "2026-09"


class ApprovalDataError(ValueError):
    """Raised when approval input data is invalid."""


@dataclass(frozen=True)
class ApprovalLevel:
    level: str
    approver: str
    role: str
    approval_limit_inr: Decimal | None
    leave_from: date | None
    leave_to: date | None


@dataclass(frozen=True)
class PurchaseRequest:
    pr_no: str
    request_date: date
    requested_by: str
    vendor: str
    item: str
    value_inr: Decimal


@dataclass(frozen=True)
class ApprovalRoute:
    pr_no: str
    requested_by: str
    vendor: str
    request_date: date
    value_inr: Decimal
    aggregate_value_inr: Decimal
    required_level: str
    approver: str
    role: str
    escalated: bool
    aggregation_key: str
    anti_splitting_flag: bool


def decimal(value: str) -> Decimal:
    try:
        return Decimal(value.strip())
    except Exception as exc:
        raise ApprovalDataError(
            f"Invalid monetary value: {value!r}"
        ) from exc


def parse_date(value: str) -> date | None:
    value = value.strip()

    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ApprovalDataError(
            f"Invalid date: {value!r}"
        ) from exc


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise ApprovalDataError(
            f"Input file does not exist: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        return list(csv.DictReader(handle))


def load_approval_matrix(
    path: Path,
) -> list[ApprovalLevel]:
    rows = read_csv(path)

    required = {
        "level",
        "approver",
        "role",
        "approval_limit_inr",
        "leave_from",
        "leave_to",
    }

    if not rows:
        raise ApprovalDataError(
            "Approval matrix is empty."
        )

    missing = required - set(rows[0].keys())

    if missing:
        raise ApprovalDataError(
            f"Approval matrix missing columns: "
            f"{sorted(missing)}"
        )

    levels: list[ApprovalLevel] = []

    for row in rows:
        limit_raw = row["approval_limit_inr"].strip()

        limit = (
            None
            if not limit_raw
            else decimal(limit_raw)
        )

        leave_from = parse_date(row["leave_from"])
        leave_to = parse_date(row["leave_to"])

        if (
            leave_from is not None
            and leave_to is not None
            and leave_from > leave_to
        ):
            raise ApprovalDataError(
                f"Invalid leave range for "
                f"{row['approver']}"
            )

        levels.append(
            ApprovalLevel(
                level=row["level"].strip(),
                approver=row["approver"].strip(),
                role=row["role"].strip(),
                approval_limit_inr=limit,
                leave_from=leave_from,
                leave_to=leave_to,
            )
        )

    return levels


def load_purchase_requests(
    path: Path,
) -> list[PurchaseRequest]:
    rows = read_csv(path)

    required = {
        "pr_no",
        "request_date",
        "requested_by",
        "vendor",
        "item",
        "value_inr",
    }

    if not rows:
        raise ApprovalDataError(
            "Purchase request file is empty."
        )

    missing = required - set(rows[0].keys())

    if missing:
        raise ApprovalDataError(
            f"Purchase request file missing columns: "
            f"{sorted(missing)}"
        )

    requests: list[PurchaseRequest] = []

    for row in rows:
        request_date = parse_date(row["request_date"])

        if request_date is None:
            raise ApprovalDataError(
                f"Missing request date for {row['pr_no']}"
            )

        value = decimal(row["value_inr"])

        if value <= 0:
            raise ApprovalDataError(
                f"Purchase request {row['pr_no']} "
                f"has non-positive value."
            )

        requests.append(
            PurchaseRequest(
                pr_no=row["pr_no"].strip(),
                request_date=request_date,
                requested_by=row["requested_by"].strip(),
                vendor=row["vendor"].strip(),
                item=row["item"].strip(),
                value_inr=value,
            )
        )

    return requests


def is_on_leave(
    level: ApprovalLevel,
    request_date: date,
) -> bool:
    if level.leave_from is None or level.leave_to is None:
        return False

    return (
        level.leave_from
        <= request_date
        <= level.leave_to
    )


def aggregate_key(request: PurchaseRequest) -> str:
    return (
        f"{request.requested_by}|"
        f"{request.vendor}|"
        f"{request.request_date.isoformat()}"
    )


def build_aggregates(
    requests: list[PurchaseRequest],
) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}

    for request in requests:
        key = aggregate_key(request)

        totals[key] = (
            totals.get(key, Decimal("0"))
            + request.value_inr
        )

    return totals


def find_required_level(
    levels: list[ApprovalLevel],
    amount: Decimal,
) -> int:
    for index, level in enumerate(levels):
        limit = level.approval_limit_inr

        if limit is None or amount <= limit:
            return index

    raise ApprovalDataError(
        f"No approval level covers amount {amount}."
    )


def route_requests(
    levels: list[ApprovalLevel],
    requests: list[PurchaseRequest],
) -> list[ApprovalRoute]:
    if not levels:
        raise ApprovalDataError(
            "Approval matrix contains no levels."
        )

    aggregates = build_aggregates(requests)

    routes: list[ApprovalRoute] = []

    for request in requests:
        key = aggregate_key(request)
        aggregate_value = aggregates[key]

        required_index = find_required_level(
            levels,
            aggregate_value,
        )

        selected_index = required_index

        while selected_index < len(levels):
            level = levels[selected_index]

            if not is_on_leave(
                level,
                request.request_date,
            ):
                break

            selected_index += 1

        if selected_index >= len(levels):
            raise ApprovalDataError(
                f"No available approver for {request.pr_no}."
            )

        selected_level = levels[selected_index]

        anti_splitting_flag = (
            aggregate_value > request.value_inr
        )

        routes.append(
            ApprovalRoute(
                pr_no=request.pr_no,
                requested_by=request.requested_by,
                vendor=request.vendor,
                request_date=request.request_date,
                value_inr=request.value_inr,
                aggregate_value_inr=aggregate_value,
                required_level=levels[
                    required_index
                ].level,
                approver=selected_level.approver,
                role=selected_level.role,
                escalated=(
                    selected_index > required_index
                ),
                aggregation_key=key,
                anti_splitting_flag=anti_splitting_flag,
            )
        )

    return routes


def format_money(value: Decimal) -> str:
    return f"₹{value:,.2f}"


def main() -> None:
    levels = load_approval_matrix(
        DATA_DIR / "approval_matrix.csv"
    )

    requests = load_purchase_requests(
        DATA_DIR / "purchase_requests_sep2026.csv"
    )

    routes = route_requests(
        levels,
        requests,
    )

    print("Purchase Approval Routing")
    print(f"Requests: {len(requests)}")
    print()

    for route in routes:
        flags = []

        if route.escalated:
            flags.append("ESCALATED")

        if route.anti_splitting_flag:
            flags.append("AGGREGATED")

        flag_text = (
            f" [{' | '.join(flags)}]"
            if flags
            else ""
        )

        print(
            f"{route.pr_no} | "
            f"{format_money(route.value_inr)} | "
            f"aggregate={format_money(route.aggregate_value_inr)} | "
            f"required={route.required_level} | "
            f"approver={route.approver} | "
            f"role={route.role}"
            f"{flag_text}"
        )


if __name__ == "__main__":
    main()