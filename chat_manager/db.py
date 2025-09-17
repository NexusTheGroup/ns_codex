"""PostgreSQL-backed persistence for the Personal AI Chat Manager."""

from __future__ import annotations

import json
import logging
import os
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, fields
from datetime import datetime, timezone
from typing import Any, Iterable, Optional

import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.pool import SimpleConnectionPool

logger = logging.getLogger(__name__)


@dataclass
class ImportJob:
    id: uuid.UUID
    job_type: str
    status: str
    scope: dict[str, Any]
    progress_percent: float
    error_messages: list[str]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]

    @classmethod
    def from_row(cls, row: dict) -> "ImportJob":
        """Create an ImportJob from a database row, handling data type conversions."""
        return cls(
            id=row["id"],
            job_type=row["job_type"],
            status=row["status"],
            scope=row.get("scope", {}),
            progress_percent=float(row.get("progress_percent", 0.0)),
            error_messages=row.get("error_messages", []),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            started_at=row.get("started_at"),
            finished_at=row.get("finished_at"),
        )


class ChatDatabase:
    """PostgreSQL helper class implementing the blueprint schema."""

    def __init__(self, dsn: Optional[str] = None, max_connections: int = 10) -> None:
        self.dsn = dsn or os.environ.get("DATABASE_URL", "postgresql://user:pass@localhost:5432/app")
        if not self.dsn:
            raise ValueError("Database DSN must be provided or set in DATABASE_URL env var.")
        self._pool = SimpleConnectionPool(minconn=1, maxconn=max_connections, dsn=self.dsn)

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool."""
        conn = self._pool.getconn()
        try:
            yield conn
        finally:
            self._pool.putconn(conn)

    @contextmanager
    def get_cursor(self, commit: bool = False):
        """Get a cursor from a pooled connection."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                try:
                    yield cur
                    if commit:
                        conn.commit()
                except psycopg2.Error as e:
                    logger.error("Database error: %s", e)
                    conn.rollback()
                    raise

    def initialize(self, schema_path: str) -> None:
        """Initialize the database by executing a schema file."""
        logger.info("Initializing database from schema: %s", schema_path)
        try:
            with open(schema_path, "r") as f:
                schema_sql = f.read()
            with self.get_cursor(commit=True) as cur:
                cur.execute(schema_sql)
            logger.info("Database initialized successfully.")
        except FileNotFoundError:
            logger.error("Schema file not found at %s", schema_path)
            raise
        except psycopg2.Error as e:
            logger.error("Failed to initialize database: %s", e)
            raise

    def close(self) -> None:
        """Close all connections in the pool."""
        if self._pool:
            self._pool.closeall()

    def get_or_create_platform(self, name: str, api_version: str | None = None) -> uuid.UUID:
        """Get a platform by name, or create it if it doesn't exist."""
        with self.get_cursor(commit=True) as cur:
            cur.execute("SELECT id FROM platforms WHERE name = %s", (name,))
            row = cur.fetchone()
            if row:
                platform_id = row["id"]
                cur.execute(
                    "UPDATE platforms SET updated_at = %s WHERE id = %s",
                    (datetime.now(timezone.utc), platform_id),
                )
                return platform_id

            cur.execute(
                "INSERT INTO platforms (name, api_version) VALUES (%s, %s) RETURNING id",
                (name, api_version),
            )
            new_row = cur.fetchone()
            if not new_row:
                raise RuntimeError("Failed to create platform.")
            return new_row["id"]

    def create_job(self, job_type: str, scope: Optional[dict] = None) -> ImportJob:
        """Create a new job entry in the database."""
        query = """
            INSERT INTO jobs (job_type, status, scope, progress_percent, error_messages)
            VALUES (%s, 'pending', %s, 0.0, ARRAY[]::TEXT[])
            RETURNING *;
        """
        with self.get_cursor(commit=True) as cur:
            cur.execute(query, (job_type, json.dumps(scope or {})))
            job_row = cur.fetchone()
            if not job_row:
                raise RuntimeError("Failed to create job.")
            return ImportJob.from_row(dict(job_row))

    def update_job_progress(
        self,
        job_id: uuid.UUID,
        *,
        status: Optional[str] = None,
        progress_percent: Optional[float] = None,
        error_messages: Optional[list[str]] = None,
        scope: Optional[dict] = None,
    ) -> None:
        """Update a job's status, progress, scope, or errors."""
        updates: list[str] = []
        params: list[Any] = []

        if status is not None:
            updates.append("status = %s")
            params.append(status)
        if progress_percent is not None:
            updates.append("progress_percent = %s")
            params.append(progress_percent)
        if error_messages is not None:
            updates.append("error_messages = error_messages || %s::TEXT[]")
            params.append(error_messages)
        if scope is not None:
            updates.append("scope = %s")
            params.append(json.dumps(scope))
        if status in {"completed", "failed", "cancelled"}:
            updates.append("finished_at = %s")
            params.append(datetime.now(timezone.utc))

        if not updates:
            return

        params.append(job_id)
        query = f"UPDATE jobs SET {', '.join(updates)}, updated_at = NOW() WHERE id = %s"

        with self.get_cursor(commit=True) as cur:
            cur.execute(query, tuple(params))

    def insert_thread(
        self,
        *,
        platform_id: uuid.UUID,
        external_id: str,
        title: Optional[str],
        created_at: datetime,
        updated_at: datetime,
        message_count: int,
        total_tokens: int,
        summary: Optional[str] = None,
        quality_score: Optional[float] = None,
    ) -> uuid.UUID:
        """Insert a new thread and return its ID."""
        query = """
            INSERT INTO threads (
                platform_id, external_id, title, summary, created_at, updated_at,
                message_count, total_tokens, quality_score
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
        """
        with self.get_cursor(commit=True) as cur:
            cur.execute(
                query,
                (
                    platform_id,
                    external_id,
                    title,
                    summary,
                    created_at,
                    updated_at,
                    message_count,
                    total_tokens,
                    quality_score,
                ),
            )
            row = cur.fetchone()
            if not row:
                raise RuntimeError("Failed to insert thread.")
            return row["id"]

    def insert_message(
        self,
        *,
        thread_id: uuid.UUID,
        role: str,
        content: str,
        content_type: str,
        timestamp: datetime,
        sequence_number: int,
        token_count: int,
        has_attachments: bool,
    ) -> uuid.UUID:
        """Insert a new message and return its ID."""
        query = """
            INSERT INTO messages (
                thread_id, role, content, content_type, timestamp,
                sequence_number, token_count, has_attachments
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
        """
        with self.get_cursor(commit=True) as cur:
            cur.execute(
                query,
                (
                    thread_id,
                    role,
                    content,
                    content_type,
                    timestamp,
                    sequence_number,
                    token_count,
                    has_attachments,
                ),
            )
            row = cur.fetchone()
            if not row:
                raise RuntimeError("Failed to insert message.")
            return row["id"]

    def insert_attachment(
        self,
        *,
        message_id: uuid.UUID,
        filename: str,
        mime_type: str,
        file_size: int,
        content_hash: str,
        storage_path: str,
        extracted_text: Optional[str],
        metadata: Optional[dict],
    ) -> str:
        """Insert a new attachment and return its content hash."""
        query = """
            INSERT INTO attachments (
                message_id, filename, mime_type, file_size, content_hash,
                storage_path, extracted_text, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING content_hash;
        """
        with self.get_cursor(commit=True) as cur:
            cur.execute(
                query,
                (
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
            row = cur.fetchone()
            if not row:
                raise RuntimeError("Failed to insert attachment.")
            return row["content_hash"]

    def is_content_hash_present(self, content_hash: str) -> bool:
        """Check if an attachment with the given content hash already exists."""
        with self.get_cursor() as cur:
            cur.execute(
                "SELECT 1 FROM attachments WHERE content_hash = %s", (content_hash,)
            )
            return cur.fetchone() is not None

    def get_thread_by_external_id(
        self, platform_id: uuid.UUID, external_id: str
    ) -> Optional[uuid.UUID]:
        """Get a thread ID by its platform and external ID."""
        with self.get_cursor() as cur:
            cur.execute(
                "SELECT id FROM threads WHERE platform_id = %s AND external_id = %s",
                (platform_id, external_id),
            )
            row = cur.fetchone()
            return row["id"] if row else None

    def is_file_hash_present(self, content_hash: str) -> bool:
        """Check if a file with the given content hash has been imported."""
        with self.get_cursor() as cur:
            cur.execute(
                "SELECT 1 FROM imported_files WHERE content_hash = %s", (content_hash,)
            )
            return cur.fetchone() is not None

    def record_imported_file(
        self,
        job_id: uuid.UUID,
        content_hash: str,
        source_path: str,
        detected_format: str,
    ) -> None:
        """Record a successfully imported file."""
        with self.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO imported_files (job_id, content_hash, source_path, detected_format)
                VALUES (%s, %s, %s, %s)
                """,
                (job_id, content_hash, source_path, detected_format),
            )
