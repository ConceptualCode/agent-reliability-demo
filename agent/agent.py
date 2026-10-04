from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent

MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = (
    "You are a customer support agent for an online store. Use the tools "
    "available to look up orders, issue refunds, and cancel orders based "
    "on the customer's request."
)

_model = ChatAnthropic(model=MODEL, temperature=0)


def build_agent(tools: list):
    return create_agent(_model, tools, system_prompt=SYSTEM_PROMPT)


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
