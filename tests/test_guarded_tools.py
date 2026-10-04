import copy
from typing import Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from agent.guarded_tools import make_guarded_tools

STORE = {
    "PROCESSING": {"status": "processing", "amount_paid": 50.0},
    "SHIPPED": {"status": "shipped", "amount_paid": 50.0},
    "DELIVERED": {"status": "delivered", "amount_paid": 50.0},
}


def fresh_store():
    return copy.deepcopy(STORE)


def test_get_order_bypasses_the_guard_entirely():
    # get_order is a pure read, so make_guarded_tools returns it unwrapped
    # (straight from make_tools) rather than routing it through guard().
    store = fresh_store()
    log = []
    get_order, _, _ = make_guarded_tools(store, log)

    result = get_order.invoke({"order_id": "PROCESSING"})

    assert result["success"] is True
    assert log == []


def test_auto_block_prevents_mutation():
    store = fresh_store()
    log = []
    _, _, cancel_order = make_guarded_tools(store, log)

    result = cancel_order.invoke({"order_id": "SHIPPED"})

    assert result == {"success": False, "error": "cannot_cancel_shipped"}
    assert store["SHIPPED"]["status"] == "shipped"
    assert log[-1]["outcome"] == "auto_block"


def test_escalate_without_interrupt_prevents_mutation():
    store = fresh_store()
    log = []
    _, refund_order, _ = make_guarded_tools(store, log, use_interrupt=False)

    result = refund_order.invoke({"order_id": "DELIVERED", "amount": 50.0})

    assert result == {"success": False, "pending_human_review": True}
    assert store["DELIVERED"]["status"] == "delivered"
    assert log[-1]["outcome"] == "escalate"


def run_single_tool_graph(tool, args: dict, thread_id: str):
    """Wraps one tool call in a minimal graph so interrupt()/Command(resume=...)
    can be exercised deterministically, with no LLM or API call involved."""

    class State(TypedDict):
        result: Any

    def node(state):
        return {"result": tool.invoke(args)}

    graph = StateGraph(State)
    graph.add_node("call_tool", node)
    graph.add_edge(START, "call_tool")
    graph.add_edge("call_tool", END)
    compiled = graph.compile(checkpointer=MemorySaver())

    config = {"configurable": {"thread_id": thread_id}}
    paused = compiled.invoke({"result": None}, config=config)
    return compiled, config, paused


def test_escalate_with_interrupt_approved_allows_mutation():
    store = fresh_store()
    log = []
    _, refund_order, _ = make_guarded_tools(store, log, use_interrupt=True)

    compiled, config, paused = run_single_tool_graph(
        refund_order, {"order_id": "DELIVERED", "amount": 50.0}, "approve-thread"
    )
    assert "__interrupt__" in paused
    assert store["DELIVERED"]["status"] == "delivered"  # still unmutated while paused

    final = compiled.invoke(Command(resume=True), config=config)

    assert final["result"] == {"success": True, "order_id": "DELIVERED", "refunded_amount": 50.0}
    assert store["DELIVERED"]["status"] == "refunded"


def test_escalate_with_interrupt_denied_prevents_mutation():
    store = fresh_store()
    log = []
    _, refund_order, _ = make_guarded_tools(store, log, use_interrupt=True)

    compiled, config, paused = run_single_tool_graph(
        refund_order, {"order_id": "DELIVERED", "amount": 50.0}, "deny-thread"
    )
    assert "__interrupt__" in paused

    final = compiled.invoke(Command(resume=False), config=config)

    assert final["result"] == {"success": False, "error": "rejected_by_reviewer"}
    assert store["DELIVERED"]["status"] == "delivered"
