"""Live demo of the real LangGraph interrupt() pause-and-resume mechanism.

Unlike the eval harness (which simulates "escalate" as a plain dict return so
23 cases can run unattended), this script wires make_guarded_tools(..., use_interrupt=True)
so the graph actually suspends mid-run at the policy checkpoint, and only
continues once a human decision is fed back in via Command(resume=...).
"""
import copy

from dotenv import load_dotenv

load_dotenv()

from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver

from data.orders import ORDERS
from agent.agent import build_agent, run_turn
from agent.guarded_tools import make_guarded_tools


def run_scenario(thread_id: str, order_id: str, message: str, resume_value: bool) -> None:
    store = copy.deepcopy(ORDERS)
    log: list = []
    tools = make_guarded_tools(store, log, use_interrupt=True)
    agent = build_agent(tools, checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": thread_id}}

    print(f"\n{'=' * 70}\nSCENARIO: {order_id} — \"{message}\"\n{'=' * 70}")
    print(f"Before: {store[order_id]}")

    human_input = f"Order ID: {order_id}\nCustomer message: {message}"
    result = agent.invoke({"messages": [{"role": "user", "content": human_input}]}, config=config)

    if "__interrupt__" not in result:
        print("No escalation triggered — nothing to pause on.")
        return

    pending = result["__interrupt__"][0].value
    print(f"\n>>> PAUSED — graph suspended, waiting for human review <<<")
    print(f"    Pending action: {pending['tool']}({pending['args']})")
    print(f"    Reason: {pending['reason']}")

    decision = "APPROVE" if resume_value else "DENY"
    print(f"\n>>> Human reviewer decision: {decision} — resuming graph <<<")
    result = agent.invoke(Command(resume=resume_value), config=config)

    final_reply = next(
        (m.content for m in reversed(result["messages"]) if m.__class__.__name__ == "AIMessage" and m.content),
        "",
    )
    print(f"\nAgent's final reply:\n{final_reply}")
    print(f"\nAfter:  {store[order_id]}")
    print(f"Policy decision: {log[-1]}")


if __name__ == "__main__":
    run_scenario(
        thread_id="demo-approve",
        order_id="ORD-1002",
        message="The package arrived damaged, I don't want it anymore, can you take care of it?",
        resume_value=True,
    )
    run_scenario(
        thread_id="demo-deny",
        order_id="ORD-1003",
        message="Please cancel my order.",
        resume_value=False,
    )
