"""Core package for Personal AI Chat Manager data foundations."""

from .db import ChatDatabase
from .storage import AttachmentStorage
from .ingest.pipeline import ImportPipeline, ImportResult, ImportConfig

__all__ = [
    "ChatDatabase",
    "AttachmentStorage",
    "ImportPipeline",
    "ImportResult",
    "ImportConfig",
]
