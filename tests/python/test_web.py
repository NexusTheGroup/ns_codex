from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"

import io
import json

from ns_codex.ingest import ingest_file
from ns_codex.web import create_app


def _call(app, path, query=""):
    status_headers = {}
    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": path,
        "QUERY_STRING": query,
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "8000",
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": "http",
        "wsgi.input": io.BytesIO(b""),
        "wsgi.errors": io.StringIO(),
        "wsgi.multithread": False,
        "wsgi.multiprocess": False,
        "wsgi.run_once": False,
    }

    def start_response(status, headers):
        status_headers["status"] = status
        status_headers["headers"] = headers

    body = b"".join(app(environ, start_response))
    headers_dict = {key: value for key, value in status_headers.get("headers", [])}
    return status_headers.get("status"), headers_dict, body


def _seed(db):
    ingest_file(db, "chatgpt", FIXTURES / "chatgpt_conversations.json")
    ingest_file(db, "claude", FIXTURES / "claude_conversations.jsonl")


def test_root_page_lists_threads(db):
    _seed(db)
    app = create_app(db)
    status, headers, body = _call(app, "/")
    assert status.startswith("200")
    html = body.decode("utf-8")
    assert "Planning session" in html


def test_api_thread_detail(db):
    _seed(db)
    app = create_app(db)
    thread_id = db.search_threads(None, limit=1)[0]["id"]
    status, headers, body = _call(app, f"/api/threads/{thread_id}")
    assert status.startswith("200")
    data = json.loads(body.decode("utf-8"))
    assert data["message_count"] >= 2


def test_api_search_threads(db):
    _seed(db)
    app = create_app(db)
    status, headers, body = _call(app, "/api/threads", "q=checklist")
    assert status.startswith("200")
    data = json.loads(body.decode("utf-8"))
    assert any(row["title"] == "Planning session" for row in data)
