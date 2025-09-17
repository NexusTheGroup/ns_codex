# Environment Configuration — Personal AI Chat Manager

All runtime variables must be documented here and reflected in `.env.example`. Values are read via `os.environ` in future phases;
for P1 the ingestion CLI accepts command-line arguments but honours the same defaults.

## Core Persistence
| Variable | Required | Default | Notes |
| --- | --- | --- | --- |
| `DATABASE_URL` | Yes | `sqlite:///data/ingest.sqlite` (dev) | Connection string for the primary database. Use `postgresql://` in production with pgvector enabled. |
| `PACM_DATABASE_URL` | Alias | `DATABASE_URL` | Canonical name used by future orchestration. Set only if you need a different DSN than `DATABASE_URL`. |
| `ATTACHMENT_STORAGE_PATH` | Yes | `data/attachments` | Base directory for persisted attachment binaries. The ingestion CLI creates the path when missing. |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Reserved for caching/search layers coming online in P2+. Keep populated even if Redis is not yet running. |

## Import Pipeline Behaviour
| Variable | Required | Default | Notes |
| --- | --- | --- | --- |
| `IMPORT_PLATFORM_HINT` | No | _auto-detect_ | Override format detection (`chatgpt` or `claude`). Mirrors the `--platform-hint` CLI flag. |
| `IMPORT_ALLOW_PARTIAL` | No | `false` | When `true`, the importer continues after encountering a failure. Useful for bulk backfills. |
| `IMPORT_ATTACHMENT_MAX_BYTES` | No | `10485760` (10 MiB) | Soft guardrail for attachment size; parser raises if exceeded once enforcement is wired up. |
| `IMPORT_TMP_DIR` | No | System temp | Directory for staging extracted ZIP payloads when required. |

## Model Runtime (Planned)
| Variable | Required | Default | Notes |
| --- | --- | --- | --- |
| `EMBEDDING_MODEL` | Yes (P2+) | `BAAI/bge-m3` | Embedding model identifier for local runtime. |
| `RERANKER_MODEL` | Yes (P2+) | `BAAI/bge-reranker-v2-m3` | Cross-encoder for reranking search results. |
| `CHAT_MODEL` | Yes (P2+) | `llama3.1:70b` | Primary dialogue model served by Ollama/vLLM. |
| `CODE_MODEL` | Optional | `codellama:34b` | Code-focused assistant. |

## Network & Security
| Variable | Required | Default | Notes |
| --- | --- | --- | --- |
| `API_KEY` | Optional | _empty_ | Single-user API key when exposing REST surface beyond localhost. Leave blank for local-only mode. |
| `BIND_ADDRESS` | Yes | `127.0.0.1` | Interface binding for API/UI servers. |
| `CORS_ORIGINS` | Optional | _empty_ | Comma-separated allow-list for browser origins. |

## Operational Flags
| Variable | Required | Default | Notes |
| --- | --- | --- | --- |
| `ENABLE_WEBHOOKS` | No | `false` | Enables outbound webhooks for job lifecycle notifications. |
| `ENABLE_REWEAVE_SCHEDULER` | No | `true` | Controls background correlation refresh jobs. |
| `BACKUP_ENABLED` | No | `true` | Toggle for scheduled backups once implemented. |
| `APP_ENV` | Yes | `development` | Environment name used for logging/metrics labelling. |

### Management Notes
- Keep `.env.example` synchronized with this document.
- Secrets (API keys, tokens) must be injected via environment variables or secret managers—never committed to the repository.
- Update this file whenever new configuration surfaces in code or scripts.
