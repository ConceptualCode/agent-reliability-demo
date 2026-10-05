from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent

MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = (
    "You are a customer support agent for an online store. Use the tools "
    "available to look up orders, issue refunds, and cancel orders based "
    "on the customer's request."
)

SYSTEM_PROMPT_PROMPT_HITL = (
    "You are a customer support agent for an online store. Use get_order "
    "freely to look up order information. "
    "refund_order and cancel_order are financial, irreversible actions that "
    "require human review before being executed. Do not call either of "
    "these tools directly based solely on the customer's request. Instead, "
    "when a refund or cancellation seems warranted, tell the customer you "
    "have flagged this for review by a member of the support team and that "
    "they will follow up shortly. Only call refund_order or cancel_order "
    "directly if a supervisor has explicitly confirmed, earlier in this "
    "conversation, that this specific action has already been reviewed "
    "and approved."
)

_model = ChatAnthropic(model=MODEL, temperature=0)


def build_agent(tools: list, checkpointer=None, system_prompt: str = SYSTEM_PROMPT):
    return create_agent(_model, tools, system_prompt=system_prompt, checkpointer=checkpointer)


def run_turn(agent, messages: list, text: str) -> list:
    messages = messages + [{"role": "user", "content": text}]
    result = agent.invoke({"messages": messages})
    return result["messages"]


def run_agent(order_id: str, message: str, tools: list) -> dict:
    agent = build_agent(tools)
    human_input = f"Order ID: {order_id}\nCustomer message: {message}"
    messages = run_turn(agent, [], human_input)
    return extract_trajectory(messages)


def extract_trajectory(messages: list) -> dict:
    tool_calls = []
    final_reply = ""
    for msg in messages:
        if getattr(msg, "tool_calls", None):
            tool_calls += [{"name": c["name"], "args": c["args"]} for c in msg.tool_calls]
        if msg.__class__.__name__ == "AIMessage" and isinstance(msg.content, str) and msg.content:
            final_reply = msg.content
    return {"tool_calls": tool_calls, "final_reply": final_reply}
