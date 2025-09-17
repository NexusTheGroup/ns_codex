"""SQLite-backed persistence primitives for ingestion pipeline tests."""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

ISOFORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime(ISOFORMAT)


SCHEMA = """
CREATE TABLE IF NOT EXISTS platforms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    api_version TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS import_jobs (
    id TEXT PRIMARY KEY,
    platform_name TEXT NOT NULL,
    status TEXT NOT NULL,
    files_total INTEGER NOT NULL,
    files_processed INTEGER NOT NULL,
    error_messages TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS import_files (
    content_hash TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    source_path TEXT NOT NULL,
    detected_format TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    FOREIGN KEY(job_id) REFERENCES import_jobs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS threads (
    id TEXT PRIMARY KEY,
    platform_id TEXT NOT NULL,
    external_id TEXT NOT NULL,
    title TEXT,
    summary TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    message_count INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    FOREIGN KEY(platform_id) REFERENCES platforms(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS threads_platform_external_idx ON threads(platform_id, external_id);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL,
    external_id TEXT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    content_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    sequence_number INTEGER NOT NULL,
    token_count INTEGER NOT NULL,
    has_attachments INTEGER NOT NULL,
    FOREIGN KEY(thread_id) REFERENCES threads(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS messages_thread_seq_idx ON messages(thread_id, sequence_number);
CREATE INDEX IF NOT EXISTS messages_timestamp_idx ON messages(timestamp);

CREATE TABLE IF NOT EXISTS attachments (
    id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    extracted_text TEXT,
    metadata TEXT NOT NULL,
    FOREIGN KEY(message_id) REFERENCES messages(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS attachments_message_idx ON attachments(message_id);
CREATE UNIQUE INDEX IF NOT EXISTS attachments_hash_idx ON attachments(content_hash);
"""


@dataclass
class ImportJob:
    id: str
    platform_name: str
    status: str
    files_total: int
    files_processed: int
    error_messages: list[str]
    started_at: str
    finished_at: Optional[str]


class ChatDatabase:
    """Lightweight SQLite helper matching subset of blueprint schema."""

    def __init__(self, path: Path | str = ":memory:") -> None:
        self.path = Path(path) if path != ":memory:" else Path("./:memory:")
        self._conn = sqlite3.connect(
            str(path),
            check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON;")

    @property
    def connection(self) -> sqlite3.Connection:
        return self._conn

    def initialize(self) -> None:
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    @contextmanager
    def transaction(self):
        try:
            yield
        except Exception:
            self._conn.rollback()
            raise
        else:
            self._conn.commit()

    def get_or_create_platform(self, name: str, api_version: str | None = None) -> str:
        cur = self._conn.execute("SELECT id FROM platforms WHERE name = ?", (name,))
        row = cur.fetchone()
        if row:
            platform_id = row["id"]
            self._conn.execute(
                "UPDATE platforms SET updated_at = ? WHERE id = ?",
                (_utc_now(), platform_id),
            )
            self._conn.commit()
            return platform_id
        platform_id = str(uuid.uuid4())
        now = _utc_now()
        self._conn.execute(
            "INSERT INTO platforms (id, name, api_version, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (platform_id, name, api_version, now, now),
        )
        self._conn.commit()
        return platform_id

    def create_job(self, platform_name: str, files_total: int) -> ImportJob:
        job_id = str(uuid.uuid4())
        now = _utc_now()
        self._conn.execute(
            """
            INSERT INTO import_jobs (id, platform_name, status, files_total, files_processed, error_messages, started_at)
            VALUES (?, ?, 'running', ?, 0, ?, ?)
            """,
            (job_id, platform_name, files_total, json.dumps([]), now),
        )
        self._conn.commit()
        return ImportJob(
            id=job_id,
            platform_name=platform_name,
            status="running",
            files_total=files_total,
            files_processed=0,
            error_messages=[],
            started_at=now,
            finished_at=None,
        )

    def update_job_progress(
        self,
        job_id: str,
        *,
        files_processed: Optional[int] = None,
        status: Optional[str] = None,
        error_messages: Optional[Iterable[str]] = None,
    ) -> None:
        updates: list[str] = []
        params: list[object] = []
        if files_processed is not None:
            updates.append("files_processed = ?")
            params.append(files_processed)
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if error_messages is not None:
            updates.append("error_messages = ?")
            params.append(json.dumps(list(error_messages)))
        if status in {"completed", "failed", "cancelled"}:
            updates.append("finished_at = ?")
            params.append(_utc_now())
        if not updates:
            return
        params.append(job_id)
        query = f"UPDATE import_jobs SET {', '.join(updates)} WHERE id = ?"
        self._conn.execute(query, tuple(params))
        self._conn.commit()

    def record_import_file(
        self,
        job_id: str,
        *,
        content_hash: str,
        source_path: str,
        detected_format: str,
    ) -> bool:
        cur = self._conn.execute(
            "SELECT content_hash FROM import_files WHERE content_hash = ?",
            (content_hash,),
        )
        if cur.fetchone():
            return False
        self._conn.execute(
            """
            INSERT INTO import_files (content_hash, job_id, source_path, detected_format, imported_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (content_hash, job_id, source_path, detected_format, _utc_now()),
        )
        self._conn.commit()
        return True

    def insert_thread(
        self,
        *,
        platform_id: str,
        external_id: str,
        title: str | None,
        created_at: str,
        updated_at: str,
        message_count: int,
        total_tokens: int,
        summary: str | None = None,
    ) -> str:
        thread_id = str(uuid.uuid4())
        self._conn.execute(
            """
            INSERT INTO threads (id, platform_id, external_id, title, summary, created_at, updated_at, message_count, total_tokens)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                thread_id,
                platform_id,
                external_id,
                title,
                summary,
                created_at,
                updated_at,
                message_count,
                total_tokens,
            ),
        )
        self._conn.commit()
        return thread_id

    def insert_message(
        self,
        *,
        thread_id: str,
        external_id: str | None,
        role: str,
        content: str,
        content_type: str,
        timestamp: str,
        sequence_number: int,
        token_count: int,
        has_attachments: bool,
    ) -> str:
        message_id = str(uuid.uuid4())
        self._conn.execute(
            """
            INSERT INTO messages (
                id, thread_id, external_id, role, content, content_type, timestamp, sequence_number, token_count, has_attachments
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                thread_id,
                external_id,
                role,
                content,
                content_type,
                timestamp,
                sequence_number,
                token_count,
                1 if has_attachments else 0,
            ),
        )
        self._conn.commit()
        return message_id

    def insert_attachment(
        self,
        *,
        message_id: str,
        filename: str,
        mime_type: str,
        file_size: int,
        content_hash: str,
        storage_path: str,
        extracted_text: str | None,
        metadata: dict | None,
    ) -> str:
        attachment_id = str(uuid.uuid4())
        self._conn.execute(
            """
            INSERT INTO attachments (
                id, message_id, filename, mime_type, file_size, content_hash, storage_path, extracted_text, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attachment_id,
                message_id,
                filename,
                mime_type,
                file_size,
                content_hash,
                storage_path,
                extracted_text,
                json.dumps(metadata or {}),
            ),
        )
        self._conn.commit()
        return attachment_id

