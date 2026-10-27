import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from frontend import api_client as api  # noqa: E402
from frontend.styles import inject  # noqa: E402

st.set_page_config(page_title="RAG Admin", page_icon="📚", layout="wide")
inject()

STATUS_BADGE = {
    "ready": ("Ready", "green"),
    "processing": ("Processing", "orange"),
    "failed": ("Failed", "red"),
}
ALLOWED_TYPES = ["pdf", "docx", "pptx", "xlsx", "html", "txt", "md", "csv"]


def show_login() -> None:
    _, middle, _ = st.columns([1, 1.2, 1])
    with middle:
        st.markdown("<h1 class='login-title'>📚 Knowledge Base Admin</h1>",
                    unsafe_allow_html=True)
        st.markdown("<p class='login-sub'>Sign in to manage documents</p>",
                    unsafe_allow_html=True)
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
            if result["role"] != "admin":
                st.error("This portal is for administrators only.")
                return
            st.session_state.token = result["access_token"]
            st.session_state.username = username
            st.rerun()


def show_sidebar() -> None:
    with st.sidebar:
        st.markdown("### 📚 RAG Admin")
        st.caption(f"Signed in as **{st.session_state.username}**")
        if st.button("Sign out", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        st.divider()
        st.caption("Upload files of any supported type. They are converted "
                   "to Markdown, split into chunks and indexed for search.")


def show_metrics(docs: list[dict]) -> None:
    ready = [d for d in docs if d["status"] == "ready"]
    failed = [d for d in docs if d["status"] == "failed"]
    cols = st.columns(4)
    cols[0].metric("Documents", len(docs))
    cols[1].metric("Ready", len(ready))
    cols[2].metric("Failed", len(failed))
    cols[3].metric("Indexed chunks", sum(d["chunk_count"] for d in ready))


@st.dialog("Delete document?")
def confirm_delete(doc: dict) -> None:
    st.write(f"**{doc['filename']}** and all its indexed chunks will be "
             "removed. This cannot be undone.")
    left, right = st.columns(2)
    if left.button("Cancel", use_container_width=True):
        st.rerun()
    if right.button("Delete", type="primary", use_container_width=True):
        try:
            api.delete_document(st.session_state.token, doc["id"])
        except api.ApiError as exc:
            st.error(str(exc))
            return
        st.toast(f"Deleted {doc['filename']}", icon="🗑️")
        st.rerun()


def show_documents(docs: list[dict]) -> None:
    if not docs:
        st.info("No documents yet. Use the **Upload** tab to add your first "
                "file.")
        return
    header = st.columns([4, 1.4, 1.2, 2, 0.8])
    for col, text in zip(header, ["File", "Status", "Chunks", "Uploaded", ""]):
        col.markdown(f"<span class='muted'>{text}</span>",
                     unsafe_allow_html=True)
    for doc in docs:
        label, color = STATUS_BADGE.get(doc["status"], (doc["status"], "gray"))
        uploaded = datetime.fromisoformat(doc["uploaded_at"])
        with st.container(border=True):
            c = st.columns([4, 1.4, 1.2, 2, 0.8], vertical_alignment="center")
            c[0].markdown(f"<span class='doc-name'>{doc['filename']}</span>",
                          unsafe_allow_html=True)
            c[1].badge(label, color=color)
            c[2].write(doc["chunk_count"])
            c[3].write(uploaded.strftime("%d %b %Y, %H:%M"))
            if c[4].button("🗑️", key=f"del_{doc['id']}", help="Delete"):
                confirm_delete(doc)
            if doc["error"]:
                st.caption(f"⚠️ {doc['error']}")


def show_upload() -> None:
    files = st.file_uploader(
        "Drop files here",
        type=ALLOWED_TYPES,
        accept_multiple_files=True,
        help="Re-uploading a changed file replaces the old version. "
             "Identical files are skipped.",
    )
    for kind, text in st.session_state.pop("upload_msgs", []):
        {"ok": st.success, "warn": st.warning, "err": st.error}[kind](text)

    if st.button("Upload & index", type="primary", disabled=not files):
        messages = []
        progress = st.progress(0.0)
        for i, f in enumerate(files):
            with st.spinner(f"Processing {f.name}…"):
                try:
                    result = api.upload_document(
                        st.session_state.token, f.name, f.getvalue()
                    )
                except api.ApiError as exc:
                    messages.append(("err", f"{f.name}: {exc}"))
                    continue
                finally:
                    progress.progress((i + 1) / len(files))
            doc = result["document"]
            if doc["status"] == "failed":
                messages.append(("err", f"{f.name}: {doc['error']}"))
            elif result["result"] == "duplicate":
                messages.append(("warn", f"{f.name}: already uploaded, skipped"))
            else:
                verb = "Replaced" if result["result"] == "replaced" else "Added"
                messages.append(
                    ("ok", f"{verb} {f.name} ({doc['chunk_count']} chunks)")
                )
        st.session_state.upload_msgs = messages
        st.rerun()


def show_app() -> None:
    show_sidebar()
    st.title("Knowledge base")
    try:
        docs = api.list_documents(st.session_state.token)
    except api.ApiError as exc:
        if str(exc).startswith("401"):
            st.session_state.clear()
            st.rerun()
        st.error(str(exc))
        return
    show_metrics(docs)
    st.write("")
    docs_tab, upload_tab = st.tabs(["Documents", "Upload"])
    with docs_tab:
        show_documents(docs)
    with upload_tab:
        show_upload()


if "token" not in st.session_state:
    show_login()
else:
    show_app()
