# Environment Variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `NS_CODEX_DB_PATH` | No | `~/.local/share/ns_codex/db.sqlite3` | File path for the SQLite database used in P1. CLI/server accept `--db` override; env var provides default. |
| `NS_CODEX_SERVER_HOST` | No | `127.0.0.1` | Host interface for the local WSGI server (`runserver`). Keep loopback for security. |
| `NS_CODEX_SERVER_PORT` | No | `8000` | TCP port for the local WSGI server. |
| `NS_CODEX_OLLAMA_DIR` | No | `~/.config/ns_codex/ollama` | Output directory for generated Ollama manifests/scripts. |
| `NS_CODEX_TIMEZONE` | No | System local timezone | Optional override when normalizing timestamps during ingest. |

## Usage Notes
- All variables are optional; CLI flags take precedence over env defaults.
- `.env.example` mirrors the table with commented defaults for convenience.
- Future phases (P2+) will add model/embedding configuration variables—track them here and in the example file.
