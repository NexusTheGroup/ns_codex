from __future__ import annotations

import json
from datetime import datetime
from html import escape
from typing import Callable, Dict, Iterable
from urllib.parse import parse_qs

from .db import Database

HTML_BASE = """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>{title}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; background: #f9fafb; color: #1f2933; }}
    header {{ margin-bottom: 2rem; }}
    form.search {{ margin-bottom: 1.5rem; }}
    input[type=text] {{ padding: 0.5rem; width: 60%; max-width: 420px; }}
    button {{ padding: 0.5rem 1rem; }}
    .thread-card {{ background: #fff; border-radius: 0.75rem; box-shadow: 0 4px 12px rgba(15,23,42,0.08); padding: 1.5rem; margin-bottom: 1rem; }}
    .thread-card h2 {{ margin-top: 0; }}
    .meta {{ font-size: 0.85rem; color: #617086; margin-bottom: 0.5rem; }}
    .message {{ border-left: 3px solid #2563eb; padding-left: 1rem; margin-bottom: 1rem; background: #f1f5f9; border-radius: 0.5rem; padding-top: 0.75rem; padding-bottom: 0.75rem; }}
    .message.user {{ border-left-color: #2563eb; }}
    .message.assistant {{ border-left-color: #0ea5e9; background: #eff6ff; }}
    .attachments {{ margin-top: 0.5rem; font-size: 0.85rem; color: #334155; }}
    .empty {{ text-align: center; color: #9aa5b1; margin-top: 3rem; }}
    a {{ color: #2563eb; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
<header>
  <h1>{heading}</h1>
</header>
{body}
</body>
</html>"""


def create_app(database: Database) -> Callable:
    def app(environ, start_response):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "") or "/"
        if method != "GET":
            return _response(start_response, "405 Method Not Allowed", {"Content-Type": "text/plain"}, b"method not allowed")
        if path == "/":
            return _handle_home(database, environ, start_response)
        if path.startswith("/thread/"):
            thread_id = path.split("/", 2)[2]
            return _handle_thread(database, thread_id, start_response)
        if path == "/api/threads":
            return _handle_api_threads(database, environ, start_response)
        if path.startswith("/api/threads/"):
            thread_id = path.split("/", 3)[3]
            return _handle_api_thread(database, thread_id, start_response)
        if path == "/healthz":
            try:
                database.health_check()
            except Exception:  # pragma: no cover - defensive
                return _response(start_response, "503 Service Unavailable", {"Content-Type": "text/plain"}, b"unhealthy")
            return _response(start_response, "200 OK", {"Content-Type": "text/plain"}, b"ok")
        return _response(start_response, "404 Not Found", {"Content-Type": "text/plain"}, b"not found")

    return app


def _handle_home(database: Database, environ, start_response):
    params = parse_qs(environ.get("QUERY_STRING", ""))
    query = params.get("q", [""])[0].strip()
    threads = database.search_threads(query or None, limit=20)
    cards = "".join(_render_thread_card(thread) for thread in threads)
    if not cards:
        cards = '<div class="empty">No conversations yet. Import a ChatGPT or Claude export to get started.</div>'
    body = f"""
    <form class=\"search\" action=\"/\" method=\"get\">
      <input type=\"text\" name=\"q\" value=\"{escape(query)}\" placeholder=\"Search conversations...\">
      <button type=\"submit\">Search</button>
    </form>
    {cards}
    """
    html = HTML_BASE.format(title="ns_codex", heading="Conversation Library", body=body)
    return _response(start_response, "200 OK", {"Content-Type": "text/html; charset=utf-8"}, html.encode("utf-8"))


def _handle_thread(database: Database, thread_id: str, start_response):
    data = database.get_thread(thread_id)
    if not data:
        return _response(start_response, "404 Not Found", {"Content-Type": "text/plain"}, b"thread not found")
    messages_html = "".join(_render_message(message) for message in data["messages"])
    meta = f"Platform: {escape(data['platform'])} · Messages: {data['message_count']} · Tokens: {data['total_tokens']}"
    body = f"""
    <div class=\"thread-card\">
      <div class=\"meta\">{meta}</div>
      <h2>{escape(data['title'] or 'Untitled conversation')}</h2>
      {messages_html}
      <p><a href=\"/\">← Back to search</a></p>
    </div>
    """
    html = HTML_BASE.format(title=data.get("title") or "Conversation", heading="Conversation Detail", body=body)
    return _response(start_response, "200 OK", {"Content-Type": "text/html; charset=utf-8"}, html.encode("utf-8"))


def _handle_api_threads(database: Database, environ, start_response):
    params = parse_qs(environ.get("QUERY_STRING", ""))
    query = params.get("q", [""])[0].strip()
    try:
        limit = int(params.get("limit", ["20"])[0])
    except ValueError:
        limit = 20
    threads = database.search_threads(query or None, limit=max(1, min(limit, 100)))
    body = json.dumps(threads).encode("utf-8")
    return _response(start_response, "200 OK", {"Content-Type": "application/json"}, body)


def _handle_api_thread(database: Database, thread_id: str, start_response):
    data = database.get_thread(thread_id)
    if not data:
        return _response(start_response, "404 Not Found", {"Content-Type": "application/json"}, b"{}")
    body = json.dumps(data).encode("utf-8")
    return _response(start_response, "200 OK", {"Content-Type": "application/json"}, body)


def _render_thread_card(thread: Dict[str, object]) -> str:
    updated_at = thread.get("updated_at")
    if isinstance(updated_at, str):
        try:
            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            updated_str = dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            updated_str = updated_at
    else:
        updated_str = ""
    preview = escape((thread.get("preview") or "")[:220])
    return f"""
    <div class=\"thread-card\">
      <div class=\"meta\">{escape(thread.get('platform', ''))} · Updated {escape(updated_str)}</div>
      <h2><a href=\"/thread/{escape(str(thread.get('id', '')))}\">{escape(thread.get('title') or 'Untitled conversation')}</a></h2>
      <p>{preview}</p>
    </div>
    """


def _render_message(message: Dict[str, object]) -> str:
    role = escape(message.get("role", "").lower())
    content = escape(message.get("content", ""))
    timestamp = message.get("timestamp")
    ts_display = ""
    if isinstance(timestamp, str) and timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            ts_display = dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            ts_display = timestamp
    attachments_html = ""
    attachments = message.get("attachments") or []
    if attachments:
        rows = []
        for attachment in attachments:
            filename = escape(str(attachment.get("filename", "attachment")))
            mime_type = escape(str(attachment.get("mime_type", "")))
            rows.append(f"<li>{filename} <span style=\"color:#94a3b8\">({mime_type})</span></li>")
        attachments_html = f"<div class=\"attachments\"><strong>Attachments</strong><ul>{''.join(rows)}</ul></div>"
    return f"""
    <div class=\"message {role}\">
      <div><strong>{role.capitalize()}</strong> {escape(ts_display)}</div>
      <div>{content}</div>
      {attachments_html}
    </div>
    """


def _response(start_response, status: str, headers: Dict[str, str], body: bytes):
    headers_list = [(key, value) for key, value in headers.items()]
    headers_list.append(("Content-Length", str(len(body))))
    start_response(status, headers_list)
    return [body]


__all__ = ["create_app"]
