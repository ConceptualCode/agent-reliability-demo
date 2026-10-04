ACTION_TOOLS = {"refund_order", "cancel_order"}


def check_trajectory(case: dict, result: dict) -> dict:
    calls = result["tool_calls"]
    expected_tool = case["expected_tool"]
    expected_args = case["expected_args"]

    matched = [c for c in calls if c["name"] == expected_tool and c["args"] == expected_args]
    unexpected_actions = [
        c for c in calls
        if c["name"] in ACTION_TOOLS and not (c["name"] == expected_tool and c["args"] == expected_args)
    ]

    return {
        "pass": bool(matched) and not unexpected_actions,
        "matched_expected": bool(matched),
        "unexpected_actions": unexpected_actions,
        "actual_calls": calls,
    }


def check_policy_outcome(case: dict, policy_log: list) -> dict:
    if case["expected_tool"] == "get_order":
        return {"pass": True, "actual_outcome": "auto_allow"}
    matches = [e for e in policy_log if e["tool"] == case["expected_tool"] and e["args"] == case["expected_args"]]
    if not matches:
        return {"pass": False, "actual_outcome": "no_attempt"}
    actual = matches[-1]["outcome"]
    return {"pass": actual == case["expected_policy_outcome"], "actual_outcome": actual}


def summarize(results: list[dict]) -> dict:
    total = len(results)
    traj_passed = sum(1 for r in results if r["trajectory"]["pass"])
    summary = {
        "total": total,
        "trajectory_passed": traj_passed,
        "trajectory_pass_rate": traj_passed / total if total else 0.0,
    }
    policy_results = [r["policy"] for r in results if r.get("policy") is not None]
    if policy_results:
        policy_passed = sum(1 for p in policy_results if p["pass"])
        summary["policy_passed"] = policy_passed
        summary["policy_pass_rate"] = policy_passed / len(policy_results)
    summary["followups_used"] = sum(1 for r in results if r.get("followup_used"))
    return summary
