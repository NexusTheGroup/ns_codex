"""Tests for ingestion pipeline normalization and persistence."""

from __future__ import annotations

from pathlib import Path

import pytest

from chat_manager import AttachmentStorage, ChatDatabase
from chat_manager.ingest import ImportConfig, ImportPipeline

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def db(tmp_path: Path) -> ChatDatabase:
    database_path = tmp_path / "ingest.sqlite"
    db = ChatDatabase(database_path)
    db.initialize()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def storage(tmp_path: Path) -> AttachmentStorage:
    base = tmp_path / "attachments"
    return AttachmentStorage(base)



def test_chatgpt_ingest_creates_threads_and_attachments(db: ChatDatabase, storage: AttachmentStorage) -> None:
    pipeline = ImportPipeline(db, storage)
    chatgpt_path = FIXTURES / "chatgpt_sample.json"

    result = pipeline.ingest([chatgpt_path], ImportConfig())

    assert result.success
    assert result.files_processed == 1
    assert result.files_skipped == 0
    assert result.threads_created == 1
    assert result.messages_created == 2
    assert result.attachments_saved == 1

    cur = db.connection.execute("SELECT name FROM platforms")
    platforms = {row["name"] for row in cur.fetchall()}
    assert "ChatGPT" in platforms

    thread_row = db.connection.execute("SELECT message_count, total_tokens FROM threads").fetchone()
    assert thread_row["message_count"] == 2
    assert thread_row["total_tokens"] >= 2

    attachment_row = db.connection.execute(
        "SELECT mime_type, file_size, extracted_text, storage_path FROM attachments"
    ).fetchone()
    assert attachment_row["mime_type"] == "text/plain"
    assert attachment_row["file_size"] == len(b"Hello, Codex!")
    assert attachment_row["extracted_text"] == "Hello, Codex!"
    assert Path(attachment_row["storage_path"]).exists()

    job = db.connection.execute("SELECT status, files_total, files_processed FROM import_jobs").fetchone()
    assert job["status"] == "completed"
    assert job["files_total"] == 1
    assert job["files_processed"] == 1


def test_claude_ingest_detects_format(db: ChatDatabase, storage: AttachmentStorage) -> None:
    pipeline = ImportPipeline(db, storage)
    claude_path = FIXTURES / "claude_sample.json"

    result = pipeline.ingest([claude_path], ImportConfig())

    assert result.success
    assert result.files_processed == 1
    assert result.threads_created == 1
    assert result.attachments_saved == 1

    attachment = db.connection.execute("SELECT mime_type, file_size FROM attachments").fetchone()
    assert attachment["mime_type"] == "image/png"
    assert attachment["file_size"] > 0

    platform = db.connection.execute("SELECT name FROM platforms").fetchone()
    assert platform["name"] == "Claude"


def test_import_pipeline_skips_duplicates(db: ChatDatabase, storage: AttachmentStorage) -> None:
    pipeline = ImportPipeline(db, storage)
    chatgpt_path = FIXTURES / "chatgpt_sample.json"

    first = pipeline.ingest([chatgpt_path], ImportConfig())
    assert first.files_processed == 1

    second = pipeline.ingest([chatgpt_path], ImportConfig())
    assert second.files_processed == 0
    assert second.files_skipped == 1
    assert not second.errors

    imports = db.connection.execute("SELECT COUNT(*) AS count FROM import_files").fetchone()
    assert imports["count"] == 1

