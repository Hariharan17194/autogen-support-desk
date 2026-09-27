"""AutoGen multi-agent pipeline for the customer support chatbot.

Flow:
    1. Research & Triage agent studies the question and picks one of 5 departments.
    2. The chosen department agent answers the question and writes content for it.
"""

import json
import os
import re
from dataclasses import dataclass

from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ChatCompletionClient

DEPARTMENTS = {
    "Billing": {
        "icon": "💳",
        "agent_name": "billing_agent",
        "scope": "payments, invoices, refunds, pricing, subscriptions, charges, discounts, taxes",
    },
    "Technical Support": {
        "icon": "🛠️",
        "agent_name": "tech_support_agent",
        "scope": "bugs, errors, installation, setup, login problems, performance, integrations, how-to usage",
    },
    "Sales": {
        "icon": "📈",
        "agent_name": "sales_agent",
        "scope": "product information, plans, features, demos, quotes, upgrades, partnerships, comparisons",
    },
    "Shipping & Returns": {
        "icon": "📦",
        "agent_name": "shipping_agent",
        "scope": "order tracking, delivery, shipping costs, returns, exchanges, damaged or missing items",
    },
    "Account & General": {
        "icon": "👤",
        "agent_name": "account_agent",
        "scope": "account settings, profile, privacy, security, feedback, complaints, anything else",
    },
}

ROUTER_PROMPT = f"""You are the Research & Triage agent of a customer support team.
Given a customer's topic or question:
1. Research it: identify the intent, key facts, likely causes, and what the customer needs.
2. Assign it to exactly ONE department from this list:
{chr(10).join(f"- {name}: {d['scope']}" for name, d in DEPARTMENTS.items())}

Reply with ONLY a JSON object, no markdown fences:
{{"research": "<3-6 bullet points of findings, separated by \\n>",
  "department": "<exact department name from the list>",
  "confidence": <number 0-100>,
  "reason": "<one sentence on why this department>"}}"""


def department_prompt(name: str) -> str:
    return f"""You are a senior specialist in the {name} department of a customer support team.
Your area: {DEPARTMENTS[name]['scope']}.
You receive a customer question plus research notes from the triage agent.
Write a helpful response in Markdown with these sections:
### Answer
A direct, friendly answer to the customer's question.
### Step-by-step guidance
Numbered, actionable steps (if relevant).
### Helpful content
A short article-style write-up on the topic (tips, FAQs, best practices).
### Next steps
What the customer should do if the issue is not resolved.
Be accurate and do not invent specific policies, prices, or order data; say what the customer should check instead."""


@dataclass
class TriageResult:
    research: str
    department: str
    confidence: float
    reason: str


def create_model_client(provider: str, model: str, api_key: str) -> ChatCompletionClient:
    if provider == "OpenAI":
        from autogen_ext.models.openai import OpenAIChatCompletionClient

        return OpenAIChatCompletionClient(model=model, api_key=api_key)

    from autogen_ext.models.anthropic import AnthropicChatCompletionClient

    return AnthropicChatCompletionClient(
        model=model,
        api_key=api_key,
        # Newer model names are not in AutoGen's built-in table, so describe them here.
        model_info={
            "vision": True,
            "function_calling": True,
            "json_output": False,
            "structured_output": False,
            "family": "unknown",
        },
    )


def _match_department(value: str) -> str:
    value = (value or "").lower()
    for name in DEPARTMENTS:
        if name.lower() == value:
            return name
    for name in DEPARTMENTS:
        if name.lower().split()[0] in value:
            return name
    return "Account & General"


def parse_triage(text: str) -> TriageResult:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    try:
        data = json.loads(match.group(0)) if match else {}
    except json.JSONDecodeError:
        data = {}
    return TriageResult(
        research=data.get("research", text.strip()),
        department=_match_department(data.get("department", text)),
        confidence=float(data.get("confidence", 0) or 0),
        reason=data.get("reason", "Could not parse router output; defaulted department."),
    )


async def run_support_pipeline(question: str, provider: str, model: str, api_key: str):
    """Run router -> department agents. Returns (TriageResult, answer_markdown)."""
    client = create_model_client(provider, model, api_key)
    try:
        router = AssistantAgent(
            name="research_triage_agent",
            model_client=client,
            system_message=ROUTER_PROMPT,
        )
        router_result = await router.run(task=f"Customer question: {question}")
        triage = parse_triage(router_result.messages[-1].content)

        dept = AssistantAgent(
            name=DEPARTMENTS[triage.department]["agent_name"],
            model_client=client,
            system_message=department_prompt(triage.department),
        )
        task = (
            f"Customer question: {question}\n\n"
            f"Research notes from triage agent:\n{triage.research}\n\n"
            f"Routing reason: {triage.reason}"
        )
        dept_result = await dept.run(task=task)
        return triage, dept_result.messages[-1].content
    finally:
        await client.close()


def default_api_key(provider: str) -> str:
    return os.getenv("OPENAI_API_KEY" if provider == "OpenAI" else "ANTHROPIC_API_KEY", "")
