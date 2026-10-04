import copy
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from data.orders import ORDERS
from agent.agent import build_agent, run_turn, extract_trajectory
from agent.tools import make_tools
from agent.guarded_tools import make_guarded_tools
from eval.evaluators import check_trajectory, check_policy_outcome, summarize

ROOT = Path(__file__).resolve().parent.parent
FOLLOWUP_MESSAGE = "Yes, please go ahead."


def load_cases() -> list[dict]:
    normal = json.loads((ROOT / "eval/normal_cases.json").read_text())
    adversarial = json.loads((ROOT / "eval/adversarial_cases.json").read_text())
    return normal + adversarial


def run_case(case: dict, guarded: bool) -> dict:
    store = copy.deepcopy(ORDERS)
    policy_log: list = []
    tools = make_guarded_tools(store, policy_log) if guarded else make_tools(store)
    agent = build_agent(tools)

    human_input = f"Order ID: {case['order_id']}\nCustomer message: {case['message']}"
    messages = run_turn(agent, [], human_input)
    trajectory = check_trajectory(case, extract_trajectory(messages))

    followup_used = not trajectory["matched_expected"] and not trajectory["unexpected_actions"]
    if followup_used:
        messages = run_turn(agent, messages, FOLLOWUP_MESSAGE)
        trajectory = check_trajectory(case, extract_trajectory(messages))

    agent_result = extract_trajectory(messages)
    policy = check_policy_outcome(case, policy_log) if guarded else None
    state_changed = store[case["order_id"]]["status"] != ORDERS[case["order_id"]]["status"]
    return {
        "id": case["id"],
        "category": case["category"],
        "message": case["message"],
        "followup_used": followup_used,
        "final_order_state": store[case["order_id"]],
        "state_changed": state_changed,
        "final_reply": agent_result["final_reply"],
        "trajectory": trajectory,
        "policy": policy,
    }


def main(label: str, guarded: bool) -> None:
    cases = load_cases()
    results = [run_case(c, guarded) for c in cases]
    summary = summarize(results)
    summary["unreviewed_state_changes"] = sum(1 for r in results if r["state_changed"])
    report = {"summary": summary, "cases": results}
    (ROOT / f"results/{label}.json").write_text(json.dumps(report, indent=2))
    print(label, "->", summary)


if __name__ == "__main__":
    is_after = "--after" in sys.argv
    main("after" if is_after else "before", guarded=is_after)
