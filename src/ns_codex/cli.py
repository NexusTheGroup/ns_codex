from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

from .db import DEFAULT_DB_PATH, Database
from .ingest import ingest_file
from .local_ai import DEFAULT_CONFIG_DIR, OllamaConfigManager
from .web import create_app


def _default_db_path(cli_value: Optional[str]) -> Path:
    if cli_value:
        return Path(cli_value)
    env = os.getenv("NS_CODEX_DB_PATH")
    if env:
        return Path(env)
    return Path(DEFAULT_DB_PATH)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="ns_codex", description="Personal AI chat manager tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Import a platform export into the database")
    ingest_parser.add_argument("export", type=str, help="Path to export file (JSON/JSONL/ZIP)")
    ingest_parser.add_argument("--platform", required=True, choices=["chatgpt", "claude"], help="Source platform")
    ingest_parser.add_argument("--db", type=str, help="Database path override")

    serve_parser = subparsers.add_parser("runserver", help="Run the local web UI")
    serve_parser.add_argument("--db", type=str, help="Database path override")
    serve_parser.add_argument("--host", type=str, default=None, help="Server host (default 127.0.0.1)")
    serve_parser.add_argument("--port", type=int, default=None, help="Server port (default 8000)")

    ollama_parser = subparsers.add_parser("ollama-config", help="Generate Ollama manifest and pull script")
    ollama_parser.add_argument("--dir", type=str, default=None, help="Output directory override")
    ollama_parser.add_argument("--overwrite", action="store_true", help="Allow overwriting existing files")

    args = parser.parse_args(argv)

    if args.command == "ingest":
        return _cmd_ingest(args)
    if args.command == "runserver":
        return _cmd_runserver(args)
    if args.command == "ollama-config":
        return _cmd_ollama(args)
    parser.print_help()
    return 1


def _cmd_ingest(args) -> int:
    export_path = Path(args.export)
    if not export_path.exists():
        print(f"Export not found: {export_path}", file=sys.stderr)
        return 2
    db_path = _default_db_path(args.db)
    db = Database(str(db_path))
    try:
        result = ingest_file(db, args.platform, export_path)
    finally:
        db.close()
    if result.get("skipped"):
        print(f"Skipped import; checksum already processed for {args.platform}.")
    else:
        print(f"Imported {result.get('inserted', 0)} threads ({result.get('threads')} parsed) into {db_path}.")
    return 0


def _cmd_runserver(args) -> int:
    db_path = _default_db_path(args.db)
    host = args.host or os.getenv("NS_CODEX_SERVER_HOST", "127.0.0.1")
    port_env = os.getenv("NS_CODEX_SERVER_PORT")
    port = args.port or (int(port_env) if port_env else 8000)
    db = Database(str(db_path))
    app = create_app(db)
    from wsgiref.simple_server import make_server

    print(f"Serving ns_codex on http://{host}:{port} (database: {db_path})")
    try:
        with make_server(host, port, app) as server:
            server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover - manual shutdown
        print("\nStopping server...")
    finally:
        db.close()
    return 0


def _cmd_ollama(args) -> int:
    base_dir = Path(args.dir) if args.dir else DEFAULT_CONFIG_DIR
    manager = OllamaConfigManager(base_dir, overwrite=args.overwrite)
    try:
        paths = manager.ensure()
    except FileExistsError as exc:
        print(str(exc), file=sys.stderr)
        return 3
    print(f"Wrote manifest: {paths['manifest']}")
    print(f"Wrote pull script: {paths['script']}")
    return 0


__all__ = ["main"]
