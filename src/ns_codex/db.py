from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

from .types import AttachmentData, ThreadBundle

DEFAULT_DB_PATH = os.getenv("NS_CODEX_DB_PATH", os.path.expanduser("~/.local/share/ns_codex/db.sqlite3"))

_SQLITE_SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS platforms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    api_version TEXT,
    export_format_version TEXT,
    created_at TEXT,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS import_runs (
    id TEXT PRIMARY KEY,
    platform_id TEXT NOT NULL REFERENCES platforms(id),
    source_file TEXT NOT NULL,
    checksum TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    error TEXT
);
CREATE TABLE IF NOT EXISTS threads (
    id TEXT PRIMARY KEY,
    platform_id TEXT NOT NULL REFERENCES platforms(id),
    import_run_id TEXT REFERENCES import_runs(id),
    external_id TEXT,
    title TEXT,
    summary TEXT,
    created_at TEXT,
    updated_at TEXT,
    message_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    quality_score REAL,
    UNIQUE(platform_id, external_id)
);
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    content_type TEXT NOT NULL,
    timestamp TEXT,
    sequence_number INTEGER NOT NULL,
    token_count INTEGER,
    has_attachments INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS attachments (
    id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    filename TEXT,
    mime_type TEXT,
    file_size INTEGER,
    content_hash TEXT,
    storage_path TEXT,
    extracted_text TEXT,
    metadata TEXT
);
CREATE INDEX IF NOT EXISTS idx_messages_thread_seq ON messages(thread_id, sequence_number);
CREATE INDEX IF NOT EXISTS idx_threads_title_lower ON threads(lower(coalesce(title, '')));
CREATE INDEX IF NOT EXISTS idx_messages_content_lower ON messages(lower(content));
"""


def _ensure_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _isoformat(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def estimate_tokens(text: str) -> int:
    text = text.strip()
    if not text:
        return 0
    return max(1, len(text.split()))


class Database:
    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path or DEFAULT_DB_PATH
        self._conn = self._connect(self.path)
        self._initialize()

    @staticmethod
    def _connect(path: str) -> sqlite3.Connection:
        db_path = Path(path)
        if str(db_path) != ":memory:":
            _ensure_directory(db_path)
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def close(self) -> None:
        self._conn.close()

    def _initialize(self) -> None:
        with self._conn:
            self._conn.executescript(_SQLITE_SCHEMA)

    @contextmanager
    def _transaction(self):
        with self._conn:
            yield

    def _get_or_create_platform(self, name: str) -> str:
        row = self._conn.execute(
            "SELECT id FROM platforms WHERE name = ?", (name,)
        ).fetchone()
        if row:
            return row[0]
        platform_id = str(uuid4())
        now = _isoformat(datetime.now(timezone.utc))
        self._conn.execute(
            "INSERT INTO platforms (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (platform_id, name, now, now),
        )
        return platform_id

    def _start_import_run(self, platform_id: str, source_file: Path, checksum: str) -> Optional[str]:
        row = self._conn.execute(
            "SELECT id FROM import_runs WHERE platform_id = ? AND checksum = ?",
            (platform_id, checksum),
        ).fetchone()
        if row:
            return None
        run_id = str(uuid4())
        now = _isoformat(datetime.now(timezone.utc))
        self._conn.execute(
            "INSERT INTO import_runs (id, platform_id, source_file, checksum, status, started_at, finished_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run_id, platform_id, str(source_file), checksum, "completed", now, now),
        )
        return run_id

    def ingest_threads(
        self,
        platform_name: str,
        threads: Iterable[ThreadBundle],
        source_file: Path,
        checksum: str,
    ) -> Dict[str, Any]:
        platform_id = self._get_or_create_platform(platform_name)
        with self._transaction():
            import_run_id = self._start_import_run(platform_id, source_file, checksum)
            if import_run_id is None:
                return {"import_run_id": None, "inserted": 0, "skipped": True}
            inserted = 0
            for bundle in threads:
                self._persist_thread(platform_id, import_run_id, bundle)
                inserted += 1
            return {"import_run_id": import_run_id, "inserted": inserted, "skipped": False}

    def _persist_thread(self, platform_id: str, import_run_id: str, bundle: ThreadBundle) -> str:
        thread_id = self._upsert_thread(platform_id, import_run_id, bundle)
        self._conn.execute("DELETE FROM messages WHERE thread_id = ?", (thread_id,))
        message_rows = []
        attachments_rows = []
        sequence = 0
        total_tokens = 0
        for message in bundle.messages:
            sequence += 1
            tokens = message.token_count if message.token_count is not None else estimate_tokens(message.content)
            total_tokens += tokens
            message_id = str(uuid4())
            has_attachments = 1 if message.attachments else 0
            message_rows.append(
                (
                    message_id,
                    thread_id,
                    message.role,
                    message.content,
                    message.content_type,
                    _isoformat(message.timestamp),
                    sequence,
                    tokens,
                    has_attachments,
                )
            )
            for attachment in message.attachments:
                attachments_rows.append(self._attachment_row(message_id, attachment))
        if message_rows:
            self._conn.executemany(
                "INSERT INTO messages (id, thread_id, role, content, content_type, timestamp, sequence_number, token_count, has_attachments) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                message_rows,
            )
        if attachments_rows:
            self._conn.executemany(
                "INSERT INTO attachments (id, message_id, filename, mime_type, file_size, content_hash, storage_path, extracted_text, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                attachments_rows,
            )
        self._conn.execute(
            "UPDATE threads SET message_count = ?, total_tokens = ?, updated_at = coalesce(?, updated_at) WHERE id = ?",
            (len(bundle.messages), total_tokens, _isoformat(bundle.updated_at), thread_id),
        )
        return thread_id

    def _upsert_thread(self, platform_id: str, import_run_id: str, bundle: ThreadBundle) -> str:
        row = None
        if bundle.external_id:
            row = self._conn.execute(
                "SELECT id FROM threads WHERE platform_id = ? AND external_id = ?",
                (platform_id, bundle.external_id),
            ).fetchone()
        thread_id = row[0] if row else str(uuid4())
        created_at = _isoformat(bundle.created_at)
        updated_at = _isoformat(bundle.updated_at) or _isoformat(datetime.now(timezone.utc))
        if row:
            self._conn.execute(
                "UPDATE threads SET title = ?, summary = ?, created_at = ?, updated_at = ?, quality_score = ?, import_run_id = ? WHERE id = ?",
                (
                    bundle.title,
                    bundle.metadata.get("summary"),
                    created_at,
                    updated_at,
                    bundle.metadata.get("quality_score"),
                    import_run_id,
                    thread_id,
                ),
            )
        else:
            self._conn.execute(
                "INSERT INTO threads (id, platform_id, import_run_id, external_id, title, summary, created_at, updated_at, message_count, total_tokens, quality_score) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    thread_id,
                    platform_id,
                    import_run_id,
                    bundle.external_id,
                    bundle.title,
                    bundle.metadata.get("summary"),
                    created_at,
                    updated_at,
                    0,
                    0,
                    bundle.metadata.get("quality_score"),
                ),
            )
        return thread_id

    def _attachment_row(self, message_id: str, attachment: AttachmentData) -> tuple:
        from hashlib import sha256

        content_bytes = attachment.content or b""
        if not content_bytes and attachment.extracted_text:
            content_bytes = attachment.extracted_text.encode("utf-8")
        digest = sha256(content_bytes).hexdigest() if content_bytes else None
        metadata = attachment.metadata or {}
        return (
            str(uuid4()),
            message_id,
            attachment.filename,
            attachment.mime_type,
            attachment.file_size,
            digest,
            None,
            attachment.extracted_text,
            json.dumps(metadata, ensure_ascii=False),
        )

    def list_recent_threads(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self.search_threads(query=None, limit=limit)

    def search_threads(self, query: Optional[str], limit: int = 20) -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        if query:
            pattern = f"%{query.lower()}%"
            rows = cur.execute(
                """
                SELECT DISTINCT t.id, t.title, t.updated_at, t.message_count, t.total_tokens, p.name AS platform
                FROM threads t
                JOIN platforms p ON p.id = t.platform_id
                LEFT JOIN messages m ON m.thread_id = t.id
                WHERE lower(coalesce(t.title, '')) LIKE ? OR lower(m.content) LIKE ?
                ORDER BY t.updated_at DESC
                LIMIT ?
                """,
                (pattern, pattern, limit),
            ).fetchall()
        else:
            rows = cur.execute(
                """
                SELECT t.id, t.title, t.updated_at, t.message_count, t.total_tokens, p.name AS platform
                FROM threads t
                JOIN platforms p ON p.id = t.platform_id
                ORDER BY t.updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        results: List[Dict[str, Any]] = []
        for row in rows:
            thread_id = row["id"]
            preview_row = None
            if query:
                preview_row = self._conn.execute(
                    "SELECT content FROM messages WHERE thread_id = ? AND lower(content) LIKE ? ORDER BY sequence_number LIMIT 1",
                    (thread_id, pattern),
                ).fetchone()
            if not preview_row:
                preview_row = self._conn.execute(
                    "SELECT content FROM messages WHERE thread_id = ? ORDER BY sequence_number LIMIT 1",
                    (thread_id,),
                ).fetchone()
            preview = preview_row[0] if preview_row else ""
            results.append(
                {
                    "id": thread_id,
                    "title": row["title"],
                    "updated_at": row["updated_at"],
                    "message_count": row["message_count"],
                    "total_tokens": row["total_tokens"],
                    "platform": row["platform"],
                    "preview": preview,
                }
            )
        return results

    def get_thread(self, thread_id: str) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            """
            SELECT t.id, t.title, t.created_at, t.updated_at, t.message_count, t.total_tokens, p.name AS platform
            FROM threads t
            JOIN platforms p ON p.id = t.platform_id
            WHERE t.id = ?
            """,
            (thread_id,),
        ).fetchone()
        if not row:
            return None
        messages = []
        message_rows = self._conn.execute(
            "SELECT id, role, content, content_type, timestamp, sequence_number FROM messages WHERE thread_id = ? ORDER BY sequence_number",
            (thread_id,),
        ).fetchall()
        for message_row in message_rows:
            attachments = self._conn.execute(
                "SELECT filename, mime_type, file_size, extracted_text, metadata FROM attachments WHERE message_id = ?",
                (message_row["id"],),
            ).fetchall()
            attachments_payload = []
            for attachment in attachments:
                metadata = json.loads(attachment[4]) if attachment[4] else {}
                attachments_payload.append(
                    {
                        "filename": attachment[0],
                        "mime_type": attachment[1],
                        "file_size": attachment[2],
                        "extracted_text": attachment[3],
                        "metadata": metadata,
                    }
                )
            messages.append(
                {
                    "role": message_row["role"],
                    "content": message_row["content"],
                    "content_type": message_row["content_type"],
                    "timestamp": message_row["timestamp"],
                    "sequence_number": message_row["sequence_number"],
                    "attachments": attachments_payload,
                }
            )
        return {
            "id": row["id"],
            "title": row["title"],
            "platform": row["platform"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "message_count": row["message_count"],
            "total_tokens": row["total_tokens"],
            "messages": messages,
        }

    def health_check(self) -> None:
        self._conn.execute("SELECT 1")


__all__ = ["Database", "DEFAULT_DB_PATH", "estimate_tokens"]
