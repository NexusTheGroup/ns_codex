"""Format detection helpers for import pipeline."""

from __future__ import annotations

from enum import Enum
from typing import Any


class SupportedFormat(str, Enum):
    CHATGPT = "chatgpt"
    CLAUDE = "claude"


def detect_format(payload: dict[str, Any]) -> SupportedFormat:
    """Detect export format based on structural hints."""

    lowered_keys = {key.lower() for key in payload.keys()}
    fingerprint = " ".join(lowered_keys)
    if "mapping" in lowered_keys or payload.get("format", "").lower().startswith("chatgpt"):
        return SupportedFormat.CHATGPT
    if "chatgpt" in fingerprint:
        return SupportedFormat.CHATGPT

    type_hint = str(payload.get("type", "")).lower()
    if "claude" in type_hint or payload.get("source", "").lower().startswith("claude"):
        return SupportedFormat.CLAUDE
    if "conversation_uuid" in lowered_keys or "workspace" in lowered_keys:
        return SupportedFormat.CLAUDE

    # Claude exports frequently include "anthropic" metadata.
    meta = payload.get("meta") or {}
    if isinstance(meta, dict):
        combined = " ".join(str(value).lower() for value in meta.values())
        if "claude" in combined or "anthropic" in combined:
            return SupportedFormat.CLAUDE

    raise ValueError("Unsupported export format; expected ChatGPT or Claude JSON")

