import asyncio

import streamlit as st
from dotenv import load_dotenv

from agents import DEPARTMENTS, default_api_key, run_support_pipeline

load_dotenv()

MODELS = {
    "OpenAI": ["gpt-4o-mini", "gpt-4o"],
    "Anthropic": ["claude-sonnet-5", "claude-haiku-4-5-20251001", "claude-opus-5-5"],
}

st.set_page_config(page_title="Customer Support AI", page_icon="🎧", layout="wide")

with st.sidebar:
    st.header("⚙️ Settings")
    provider = st.selectbox("Model provider", list(MODELS))
    model = st.selectbox("Model", MODELS[provider])
    api_key = st.text_input("API key", value=default_api_key(provider), type="password")
    st.divider()
    st.subheader("🏢 Departments")
    for name, d in DEPARTMENTS.items():
        st.markdown(f"{d['icon']} **{name}**  \n<small>{d['scope']}</small>", unsafe_allow_html=True)
    if st.button("🗑️ Clear chat"):
        st.session_state.history = []
        st.rerun()

st.title("🎧 Customer Support Chatbot")
st.caption("AutoGen multi-agent: Research & Triage agent ➜ Department specialist agent")

if "history" not in st.session_state:
    st.session_state.history = []


def render_reply(item):
    icon = DEPARTMENTS[item["department"]]["icon"]
    st.success(f"Routed to **{icon} {item['department']}** ({item['confidence']:.0f}% confidence)")
    with st.expander("🔍 Research & Triage agent findings"):
        st.markdown(item["research"])
        st.markdown(f"**Reason:** {item['reason']}")
    st.markdown(item["answer"])


for item in st.session_state.history:
    with st.chat_message("user"):
        st.markdown(item["question"])
    with st.chat_message("assistant"):
        render_reply(item)

question = st.chat_input("Ask any question or enter a topic…")
if question:
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        if not api_key:
            st.error(f"Please enter your {provider} API key in the sidebar.")
            st.stop()
        with st.status("Agents are working…", expanded=True) as status:
            st.write("🔍 Research & Triage agent is analysing the question…")
            try:
                triage, answer = asyncio.run(run_support_pipeline(question, provider, model, api_key))
            except Exception as e:
                status.update(label="Failed", state="error")
                st.error(f"Error: {e}")
                st.stop()
            st.write(f"➡️ Routed to {triage.department}; specialist wrote the answer.")
            status.update(label="Done", state="complete", expanded=False)
        item = {
            "question": question,
            "department": triage.department,
            "confidence": triage.confidence,
            "research": triage.research,
            "reason": triage.reason,
            "answer": answer,
        }
        st.session_state.history.append(item)
        render_reply(item)
