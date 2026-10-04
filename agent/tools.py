from langchain_core.tools import tool


def make_tools(store: dict) -> list:
    @tool
    def get_order(order_id: str) -> dict:
        """Look up an order's status, item, and amount paid."""
        order = store.get(order_id)
        if order is None:
            return {"success": False, "error": "order_not_found"}
        return {"success": True, **order}

    @tool
    def refund_order(order_id: str, amount: float) -> dict:
        """Issue a refund for an order."""
        order = store.get(order_id)
        if order is None:
            return {"success": False, "error": "order_not_found"}
        order["status"] = "refunded"
        return {"success": True, "order_id": order_id, "refunded_amount": amount}

    @tool
    def cancel_order(order_id: str) -> dict:
        """Cancel an order."""
        order = store.get(order_id)
        if order is None:
            return {"success": False, "error": "order_not_found"}
        order["status"] = "cancelled"
        return {"success": True, "order_id": order_id}

    return [get_order, refund_order, cancel_order]
