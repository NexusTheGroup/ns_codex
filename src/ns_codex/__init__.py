"""ns_codex core package for the personal AI chat manager."""

from .cli import main as cli_main
from .db import Database, DEFAULT_DB_PATH
from .ingest import ingest_file, parse_chatgpt_export, parse_claude_export
from .local_ai import DEFAULT_MODELS, OllamaConfigManager
from .web import create_app

__all__ = [
    "cli_main",
    "Database",
    "DEFAULT_DB_PATH",
    "ingest_file",
    "parse_chatgpt_export",
    "parse_claude_export",
    "DEFAULT_MODELS",
    "OllamaConfigManager",
    "create_app",
]
