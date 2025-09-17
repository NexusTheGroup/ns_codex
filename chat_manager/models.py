"""Dataclasses representing canonical ingestion records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable, List, Sequence


@dataclass(slots=True)
class NormalizedAttachment:
    """Attachment payload extracted during normalization."""

    filename: str
    content: bytes
    mime_type: str | None = None
    extracted_text: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class NormalizedMessage:
    """Canonical message representation."""

    role: str
    content: str
    timestamp: datetime
    external_id: str | None = None
    content_type: str = "text"
    attachments: Sequence[NormalizedAttachment] = field(default_factory=tuple)

    def token_estimate(self) -> int:
        """Approximate token count using whitespace split fallback."""

        stripped = self.content.strip()
        if not stripped:
            return 0
        # Heuristic: tokens roughly equal to word count * 1.3 for safety.
        words = max(1, len(stripped.split()))
        return int(words * 1.3)


@dataclass(slots=True)
class NormalizedThread:
    """Canonical conversation thread."""

    external_id: str
    title: str | None
    created_at: datetime
    updated_at: datetime
    messages: List[NormalizedMessage] = field(default_factory=list)

    def message_count(self) -> int:
        return len(self.messages)

    def total_tokens(self) -> int:
        return sum(message.token_estimate() for message in self.messages)


@dataclass(slots=True)
class NormalizedImport:
    """Wrapper containing normalized threads for a source export."""

    platform_name: str
    threads: Iterable[NormalizedThread]

