"""Export format parsers producing normalized records."""

from __future__ import annotations

import base64
import binascii
from datetime import datetime, timezone
from typing import Any, Iterable, List

from ..models import (
    NormalizedAttachment,
    NormalizedImport,
    NormalizedMessage,
    NormalizedThread,
)


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if not value:
        return datetime.now(tz=timezone.utc)
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).astimezone(timezone.utc)
    except ValueError as exc:
        raise ValueError(f"Unable to parse datetime value: {value!r}") from exc


def _coerce_bytes(blob: Any) -> bytes:
    if isinstance(blob, bytes):
        return blob
    if blob is None:
        return b""
    if isinstance(blob, str):
        candidate = blob.strip()
        if not candidate:
            return b""
        try:
            return base64.b64decode(candidate, validate=True)
        except (binascii.Error, ValueError):
            return candidate.encode()
    raise TypeError(f"Unsupported attachment payload: {type(blob)!r}")


def _normalise_role(raw: Any) -> str:
    if isinstance(raw, dict):
        raw = raw.get("role") or raw.get("author")
    if raw is None:
        return "user"
    return str(raw).strip().lower() or "user"


def _normalise_content(payload: Any) -> str:
    if isinstance(payload, dict):
        if "parts" in payload and isinstance(payload["parts"], Iterable):
            parts = [str(part) for part in payload["parts"]]
            return "\n".join(part for part in parts if part)
        if "text" in payload:
            return str(payload.get("text", ""))
        if "content" in payload:
            return str(payload.get("content", ""))
    if payload is None:
        return ""
    return str(payload)


def parse_chatgpt_export(payload: dict[str, Any]) -> NormalizedImport:
    conversations = payload.get("conversations") or payload.get("threads") or []
    if not isinstance(conversations, Iterable):
        raise ValueError("ChatGPT export missing conversations list")

    threads: List[NormalizedThread] = []
    for conversation in conversations:
        messages_raw = conversation.get("messages") or []
        created = _parse_datetime(
            conversation.get("create_time")
            or conversation.get("created_at")
            or (messages_raw[0]["timestamp"] if messages_raw else None)
        )
        updated = _parse_datetime(conversation.get("update_time") or conversation.get("updated_at") or created)
        normalized_messages: List[NormalizedMessage] = []
        for sequence, message in enumerate(messages_raw, start=1):
            attachments_payload = []
            for attachment in message.get("attachments", []) or []:
                metadata = {
                    key: value
                    for key, value in attachment.items()
                    if key not in {"filename", "mime_type", "data", "base64", "content", "extracted_text"}
                }
                blob = (
                    attachment.get("data")
                    or attachment.get("base64")
                    or attachment.get("content")
                    or attachment.get("body")
                )
                attachments_payload.append(
                    NormalizedAttachment(
                        filename=str(attachment.get("filename") or "attachment.bin"),
                        content=_coerce_bytes(blob),
                        mime_type=attachment.get("mime_type"),
                        extracted_text=attachment.get("extracted_text"),
                        metadata=metadata,
                    )
                )
            normalized_messages.append(
                NormalizedMessage(
                    external_id=str(message.get("id")) if message.get("id") else None,
                    role=_normalise_role(message.get("author") or message.get("role")),
                    content=_normalise_content(message.get("content") or message.get("text")),
                    timestamp=_parse_datetime(message.get("timestamp") or message.get("create_time")),
                    content_type=str(message.get("content_type") or "text"),
                    attachments=tuple(attachments_payload),
                )
            )
        threads.append(
            NormalizedThread(
                external_id=str(conversation.get("id") or conversation.get("conversation_id") or conversation.get("uuid")),
                title=conversation.get("title") or conversation.get("name"),
                created_at=created,
                updated_at=updated,
                messages=normalized_messages,
            )
        )
    return NormalizedImport(platform_name="ChatGPT", threads=threads)


def parse_claude_export(payload: dict[str, Any]) -> NormalizedImport:
    conversations = payload.get("conversations") or payload.get("chats") or []
    if not isinstance(conversations, Iterable):
        raise ValueError("Claude export missing conversations list")

    threads: List[NormalizedThread] = []
    for conversation in conversations:
        messages_raw = conversation.get("messages") or []
        created = _parse_datetime(
            conversation.get("created_at")
            or conversation.get("created")
            or (messages_raw[0]["timestamp"] if messages_raw else None)
        )
        updated = _parse_datetime(conversation.get("updated_at") or conversation.get("modified_at") or created)
        normalized_messages: List[NormalizedMessage] = []
        for sequence, message in enumerate(messages_raw, start=1):
            attachments_payload = []
            for attachment in message.get("attachments", []) or []:
                metadata = {
                    key: value
                    for key, value in attachment.items()
                    if key
                    not in {
                        "name",
                        "filename",
                        "mime_type",
                        "data",
                        "base64",
                        "content",
                        "text",
                        "extracted_text",
                    }
                }
                blob = (
                    attachment.get("data")
                    or attachment.get("base64")
                    or attachment.get("body")
                    or attachment.get("text")
                )
                attachments_payload.append(
                    NormalizedAttachment(
                        filename=str(
                            attachment.get("filename")
                            or attachment.get("name")
                            or attachment.get("id")
                            or "attachment.bin"
                        ),
                        content=_coerce_bytes(blob),
                        mime_type=attachment.get("mime_type"),
                        extracted_text=attachment.get("extracted_text"),
                        metadata=metadata,
                    )
                )
            normalized_messages.append(
                NormalizedMessage(
                    external_id=str(message.get("id") or message.get("uuid")) if message.get("id") or message.get("uuid") else None,
                    role=_normalise_role(message.get("role") or message.get("speaker")),
                    content=_normalise_content(message.get("text") or message.get("content")),
                    timestamp=_parse_datetime(message.get("timestamp") or message.get("created_at")),
                    content_type=str(message.get("content_type") or "text"),
                    attachments=tuple(attachments_payload),
                )
            )
        threads.append(
            NormalizedThread(
                external_id=str(
                    conversation.get("uuid")
                    or conversation.get("id")
                    or conversation.get("conversation_uuid")
                ),
                title=conversation.get("name") or conversation.get("title"),
                created_at=created,
                updated_at=updated,
                messages=normalized_messages,
            )
        )
    return NormalizedImport(platform_name="Claude", threads=threads)

