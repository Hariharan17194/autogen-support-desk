# 🎧 Multi-Agent Customer Support Chatbot (AutoGen + Streamlit)

A customer support chatbot built with Microsoft **AutoGen** (`autogen-agentchat` 0.4+) and a **Streamlit** chat UI.
A user asks any question or enters a topic. A research agent studies it and sends it to the right department, and that department's specialist agent writes the answer.

## How it works

```
User question
     │
     ▼
🔍 Research & Triage agent  ── researches the question, picks 1 of 5 departments
     │                          (returns research notes, department, confidence, reason)
     ▼
🏢 Department specialist agent ── answers the question and writes helpful content
     │
     ▼
Streamlit chat UI (routing badge + research panel + final answer)
```

### Departments

| Department | Handles |
|---|---|
| 💳 Billing | payments, invoices, refunds, pricing, subscriptions |
| 🛠️ Technical Support | bugs, errors, setup, login problems, integrations |
| 📈 Sales | product info, plans, features, demos, upgrades |
| 📦 Shipping & Returns | order tracking, delivery, returns, exchanges |
| 👤 Account & General | account settings, privacy, security, feedback, anything else |

Each department reply has four sections: **Answer**, **Step-by-step guidance**, **Helpful content** and **Next steps**.

## Features

- Two-stage AutoGen agent pipeline: triage, then a department specialist
- Works with **OpenAI** (`gpt-4o-mini`, `gpt-4o`) or **Anthropic** (Claude) models, chosen in the sidebar
- Shows which department was picked, the confidence score, and the research notes behind the choice
- Chat history kept for the session, plus a clear-chat button
- If the triage agent's reply can't be read, the question goes to **Account & General**

## Setup

```bash
git clone <this-repo-url>
cd <repo-folder>
pip install -r requirements.txt
cp .env.example .env      # then add OPENAI_API_KEY and/or ANTHROPIC_API_KEY
streamlit run app.py
```

You can also paste the API key into the sidebar instead of using `.env`.

## Project structure

| File | Purpose |
|---|---|
| `agents.py` | Department list, agent instructions, model setup and the AutoGen pipeline |
| `app.py` | Streamlit chat interface |
| `requirements.txt` | Python dependencies |
| `.env.example` | API key template |

## Example questions

- *I was charged twice for my subscription this month. How do I get a refund?* → Billing
- *The app crashes when I upload a file larger than 10 MB.* → Technical Support
- *What's the difference between your Basic and Pro plans?* → Sales
- *My order hasn't arrived after 10 days. How can I track it?* → Shipping & Returns
- *How do I turn on two-factor authentication?* → Account & General

## Customizing

To add, remove or rename departments, edit the `DEPARTMENTS` list at the top of `agents.py`. The triage agent's instructions and the sidebar update automatically.
