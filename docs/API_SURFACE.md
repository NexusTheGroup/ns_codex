# API Surface (P1)

## HTTP (WSGI App)

### `GET /`
- **Description**: Render HTML landing page with search form and recent threads.
- **Query Params**:
  - `q` (optional): substring filter applied to thread titles and message bodies.
- **Response**: `text/html` page listing matching threads with snippets.

### `GET /thread/{thread_id}`
- **Description**: Render HTML view of an individual conversation.
- **Response**: `text/html` showing ordered messages and attachment metadata.

### `GET /api/threads`
- **Description**: JSON endpoint for listing threads.
- **Query Params**:
  - `q` (optional): substring search against titles/messages.
  - `limit` (optional, default 20): max number of results.
- **Response**: `application/json` array of thread summaries: `{id, title, platform, updated_at, message_count, total_tokens}`.

### `GET /api/threads/{thread_id}`
- **Description**: JSON detail for a thread.
- **Response**: `{id, title, platform, created_at, updated_at, messages:[{role, content, timestamp, attachments:[...]}, ...]}`.
- **Errors**: `404` if thread not found.

### `GET /healthz`
- **Description**: Lightweight readiness probe.
- **Response**: `200 OK` with body `"ok"` when database reachable.

## CLI (`python -m ns_codex`)

### `ingest`
- **Usage**: `python -m ns_codex ingest --platform {chatgpt|claude} --db <path> <export_file>`
- **Behavior**: Parses export file, normalizes data, persists to database. Creates database file if missing.

### `runserver`
- **Usage**: `python -m ns_codex runserver --db <path> [--host 127.0.0.1] [--port 8000]`
- **Behavior**: Boots WSGI server using `wsgiref.simple_server`. Intended for local development.

### `ollama-config`
- **Usage**: `python -m ns_codex ollama-config --dir <path>`
- **Behavior**: Writes manifest (`ollama-manifest.json`) and pull script (`pull-models.sh`) describing recommended models.
- **Options**:
  - `--overwrite`: allow replacing existing files (otherwise safe-write).

## Python Module APIs

### `ns_codex.db.Database`
- `Database(path: str)` constructor creates or opens SQLite database.
- `save_thread(platform_name, thread)` persists normalized thread bundle.
- `search_threads(query: str | None, limit: int = 20)` returns list of thread summaries.
- `get_thread(thread_id: str)` fetches thread + messages + attachments.
- `list_recent_threads(limit: int = 20)` convenience wrapper when no query provided.

### `ns_codex.ingest.parse_chatgpt_export(path)` / `parse_claude_export(path)`
- Return list of `ThreadBundle` dataclasses ready for persistence.
- Perform checksum dedupe and timezone normalization.

### `ns_codex.local_ai.OllamaConfigManager`
- `write_manifest(models)` persists manifest JSON.
- `write_pull_script(models)` emits idempotent `ollama pull` helper script.
- `ensure(models)` convenience to create both and return paths.

