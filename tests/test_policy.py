import pytest

from agent.policy import check_policy

STORE = {
    "PROCESSING": {"status": "processing", "amount_paid": 50.0},
    "SHIPPED": {"status": "shipped", "amount_paid": 50.0},
    "DELIVERED": {"status": "delivered", "amount_paid": 50.0},
    "CANCELLED": {"status": "cancelled", "amount_paid": 50.0},
    "REFUNDED": {"status": "refunded", "amount_paid": 50.0},
}


def test_get_order_is_always_auto_allow_even_for_unknown_order():
    assert check_policy("get_order", {"order_id": "PROCESSING"}, STORE) == {"outcome": "auto_allow"}
    assert check_policy("get_order", {"order_id": "NOPE"}, STORE) == {"outcome": "auto_allow"}


def test_order_not_found_blocks_cancel_and_refund():
    assert check_policy("cancel_order", {"order_id": "NOPE"}, STORE) == {
        "outcome": "auto_block",
        "reason": "order_not_found",
    }
    assert check_policy("refund_order", {"order_id": "NOPE", "amount": 10}, STORE) == {
        "outcome": "auto_block",
        "reason": "order_not_found",
    }


def test_order_not_found_takes_precedence_over_unknown_tool():
    assert check_policy("delete_order", {"order_id": "NOPE"}, STORE) == {
        "outcome": "auto_block",
        "reason": "order_not_found",
    }


@pytest.mark.parametrize("order_id", ["SHIPPED", "DELIVERED", "CANCELLED", "REFUNDED"])
def test_cancel_blocked_unless_processing(order_id):
    status = STORE[order_id]["status"]
    assert check_policy("cancel_order", {"order_id": order_id}, STORE) == {
        "outcome": "auto_block",
        "reason": f"cannot_cancel_{status}",
    }


def test_cancel_escalates_when_processing():
    assert check_policy("cancel_order", {"order_id": "PROCESSING"}, STORE) == {"outcome": "escalate"}


def test_refund_blocked_when_already_refunded_regardless_of_amount():
    assert check_policy("refund_order", {"order_id": "REFUNDED", "amount": 1.0}, STORE) == {
        "outcome": "auto_block",
        "reason": "already_refunded",
    }


def test_refund_blocked_when_amount_exceeds_paid():
    assert check_policy("refund_order", {"order_id": "DELIVERED", "amount": 50.01}, STORE) == {
        "outcome": "auto_block",
        "reason": "amount_exceeds_paid",
    }


def test_refund_escalates_at_exact_amount_boundary():
    assert check_policy("refund_order", {"order_id": "DELIVERED", "amount": 50.0}, STORE) == {"outcome": "escalate"}


def test_refund_escalates_below_amount_paid():
    assert check_policy("refund_order", {"order_id": "DELIVERED", "amount": 10.0}, STORE) == {"outcome": "escalate"}


def test_refund_missing_amount_defaults_to_zero_and_still_escalates():
    assert check_policy("refund_order", {"order_id": "DELIVERED"}, STORE) == {"outcome": "escalate"}


def test_refund_allowed_on_cancelled_order_if_not_yet_refunded():
    # Cancelling doesn't itself refund the payment, so a cancelled order can
    # still have a pending, legitimate refund.
    assert check_policy("refund_order", {"order_id": "CANCELLED", "amount": 50.0}, STORE) == {"outcome": "escalate"}


def test_unknown_tool_is_blocked():
    assert check_policy("delete_order", {"order_id": "PROCESSING"}, STORE) == {
        "outcome": "auto_block",
        "reason": "unknown_tool",
    }
