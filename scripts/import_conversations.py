#!/usr/bin/env python
"""CLI helper to run the ingestion pipeline on export files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from chat_manager import AttachmentStorage, ChatDatabase
from chat_manager.ingest import ImportConfig, ImportPipeline, SupportedFormat


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "sources",
        nargs="+",
        help="Paths to export files or directories containing ChatGPT/Claude exports.",
    )
    parser.add_argument(
        "--database",
        default=Path("data/ingest.sqlite"),
        type=Path,
        help="SQLite database path for storing normalized records (default: data/ingest.sqlite).",
    )
    parser.add_argument(
        "--attachments",
        default=Path("data/attachments"),
        type=Path,
        help="Directory to persist attachment binaries (default: data/attachments).",
    )
    parser.add_argument(
        "--platform-hint",
        choices=[fmt.value for fmt in SupportedFormat],
        help="Optional format hint to skip auto-detection.",
    )
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Continue processing additional files when one fails (default: stop on first failure).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    db_path: Path = args.database
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = ChatDatabase(db_path)
    db.initialize()

    attachments_path: Path = args.attachments
    storage = AttachmentStorage(attachments_path)

    pipeline = ImportPipeline(db, storage)
    config = ImportConfig(
        platform_hint=SupportedFormat(args.platform_hint) if args.platform_hint else None,
        allow_partial=args.allow_partial,
    )

    result = pipeline.ingest([Path(src) for src in args.sources], config)

    if not result.success:
        print("Import completed with issues:")
        for error in result.errors:
            print(f"  - {error}")
    else:
        print("Import completed successfully.")

    print(
        "Processed={processed} skipped={skipped} threads={threads} messages={messages} attachments={attachments}".format(
            processed=result.files_processed,
            skipped=result.files_skipped,
            threads=result.threads_created,
            messages=result.messages_created,
            attachments=result.attachments_saved,
        )
    )

    if not result.success:
        print("See import_jobs table for additional metadata.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

