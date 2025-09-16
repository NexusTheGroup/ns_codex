# Build Plan

## Phase Overview
- **P0 – Planning**: Complete foundational docs (build plan, test matrix, API surface, DB schema) and security posture. ✅
- **P1 – Foundation** *(current phase)*: Stand up the local data layer, ingestion pipeline for ChatGPT & Claude, Ollama configuration helpers, and the minimal web UI for browsing/searching stored threads.
- **Future Phases**: P2 (analysis), P3 (correlation/search), P4 (polish & ops), P5 (scale) will build on the P1 substrate.

## Scope for P1
1. **Data Layer**
   - Bootstrap a local SQLite-backed store that mirrors the Postgres/pgvector schema defined in [`docs/DB_SCHEMA.sql`](DB_SCHEMA.sql).
   - Provide Python accessors for creating platforms, threads, messages, and attachments, along with thread search helpers.
2. **Import Pipeline**
   - Implement parsers for ChatGPT `conversations.json` exports and Claude JSONL exports.
   - Normalize message chronology, estimate token counts, and persist via the data layer.
3. **Local AI Configuration**
   - Generate Ollama model manifests and pull scripts so users can provision embedding/chat models with one command.
4. **Web Experience**
   - Ship a lightweight WSGI application offering HTML + JSON endpoints for searching and reading conversations.
5. **Tooling & Docs**
   - Expose the new functionality via `python -m ns_codex` CLI commands (`ingest`, `runserver`, `ollama-config`).
   - Document APIs, schema, tests, env vars, and security posture.

## Deliverables & Links
- [`docs/TEST_MATRIX.md`](TEST_MATRIX.md)
- [`docs/API_SURFACE.md`](API_SURFACE.md)
- [`docs/DB_SCHEMA.sql`](DB_SCHEMA.sql)
- [`docs/ENV.md`](ENV.md)
- [`docs/SECURITY.md`](SECURITY.md)
- [`docs/CHANGELOG.md`](CHANGELOG.md)

## Implementation Plan
1. **Schema & Storage (Day 1)**
   - Translate blueprint entities into SQL (UUID keys, FK constraints, attachment metadata, audit log, etc.).
   - Create `Database` helper that executes the schema, exposes ingest/query methods, and indexes for search.
2. **Importers (Day 1-2)**
   - Define ingestion dataclasses for normalized threads/messages/attachments.
   - Build ChatGPT + Claude parsers with checksum dedupe, timezone normalization, and attachment capture.
   - Wire importers into the database writer.
3. **Local AI Manifests (Day 2)**
   - Capture required models (BGE-M3, reranker, Llama 3.1, CodeLlama) in a JSON manifest + shell script generator.
   - Allow CLI to update manifests in a configurable directory.
4. **Web Layer (Day 2-3)**
   - Implement WSGI app with HTML templates and JSON API.
   - Add search/filter capabilities backed by database helper.
5. **Testing & Docs (Day 3)**
   - Cover database, importers, API/web, CLI, and Ollama config in pytest.
   - Update docs, TODO, task log, and changelog.

## Risks & Mitigations
- **Export Format Drift**: Parsers may break if vendors change exports → keep modular parser classes with fixture-driven tests.
- **Search Performance**: SQLite `LIKE` search is limited → plan to swap with Postgres FTS/pgvector in P2 while keeping API contract stable.
- **Local Model Footprint**: Large downloads may overwhelm users → manifest includes size notes and script is opt-in.
- **Security**: Web UI intentionally local-only, CSRF-free, and read-only in P1.

## Acceptance for P1
- Import ChatGPT + Claude fixtures into the SQLite store via CLI.
- Search/view stored threads through both HTML and JSON endpoints.
- Ollama manifest/script generated with listed models.
- All tests (`pytest`, `pnpm test`, `scripts/smoke_test.sh`) pass locally.
