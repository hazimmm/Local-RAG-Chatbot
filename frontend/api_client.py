import json
import os
from collections.abc import Iterator

import httpx

API_URL = os.environ.get("API_URL", "http://localhost:8000")


class ApiError(Exception):
    pass


def _check(resp: httpx.Response) -> httpx.Response:
    if resp.is_success:
        return resp
    try:
        detail = resp.json().get("detail", resp.text)
    except ValueError:
        detail = resp.text
    raise ApiError(f"{resp.status_code}: {detail}")


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _request(method: str, path: str, token: str | None = None, **kw):
    kw.setdefault("timeout", 600)
    headers = _headers(token) if token else {}
    try:
        return _check(
            httpx.request(method, f"{API_URL}{path}", headers=headers, **kw)
        )
    except httpx.ConnectError:
        raise ApiError(f"Cannot reach the API at {API_URL}. Is it running?")


def login(username: str, password: str) -> dict:
    body = {"username": username, "password": password}
    return _request("POST", "/auth/login", json=body).json()


def me(token: str) -> dict:
    return _request("GET", "/auth/me", token).json()


def list_documents(token: str) -> list[dict]:
    return _request("GET", "/admin/documents", token).json()


def upload_document(token: str, filename: str, data: bytes) -> dict:
    files = {"file": (filename, data)}
    return _request("POST", "/admin/documents", token, files=files).json()


def delete_document(token: str, doc_id: str) -> None:
    _request("DELETE", f"/admin/documents/{doc_id}", token)


def chat_stream(
    token: str, question: str, session_id: str | None = None
) -> Iterator[dict]:
    body = {"question": question, "session_id": session_id}
    try:
        with httpx.stream(
            "POST",
            f"{API_URL}/chat",
            json=body,
            headers=_headers(token),
            timeout=600,
        ) as resp:
            if not resp.is_success:
                resp.read()
                _check(resp)
            for line in resp.iter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    yield json.loads(line[6:])
    except httpx.ConnectError:
        raise ApiError(f"Cannot reach the API at {API_URL}. Is it running?")


def list_sessions(token: str) -> list[dict]:
    return _request("GET", "/sessions", token).json()


def get_session(token: str, session_id: str) -> dict:
    return _request("GET", f"/sessions/{session_id}", token).json()
