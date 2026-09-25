from datetime import date
from decimal import Decimal
from pathlib import Path

from src.approval_router import (
    ApprovalLevel,
    PurchaseRequest,
    load_approval_matrix,
    load_purchase_requests,
    route_requests,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "raw"


def load_test_routes():
    levels = load_approval_matrix(
        DATA_DIR / "approval_matrix.csv"
    )

    requests = load_purchase_requests(
        DATA_DIR / "purchase_requests_sep2026.csv"
    )

    return route_requests(levels, requests)


def test_purchase_request_count() -> None:
    requests = load_purchase_requests(
        DATA_DIR / "purchase_requests_sep2026.csv"
    )

    assert len(requests) == 9


def test_exact_l1_limit_stays_at_l1() -> None:
    routes = load_test_routes()

    pr102 = next(
        route
        for route in routes
        if route.pr_no == "PR-102"
    )

    assert pr102.value_inr == Decimal("50000")
    assert pr102.aggregate_value_inr == Decimal("50000")
    assert pr102.required_level == "L1"
    assert pr102.approver == "Arjun Mehta"
    assert pr102.escalated is False


def test_value_just_above_l1_moves_to_l2() -> None:
    routes = load_test_routes()

    pr103 = next(
        route
        for route in routes
        if route.pr_no == "PR-103"
    )

    assert pr103.value_inr == Decimal("50001")
    assert pr103.required_level == "L2"
    assert pr103.approver == "Neha Kulkarni"
    assert pr103.escalated is False


def test_neha_leave_causes_pr104_escalation() -> None:
    routes = load_test_routes()

    pr104 = next(
        route
        for route in routes
        if route.pr_no == "PR-104"
    )

    assert pr104.required_level == "L2"
    assert pr104.approver == "Vikram Rao"
    assert pr104.role == "Operations Head"
    assert pr104.escalated is True


def test_same_requester_vendor_date_is_aggregated() -> None:
    routes = load_test_routes()

    pr105 = next(
        route
        for route in routes
        if route.pr_no == "PR-105"
    )

    pr106 = next(
        route
        for route in routes
        if route.pr_no == "PR-106"
    )

    assert pr105.aggregate_value_inr == Decimal("90000")
    assert pr106.aggregate_value_inr == Decimal("90000")

    assert pr105.required_level == "L3"
    assert pr106.required_level == "L3"

    assert pr105.approver == "Vikram Rao"
    assert pr106.approver == "Vikram Rao"

    assert pr105.anti_splitting_flag is True
    assert pr106.anti_splitting_flag is True


def test_above_l3_limit_routes_to_l4() -> None:
    routes = load_test_routes()

    pr107 = next(
        route
        for route in routes
        if route.pr_no == "PR-107"
    )

    assert pr107.value_inr == Decimal("620000")
    assert pr107.required_level == "L4"
    assert pr107.approver == "Suresh Iyer"
    assert pr107.role == "Finance Head"
    assert pr107.escalated is False


def test_leave_end_date_is_inclusive() -> None:
    routes = load_test_routes()

    pr108 = next(
        route
        for route in routes
        if route.pr_no == "PR-108"
    )

    assert pr108.request_date == date(2026, 9, 26)
    assert pr108.required_level == "L2"
    assert pr108.approver == "Vikram Rao"
    assert pr108.escalated is True


def test_request_after_leave_returns_to_l2() -> None:
    routes = load_test_routes()

    pr109 = next(
        route
        for route in routes
        if route.pr_no == "PR-109"
    )

    assert pr109.request_date == date(2026, 9, 27)
    assert pr109.required_level == "L2"
    assert pr109.approver == "Neha Kulkarni"
    assert pr109.escalated is False


def test_normal_l1_request_routes_to_arjun() -> None:
    routes = load_test_routes()

    pr101 = next(
        route
        for route in routes
        if route.pr_no == "PR-101"
    )

    assert pr101.required_level == "L1"
    assert pr101.approver == "Arjun Mehta"
    assert pr101.anti_splitting_flag is False


def test_all_requests_have_routes() -> None:
    requests = load_purchase_requests(
        DATA_DIR / "purchase_requests_sep2026.csv"
    )

    routes = load_test_routes()

    assert {
        route.pr_no
        for route in routes
    } == {
        request.pr_no
        for request in requests
    }