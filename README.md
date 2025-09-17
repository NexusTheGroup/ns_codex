# Personal AI Chat Manager

Local-first system for ingesting and reasoning over AI conversations from multiple platforms. This repository implements the
phase-oriented plan documented in [docs/BUILD_PLAN.md](docs/BUILD_PLAN.md). P1 focuses on the storage and ingestion foundation
for ChatGPT and Claude exports.

## Key Capabilities (P1)
- SQLite-backed implementation of the PostgreSQL schema described in `docs/DB_SCHEMA.sql` (scoped to ingestion tables).
- Import pipeline with format detection, checksum deduplication, timestamp normalization, and attachment extraction.
- Filesystem-backed attachment storage with deterministic hashing layout.
- Python CLI (`scripts/import_conversations.py`) to normalize exports into the local database.
- Pytest coverage verifying end-to-end normalization, dedupe handling, and metadata persistence.

## Repository Structure
- `chat_manager/` — Python package containing database helpers, ingestion parsers, and storage utilities.
- `docs/` — Architecture, plan, and ops documentation.
- `scripts/` — Smoke test, setup script, and ingestion CLI.
- `tests/` — Pytest and Vitest suites; ingestion fixtures live in `tests/python/fixtures`.

## Getting Started
1. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install test dependencies (only `pytest` required for Python stack):
   ```bash
   pip install -U pytest
   pnpm install
   ```
3. Run the full smoke to verify everything:
   ```bash
   bash scripts/smoke_test.sh
   ```

## Running the Import CLI
```bash
scripts/import_conversations.py exports/chatgpt.json --database data/ingest.sqlite --attachments data/attachments
```

Optional arguments:
- `--platform-hint` — choose `chatgpt` or `claude` to bypass auto-detection.
- `--allow-partial` — continue processing additional files when one fails.

The CLI creates/updates the SQLite database and attachment directory automatically. Import metadata is stored in the
`import_jobs` and `import_files` tables for auditability.

## Environment Variables
See [docs/ENV.md](docs/ENV.md) for canonical definitions. Key variables for P1 include:
- `DATABASE_URL` / `PACM_DATABASE_URL` — connection string for persistence (defaults to SQLite path for dev).
- `ATTACHMENT_STORAGE_PATH` — base directory for attachment binaries.
- `REDIS_URL` — reserved for later caching layers.

## Testing
- Python: `pytest`
- JavaScript: `pnpm test`
- Combined smoke: `bash scripts/smoke_test.sh`

Each change should update documentation, extend tests as needed, and keep smoke + CI runs green.
