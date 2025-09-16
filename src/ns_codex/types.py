from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class AttachmentData:
    """Normalized representation of an attachment extracted from an import."""

    filename: str
    mime_type: str
    file_size: Optional[int] = None
    content: Optional[bytes] = None
    extracted_text: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MessageData:
    """Single conversational turn."""

    role: str
    content: str
    content_type: str = "text"
    timestamp: Optional[datetime] = None
    token_count: Optional[int] = None
    attachments: List[AttachmentData] = field(default_factory=list)
    raw_id: Optional[str] = None


@dataclass
class ThreadBundle:
    """Normalized conversation prior to persistence."""

    external_id: Optional[str]
    title: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    messages: List[MessageData] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    checksum: Optional[str] = None

    def compute_checksum(self) -> str:
        import hashlib

        hasher = hashlib.sha256()
        for message in self.messages:
            hasher.update((message.role or "").encode("utf-8"))
            hasher.update((message.content or "").encode("utf-8"))
            if message.timestamp:
                hasher.update(message.timestamp.isoformat().encode("utf-8"))
            for attachment in message.attachments:
                hasher.update((attachment.filename or "").encode("utf-8"))
                if attachment.extracted_text:
                    hasher.update(attachment.extracted_text.encode("utf-8"))
        digest = hasher.hexdigest()
        self.checksum = digest
        return digest
