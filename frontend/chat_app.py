import re
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from frontend import api_client as api  # noqa: E402
from frontend.styles import inject  # noqa: E402

st.set_page_config(page_title="Knowledge Assistant", page_icon="💬")
inject()

REFUSAL_PREFIX = "I don't know based on"


def init_state() -> None:
    st.session_state.setdefault("session_id", None)
    st.session_state.setdefault("messages", [])


def show_login() -> None:
    st.markdown("<h1 class='login-title'>💬 Knowledge Assistant</h1>",
                unsafe_allow_html=True)
    st.markdown("<p class='login-sub'>Ask questions about your company "
                "documents</p>", unsafe_allow_html=True)
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button(
            "Sign in", type="primary", use_container_width=True
        )
    if submitted:
        try:
            result = api.login(username, password)
        except api.ApiError as exc:
            st.error(str(exc))
            return
        st.session_state.token = result["access_token"]
        st.session_state.username = username
        st.rerun()


def sign_out_on_401(exc: api.ApiError) -> None:
    if str(exc).startswith("401"):
        st.session_state.clear()
        st.rerun()


def open_session(session_id: str) -> None:
    try:
        data = api.get_session(st.session_state.token, session_id)
    except api.ApiError as exc:
        sign_out_on_401(exc)
        st.error(str(exc))
        return
    st.session_state.session_id = session_id
    st.session_state.messages = data["messages"]


def new_chat() -> None:
    st.session_state.session_id = None
    st.session_state.messages = []


def show_sidebar() -> None:
    with st.sidebar:
        st.markdown("### 💬 Knowledge Assistant")
        if st.button("＋ New chat", use_container_width=True, type="primary"):
            new_chat()
            st.rerun()
        st.markdown("<span class='muted'>Recent chats</span>",
                    unsafe_allow_html=True)
        try:
            sessions = api.list_sessions(st.session_state.token)
        except api.ApiError as exc:
            sign_out_on_401(exc)
            st.error(str(exc))
            sessions = []
        if not sessions:
            st.caption("No chats yet.")
        for s in sessions[:20]:
            current = s["id"] == st.session_state.session_id
            label = s["title"] if len(s["title"]) < 32 else s["title"][:30] + "…"
            if st.button(label, key=f"s_{s['id']}", use_container_width=True,
                         type="secondary", disabled=current):
                open_session(s["id"])
                st.rerun()
        st.divider()
        st.caption(f"Signed in as **{st.session_state.username}**")
        if st.button("Sign out", use_container_width=True):
            st.session_state.clear()
            st.rerun()


def cited_sources(answer: str, sources: list[dict]) -> list[dict]:
    if answer.strip().startswith(REFUSAL_PREFIX):
        return []
    cited = {int(n) for n in re.findall(r"\[(\d+)\]", answer)}
    picked = [s for i, s in enumerate(sources, start=1) if i in cited]
    return picked or sources[:1]


def render_sources(answer: str, sources: list[dict]) -> None:
    shown = cited_sources(answer, sources)
    if not shown:
        return
    with st.expander(f"📄 Sources ({len(shown)})"):
        for s in shown:
            st.markdown(f"**{s['heading']}**")
            st.caption(s["text"][:300] + ("…" if len(s["text"]) > 300 else ""))


def render_history() -> None:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m["role"] == "assistant":
                render_sources(m["content"], m.get("sources", []))


def answer_question(question: str) -> None:
    st.session_state.messages.append(
        {"role": "user", "content": question, "sources": []}
    )
    with st.chat_message("user"):
        st.markdown(question)

    captured = {"sources": []}
    with st.chat_message("assistant"):
        waiting = st.empty()
        waiting.caption("🔎 Searching the knowledge base…")

        def tokens():
            for event in api.chat_stream(
                st.session_state.token, question, st.session_state.session_id
            ):
                if event["type"] == "meta":
                    st.session_state.session_id = event["session_id"]
                elif event["type"] == "sources":
                    captured["sources"] = event["sources"]
                    waiting.caption("✍️ Writing the answer…")
                elif event["type"] == "token":
                    waiting.empty()
                    yield event["token"]

        try:
            answer = st.write_stream(tokens())
        except api.ApiError as exc:
            waiting.empty()
            sign_out_on_401(exc)
            st.error(str(exc))
            st.session_state.messages.pop()
            return
        render_sources(answer, captured["sources"])

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": captured["sources"]}
    )
    st.rerun()


def show_app() -> None:
    show_sidebar()
    if not st.session_state.messages:
        st.markdown("## How can I help you today?")
        st.caption("Answers come only from the documents your administrators "
                   "have uploaded, with sources shown under each reply.")
    render_history()
    question = st.chat_input("Ask a question about the documents…")
    if question:
        answer_question(question)


init_state()
if "token" not in st.session_state:
    show_login()
else:
    show_app()
