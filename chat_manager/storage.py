"""Filesystem attachment storage utilities."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .models import NormalizedAttachment


_SAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def _sanitize_filename(name: str) -> str:
    # Drop path traversal and compress spaces
    candidate = Path(name).name.strip()
    if not candidate:
        candidate = "attachment.bin"
    cleaned = _SAFE_CHARS.sub("_", candidate)
    return cleaned[:128]


class AttachmentStorage:
    """Store attachments on disk using content-hash fan-out directories."""

    def __init__(self, base_path: Path) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def persist(self, message_id: str, attachment: NormalizedAttachment) -> tuple[str, Path]:
        content_hash = hashlib.sha256(attachment.content).hexdigest()
        shard_a, shard_b = content_hash[:2], content_hash[2:4]
        directory = self.base_path / shard_a / shard_b / message_id
        directory.mkdir(parents=True, exist_ok=True)
        filename = _sanitize_filename(attachment.filename)
        path = directory / filename
        path.write_bytes(attachment.content)
        return content_hash, path

