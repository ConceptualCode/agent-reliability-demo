def check_policy(tool_name: str, args: dict, store: dict) -> dict:
    if tool_name == "get_order":
        return {"outcome": "auto_allow"}

    order = store.get(args.get("order_id"))
    if order is None:
        return {"outcome": "auto_block", "reason": "order_not_found"}

    if tool_name == "cancel_order":
        if order["status"] != "processing":
            return {"outcome": "auto_block", "reason": f"cannot_cancel_{order['status']}"}
        return {"outcome": "escalate"}

    if tool_name == "refund_order":
        if order["status"] == "refunded":
            return {"outcome": "auto_block", "reason": "already_refunded"}
        if args.get("amount", 0) > order["amount_paid"]:
            return {"outcome": "auto_block", "reason": "amount_exceeds_paid"}
        return {"outcome": "escalate"}

    return {"outcome": "auto_block", "reason": "unknown_tool"}
