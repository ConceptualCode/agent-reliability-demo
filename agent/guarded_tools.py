from langchain_core.tools import tool
from agent.tools import make_tools
from agent.policy import check_policy


def make_guarded_tools(store: dict, log: list) -> list:
    get_order, refund_order, cancel_order = make_tools(store)

    def guard(name: str, raw_tool, args: dict) -> dict:
        decision = check_policy(name, args, store)
        log.append({"tool": name, "args": args, "outcome": decision["outcome"]})
        if decision["outcome"] == "auto_block":
            return {"success": False, "error": decision["reason"]}
        if decision["outcome"] == "escalate":
            return {"success": False, "pending_human_review": True}
        return raw_tool.invoke(args)

    @tool("refund_order")
    def guarded_refund_order(order_id: str, amount: float) -> dict:
        """Issue a refund for an order."""
        return guard("refund_order", refund_order, {"order_id": order_id, "amount": amount})

    @tool("cancel_order")
    def guarded_cancel_order(order_id: str) -> dict:
        """Cancel an order."""
        return guard("cancel_order", cancel_order, {"order_id": order_id})

    return [get_order, guarded_refund_order, guarded_cancel_order]
