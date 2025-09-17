"""Tests for ingestion pipeline normalization and persistence."""

from __future__ import annotations

import os
from pathlib import Path

import psycopg2
import pytest

from chat_manager import AttachmentStorage, ChatDatabase
from chat_manager.ingest import ImportConfig, ImportPipeline

FIXTURES = Path(__file__).parent / "fixtures"
TEST_DB_URL = os.environ.get("TEST_DATABASE_URL", "postgresql://user:pass@localhost:5432/test_db")

TABLES_TO_TRUNCATE = [
    "imported_files",
    "job_artifacts",
    "jobs",
    "message_entities",
    "thread_tags",
    "thread_topics",
    "embeddings",
    "link_edges",
    "audits",
    "attachments",
    "messages",
    "threads",
    "platforms",
    "tags",
    "entities",
    "topics",
]


@pytest.fixture(scope="session")
def db_session() -> ChatDatabase:
    """
    Session-scoped database connection.
    Assumes the database schema and extensions are already created.
    """
    db = ChatDatabase(dsn=TEST_DB_URL)
    yield db
    db.close()


@pytest.fixture()
def db(db_session: ChatDatabase) -> ChatDatabase:
    """
    Function-scoped database fixture that truncates all tables for test isolation.
    """
    with db_session.get_cursor(commit=True) as cur:
        # TRUNCATE is much faster than DROP/CREATE for cleaning tables.
        # RESTART IDENTITY resets auto-incrementing counters.
        cur.execute(f"TRUNCATE TABLE {', '.join(TABLES_TO_TRUNCATE)} RESTART IDENTITY CASCADE;")

    yield db_session


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

    with db.get_cursor() as cur:
        cur.execute("SELECT name FROM platforms")
        platforms = {row["name"] for row in cur.fetchall()}
        assert "ChatGPT" in platforms

        cur.execute("SELECT message_count, total_tokens FROM threads")
        thread_row = cur.fetchone()
        assert thread_row["message_count"] == 2
        assert thread_row["total_tokens"] >= 2

        cur.execute("SELECT mime_type, file_size, extracted_text, storage_path FROM attachments")
        attachment_row = cur.fetchone()
        assert attachment_row["mime_type"] == "text/plain"
        assert attachment_row["file_size"] == len(b"Hello, Codex!")
        assert attachment_row["extracted_text"] == "Hello, Codex!"
        assert Path(attachment_row["storage_path"]).exists()

        cur.execute("SELECT status, scope->>'files_total' as files_total, scope->>'files_processed' as files_processed FROM jobs")
        job_row = cur.fetchone()
        assert job_row["status"] == "completed"
        assert int(job_row["files_total"]) == 1
        assert int(job_row["files_processed"]) == 1


def test_claude_ingest_detects_format(db: ChatDatabase, storage: AttachmentStorage) -> None:
    pipeline = ImportPipeline(db, storage)
    claude_path = FIXTURES / "claude_sample.json"

    result = pipeline.ingest([claude_path], ImportConfig())

    assert result.success
    assert result.files_processed == 1
    assert result.threads_created == 1
    assert result.attachments_saved == 1

    with db.get_cursor() as cur:
        cur.execute("SELECT mime_type, file_size FROM attachments")
        attachment = cur.fetchone()
        assert attachment["mime_type"] == "image/png"
        assert attachment["file_size"] > 0

        cur.execute("SELECT name FROM platforms")
        platform = cur.fetchone()
        assert platform["name"] == "Claude"


def test_import_pipeline_skips_duplicates(db: ChatDatabase, storage: AttachmentStorage) -> None:
    # This test now relies on the attachment's content_hash to detect duplicates,
    # as the old `import_files` table is gone.
    pipeline = ImportPipeline(db, storage)
    chatgpt_path = FIXTURES / "chatgpt_sample.json"

    # First run should succeed
    first = pipeline.ingest([chatgpt_path], ImportConfig())
    assert first.success
    assert first.files_processed == 1

    with db.get_cursor() as cur:
        cur.execute("SELECT COUNT(*) as count FROM attachments")
        assert cur.fetchone()["count"] == 1

    # Second run should skip the file because the attachment hash is already present
    second = pipeline.ingest([chatgpt_path], ImportConfig())
    assert second.success
    assert second.files_processed == 0
    assert second.files_skipped == 1
    assert not second.errors

    with db.get_cursor() as cur:
        cur.execute("SELECT COUNT(*) as count FROM attachments")
        assert cur.fetchone()["count"] == 1
