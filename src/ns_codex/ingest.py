from __future__ import annotations

import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List

from .db import Database
from .types import AttachmentData, MessageData, ThreadBundle

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore

_TIMEZONE_NAME = os.getenv("NS_CODEX_TIMEZONE")


def _target_timezone():
    if _TIMEZONE_NAME and ZoneInfo:
        try:
            return ZoneInfo(_TIMEZONE_NAME)
        except Exception:  # pragma: no cover - invalid tz, fallback to UTC
            pass
    return timezone.utc


def _to_datetime(value) -> datetime | None:
    if value is None:
        return None
    tz = _target_timezone()
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz)
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(tz)
    return None


def _read_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _read_zip_json(path: Path, inner_name: str) -> Any:
    with zipfile.ZipFile(path) as archive:
        with archive.open(inner_name) as fh:
            data = fh.read().decode("utf-8")
            return json.loads(data)


def _read_zip_jsonl(path: Path, inner_name: str) -> List[dict]:
    results = []
    with zipfile.ZipFile(path) as archive:
        with archive.open(inner_name) as fh:
            for line in fh:
                line = line.decode("utf-8").strip()
                if line:
                    results.append(json.loads(line))
    return results


def parse_chatgpt_export(path: Path) -> List[ThreadBundle]:
    path = Path(path)
    if path.suffix == ".zip":
        conversations = _read_zip_json(path, "conversations.json")
    else:
        conversations = _read_json_file(path)
    bundles: List[ThreadBundle] = []
    for convo in conversations:
        mapping = convo.get("mapping") or {}
        messages = []
        for node in mapping.values():
            message = node.get("message")
            if not message:
                continue
            author = (message.get("author") or {}).get("role")
            if author not in {"user", "assistant", "system"}:
                continue
            content = _extract_chatgpt_content(message)
            timestamp = _to_datetime(message.get("create_time"))
            attachments = _extract_chatgpt_attachments(message.get("metadata") or {})
            messages.append(
                MessageData(
                    role=author,
                    content=content,
                    timestamp=timestamp,
                    content_type=message.get("content", {}).get("content_type", "text"),
                    attachments=attachments,
                    raw_id=message.get("id"),
                )
            )
        if not messages:
            continue
        messages.sort(key=lambda item: (item.timestamp or datetime.min.replace(tzinfo=timezone.utc), item.raw_id or ""))
        bundle = ThreadBundle(
            external_id=convo.get("id") or convo.get("conversation_id"),
            title=convo.get("title"),
            created_at=_to_datetime(convo.get("create_time")),
            updated_at=_to_datetime(convo.get("update_time")),
            messages=messages,
            metadata={"summary": convo.get("current_node_summary")},
        )
        bundle.compute_checksum()
        bundles.append(bundle)
    return bundles


def _extract_chatgpt_content(message: dict) -> str:
    content = message.get("content") or {}
    parts = content.get("parts")
    if isinstance(parts, list) and parts:
        return "\n\n".join(str(part) for part in parts if part is not None)
    text = content.get("text")
    if isinstance(text, str):
        return text
    return ""


def _extract_chatgpt_attachments(metadata: dict) -> List[AttachmentData]:
    attachments: List[AttachmentData] = []
    for item in metadata.get("attachments", []):
        filename = item.get("filename") or item.get("name") or "attachment"
        mime_type = item.get("mimeType") or item.get("mime_type") or "application/octet-stream"
        extracted = item.get("extract") or item.get("text")
        extra = {k: v for k, v in item.items() if k not in {"filename", "name", "mimeType", "mime_type", "extract", "text"}}
        attachments.append(
            AttachmentData(
                filename=filename,
                mime_type=mime_type,
                extracted_text=extracted,
                metadata=extra,
            )
        )
    return attachments


def parse_claude_export(path: Path) -> List[ThreadBundle]:
    path = Path(path)
    if path.suffix == ".zip":
        records = _read_zip_jsonl(path, "conversations.jsonl")
    elif path.suffix == ".jsonl":
        with path.open("r", encoding="utf-8") as fh:
            records = [json.loads(line) for line in fh if line.strip()]
    else:
        data = _read_json_file(path)
        records = data if isinstance(data, list) else [data]
    bundles: List[ThreadBundle] = []
    for record in records:
        convo_messages = record.get("messages") or record.get("conversation") or []
        messages: List[MessageData] = []
        for msg in convo_messages:
            role = _normalize_claude_role(msg.get("type") or msg.get("role"))
            if role not in {"user", "assistant", "system"}:
                continue
            text = msg.get("text") or msg.get("content") or ""
            timestamp = _to_datetime(msg.get("created_at") or record.get("created_at"))
            attachments = _extract_claude_attachments(msg)
            messages.append(
                MessageData(
                    role=role,
                    content=text,
                    timestamp=timestamp,
                    attachments=attachments,
                    raw_id=str(msg.get("id") or msg.get("uuid") or ""),
                )
            )
        if not messages:
            continue
        messages.sort(key=lambda item: (item.timestamp or datetime.min.replace(tzinfo=timezone.utc), item.raw_id or ""))
        bundle = ThreadBundle(
            external_id=str(record.get("uuid") or record.get("id")),
            title=record.get("name") or record.get("summary"),
            created_at=_to_datetime(record.get("created_at")),
            updated_at=_to_datetime(record.get("updated_at")),
            messages=messages,
            metadata={"summary": record.get("summary")},
        )
        bundle.compute_checksum()
        bundles.append(bundle)
    return bundles


def _normalize_claude_role(value: str | None) -> str | None:
    if not value:
        return None
    mapping = {
        "human": "user",
        "user": "user",
        "assistant": "assistant",
        "computer": "assistant",
        "system": "system",
    }
    return mapping.get(value.lower(), value.lower())


def _extract_claude_attachments(message: dict) -> List[AttachmentData]:
    attachments: List[AttachmentData] = []
    for item in message.get("attachments", []):
        filename = item.get("filename") or item.get("name") or "attachment"
        mime_type = item.get("mime_type") or item.get("mimetype") or "application/octet-stream"
        extracted = item.get("text") or item.get("excerpt")
        attachments.append(
            AttachmentData(
                filename=filename,
                mime_type=mime_type,
                extracted_text=extracted,
                metadata={k: v for k, v in item.items() if k not in {"filename", "name", "mime_type", "mimetype", "text", "excerpt"}},
            )
        )
    return attachments


def ingest_file(db: Database, platform: str, path: Path) -> dict:
    path = Path(path)
    if platform == "chatgpt":
        bundles = parse_chatgpt_export(path)
    elif platform == "claude":
        bundles = parse_claude_export(path)
    else:  # pragma: no cover - defensive
        raise ValueError(f"Unsupported platform: {platform}")
    checksum = _file_checksum(path)
    result = db.ingest_threads(platform, bundles, path, checksum)
    result["threads"] = len(bundles)
    return result


def _file_checksum(path: Path) -> str:
    import hashlib

    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


__all__ = [
    "parse_chatgpt_export",
    "parse_claude_export",
    "ingest_file",
]
