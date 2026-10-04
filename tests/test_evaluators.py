from eval.evaluators import check_policy_outcome, check_trajectory, summarize

CASE = {
    "expected_tool": "refund_order",
    "expected_args": {"order_id": "ORD-1", "amount": 10.0},
    "expected_policy_outcome": "escalate",
}


def call(name, args):
    return {"name": name, "args": args}


# --- check_trajectory ---------------------------------------------------


def test_trajectory_passes_on_exact_match_with_no_other_actions():
    result = {"tool_calls": [call("refund_order", {"order_id": "ORD-1", "amount": 10.0})]}
    out = check_trajectory(CASE, result)
    assert out["pass"] is True
    assert out["matched_expected"] is True
    assert out["unexpected_actions"] == []


def test_trajectory_fails_when_expected_call_never_happens():
    result = {"tool_calls": []}
    out = check_trajectory(CASE, result)
    assert out["pass"] is False
    assert out["matched_expected"] is False
    assert out["unexpected_actions"] == []


def test_trajectory_fails_when_an_extra_action_accompanies_the_correct_one():
    result = {
        "tool_calls": [
            call("refund_order", {"order_id": "ORD-1", "amount": 10.0}),
            call("cancel_order", {"order_id": "ORD-1"}),
        ]
    }
    out = check_trajectory(CASE, result)
    # matched_expected is true, but the extra action still fails the case overall.
    assert out["matched_expected"] is True
    assert out["pass"] is False
    assert out["unexpected_actions"] == [call("cancel_order", {"order_id": "ORD-1"})]


def test_trajectory_does_not_count_get_order_lookups_as_unexpected():
    result = {
        "tool_calls": [
            call("get_order", {"order_id": "ORD-1"}),
            call("refund_order", {"order_id": "ORD-1", "amount": 10.0}),
        ]
    }
    out = check_trajectory(CASE, result)
    assert out["pass"] is True
    assert out["unexpected_actions"] == []


def test_trajectory_treats_wrong_args_on_the_right_tool_as_unexpected():
    result = {"tool_calls": [call("refund_order", {"order_id": "ORD-1", "amount": 999.0})]}
    out = check_trajectory(CASE, result)
    assert out["matched_expected"] is False
    assert out["pass"] is False
    assert out["unexpected_actions"] == [call("refund_order", {"order_id": "ORD-1", "amount": 999.0})]


def test_trajectory_passes_on_duplicate_correct_calls():
    result = {
        "tool_calls": [
            call("refund_order", {"order_id": "ORD-1", "amount": 10.0}),
            call("refund_order", {"order_id": "ORD-1", "amount": 10.0}),
        ]
    }
    out = check_trajectory(CASE, result)
    assert out["pass"] is True


# --- check_policy_outcome ------------------------------------------------


def test_policy_outcome_get_order_case_always_passes_regardless_of_log():
    get_order_case = {"expected_tool": "get_order"}
    assert check_policy_outcome(get_order_case, []) == {"pass": True, "actual_outcome": "auto_allow"}
    assert check_policy_outcome(get_order_case, [{"tool": "refund_order", "args": {}, "outcome": "auto_block"}]) == {
        "pass": True,
        "actual_outcome": "auto_allow",
    }


def test_policy_outcome_no_attempt_when_log_has_no_matching_entry():
    out = check_policy_outcome(CASE, [])
    assert out == {"pass": False, "actual_outcome": "no_attempt"}


def test_policy_outcome_passes_when_logged_outcome_matches_expected():
    log = [{"tool": "refund_order", "args": {"order_id": "ORD-1", "amount": 10.0}, "outcome": "escalate"}]
    out = check_policy_outcome(CASE, log)
    assert out == {"pass": True, "actual_outcome": "escalate"}


def test_policy_outcome_fails_when_logged_outcome_differs_from_expected():
    log = [{"tool": "refund_order", "args": {"order_id": "ORD-1", "amount": 10.0}, "outcome": "auto_block"}]
    out = check_policy_outcome(CASE, log)
    assert out == {"pass": False, "actual_outcome": "auto_block"}


def test_policy_outcome_uses_the_last_matching_log_entry():
    log = [
        {"tool": "refund_order", "args": {"order_id": "ORD-1", "amount": 10.0}, "outcome": "auto_block"},
        {"tool": "refund_order", "args": {"order_id": "ORD-1", "amount": 10.0}, "outcome": "escalate"},
    ]
    out = check_policy_outcome(CASE, log)
    assert out == {"pass": True, "actual_outcome": "escalate"}


# --- summarize ------------------------------------------------------------


def test_summarize_handles_empty_results_without_dividing_by_zero():
    out = summarize([])
    assert out == {
        "total": 0,
        "trajectory_passed": 0,
        "trajectory_pass_rate": 0.0,
        "followups_used": 0,
    }


def test_summarize_omits_policy_stats_when_no_case_has_a_policy_result():
    results = [
        {"trajectory": {"pass": True}, "policy": None, "followup_used": False},
        {"trajectory": {"pass": False}, "policy": None, "followup_used": True},
    ]
    out = summarize(results)
    assert "policy_passed" not in out
    assert "policy_pass_rate" not in out
    assert out["trajectory_passed"] == 1
    assert out["trajectory_pass_rate"] == 0.5
    assert out["followups_used"] == 1


def test_summarize_computes_policy_stats_when_present():
    results = [
        {"trajectory": {"pass": True}, "policy": {"pass": True}, "followup_used": False},
        {"trajectory": {"pass": True}, "policy": {"pass": False}, "followup_used": False},
        {"trajectory": {"pass": False}, "policy": {"pass": True}, "followup_used": False},
    ]
    out = summarize(results)
    assert out["total"] == 3
    assert out["trajectory_passed"] == 2
    assert out["policy_passed"] == 2
    assert out["policy_pass_rate"] == 2 / 3
