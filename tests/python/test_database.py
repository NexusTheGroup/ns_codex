from datetime import datetime, timezone
from pathlib import Path

from ns_codex.db import Database
from ns_codex.types import AttachmentData, MessageData, ThreadBundle


def _bundle() -> ThreadBundle:
    messages = [
        MessageData(
            role="user",
            content="Hello there",
            timestamp=datetime(2024, 3, 10, 10, 0, tzinfo=timezone.utc),
        ),
        MessageData(
            role="assistant",
            content="General Kenobi",
            timestamp=datetime(2024, 3, 10, 10, 1, tzinfo=timezone.utc),
            attachments=[
                AttachmentData(
                    filename="plan.txt",
                    mime_type="text/plain",
                    extracted_text="It worked",
                )
            ],
        ),
    ]
    bundle = ThreadBundle(
        external_id="thread-1",
        title="Greeting",
        created_at=datetime(2024, 3, 10, 10, 0, tzinfo=timezone.utc),
        updated_at=datetime(2024, 3, 10, 10, 1, tzinfo=timezone.utc),
        messages=messages,
    )
    bundle.compute_checksum()
    return bundle


def test_schema_installs(db: Database):
    tables = {
        row[0]
        for row in db._conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert {"platforms", "threads", "messages", "attachments"}.issubset(tables)


def test_store_and_fetch_thread(db: Database):
    bundle = _bundle()
    result = db.ingest_threads("chatgpt", [bundle], Path("export.json"), bundle.checksum or "abc")
    assert result["inserted"] == 1
    threads = db.search_threads(None, limit=5)
    assert len(threads) == 1
    thread_id = threads[0]["id"]
    fetched = db.get_thread(thread_id)
    assert fetched
    assert fetched["message_count"] == 2
    assert fetched["total_tokens"] > 0
    assert fetched["messages"][1]["attachments"][0]["filename"] == "plan.txt"


def test_search_threads(db: Database):
    bundle = _bundle()
    db.ingest_threads("chatgpt", [bundle], Path("export.json"), bundle.checksum or "abc")
    results = db.search_threads("general", limit=5)
    assert len(results) == 1
    assert "General" in results[0]["preview"]
