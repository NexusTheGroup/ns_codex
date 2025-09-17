"""High-level ingestion pipeline orchestration."""

from __future__ import annotations

import json
import mimetypes
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Iterable, Iterator, List

from ..db import ChatDatabase
from ..models import NormalizedImport, NormalizedThread
from ..storage import AttachmentStorage
from .detectors import SupportedFormat, detect_format
from .parsers import parse_chatgpt_export, parse_claude_export

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


@dataclass(slots=True)
class ImportConfig:
    platform_hint: SupportedFormat | None = None
    allow_partial: bool = True


@dataclass(slots=True)
class ImportResult:
    job_id: str
    files_processed: int
    files_skipped: int
    threads_created: int
    messages_created: int
    attachments_saved: int
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return not self.errors


@dataclass(slots=True)
class _LoadedPayload:
    source: str
    raw: bytes
    data: dict


class ImportPipeline:
    """Run normalization and persistence for supported exports."""

    def __init__(self, db: ChatDatabase, storage: AttachmentStorage) -> None:
        self.db = db
        self.storage = storage

    def ingest(self, sources: Iterable[Path | str], config: ImportConfig) -> ImportResult:
        payloads = list(self._load_sources(sources))
        job = self.db.create_job(
            (config.platform_hint.value if config.platform_hint else "auto"),
            len(payloads),
        )

        processed = skipped = threads_created = messages_created = attachments_saved = 0
        errors: List[str] = []

        for payload in payloads:
            content_hash = sha256(payload.raw).hexdigest()
            try:
                fmt = config.platform_hint or detect_format(payload.data)
            except ValueError as exc:
                errors.append(f"{payload.source}: {exc}")
                if not config.allow_partial:
                    break
                else:
                    continue

            recorded = self.db.record_import_file(
                job.id,
                content_hash=content_hash,
                source_path=payload.source,
                detected_format=fmt.value,
            )
            if not recorded:
                skipped += 1
                self.db.update_job_progress(job.id, files_processed=processed + skipped)
                continue

            try:
                normalized = self._normalize(fmt, payload.data)
            except Exception as exc:  # noqa: BLE001 - bubble up to caller optionally
                errors.append(f"{payload.source}: {exc}")
                if not config.allow_partial:
                    break
                else:
                    continue

            processed += 1
            stats = self._persist(normalized)
            threads_created += stats[0]
            messages_created += stats[1]
            attachments_saved += stats[2]
            self.db.update_job_progress(job.id, files_processed=processed + skipped)

        final_status = "completed" if not errors else ("failed" if processed == 0 else "completed_with_warnings")
        self.db.update_job_progress(job.id, status=final_status, error_messages=errors)
        return ImportResult(
            job_id=job.id,
            files_processed=processed,
            files_skipped=skipped,
            threads_created=threads_created,
            messages_created=messages_created,
            attachments_saved=attachments_saved,
            errors=errors,
        )

    def _normalize(self, fmt: SupportedFormat, data: dict) -> NormalizedImport:
        if fmt is SupportedFormat.CHATGPT:
            return parse_chatgpt_export(data)
        if fmt is SupportedFormat.CLAUDE:
            return parse_claude_export(data)
        raise ValueError(f"Unsupported format: {fmt}")

    def _persist(self, normalized: NormalizedImport) -> tuple[int, int, int]:
        platform_id = self.db.get_or_create_platform(normalized.platform_name)
        thread_count = message_count = attachment_count = 0
        for thread in normalized.threads:
            thread_count += 1
            message_count += thread.message_count()
            attachment_count += self._persist_thread(platform_id, thread)
        return thread_count, message_count, attachment_count

    def _persist_thread(self, platform_id: str, thread: NormalizedThread) -> int:
        created_at = self._format_datetime(thread.created_at)
        updated_at = self._format_datetime(thread.updated_at)
        thread_id = self.db.insert_thread(
            platform_id=platform_id,
            external_id=thread.external_id,
            title=thread.title,
            created_at=created_at,
            updated_at=updated_at,
            message_count=thread.message_count(),
            total_tokens=thread.total_tokens(),
        )
        attachments_saved = 0
        for sequence, message in enumerate(thread.messages, start=1):
            message_id = self.db.insert_message(
                thread_id=thread_id,
                external_id=message.external_id,
                role=message.role,
                content=message.content,
                content_type=message.content_type,
                timestamp=self._format_datetime(message.timestamp),
                sequence_number=sequence,
                token_count=message.token_estimate(),
                has_attachments=bool(message.attachments),
            )
            for attachment in message.attachments:
                mime_type = attachment.mime_type or mimetypes.guess_type(attachment.filename)[0] or "application/octet-stream"
                content_hash, path = self.storage.persist(message_id, attachment)
                self.db.insert_attachment(
                    message_id=message_id,
                    filename=attachment.filename,
                    mime_type=mime_type,
                    file_size=len(attachment.content),
                    content_hash=content_hash,
                    storage_path=str(path),
                    extracted_text=attachment.extracted_text,
                    metadata=attachment.metadata,
                )
                attachments_saved += 1
        return attachments_saved

    def _load_sources(self, sources: Iterable[Path | str]) -> Iterator[_LoadedPayload]:
        for source in sources:
            path = Path(source)
            if path.is_dir():
                for child in sorted(path.iterdir()):
                    yield from self._load_sources([child])
                continue
            if zipfile.is_zipfile(path):
                with zipfile.ZipFile(path) as archive:
                    for name in archive.namelist():
                        if not name.lower().endswith((".json", ".jsonl", ".ndjson")):
                            continue
                        raw = archive.read(name)
                        yield from self._decode_raw(raw, f"{path}::{name}")
                continue
            raw = path.read_bytes()
            yield from self._decode_raw(raw, str(path))

    def _decode_raw(self, raw: bytes, source: str) -> Iterator[_LoadedPayload]:
        text = raw.decode("utf-8")
        if source.lower().endswith((".jsonl", ".ndjson")):
            for idx, line in enumerate(text.splitlines(), start=1):
                line_text = line.strip()
                if not line_text:
                    continue
                data = json.loads(line_text)
                yield _LoadedPayload(source=f"{source}#L{idx}", raw=line_text.encode(), data=data)
        else:
            data = json.loads(text)
            yield _LoadedPayload(source=source, raw=raw, data=data)

    @staticmethod
    def _format_datetime(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).strftime(TIMESTAMP_FORMAT)

