# Environment Configuration — Personal AI Chat Manager

All runtime variables are loaded from a `.env` file (development) or the host environment (staging/production). Keep `.env.example` in sync with this table.

## Database & Cache
| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `DATABASE_URL` | Yes | `postgresql://user:pass@localhost:5432/ai_chat_manager` | PostgreSQL connection string; must include pgvector extension. |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` | Redis instance used for caching, job coordination, and rate limiting. |

## Model Runtime
| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `EMBEDDING_MODEL` | Yes | `BAAI/bge-m3` | Embedding model identifier loaded via Ollama/vLLM. |
| `RERANKER_MODEL` | Yes | `BAAI/bge-reranker-v2-m3` | Cross-encoder reranker used during hybrid search. |
| `CHAT_MODEL` | Yes | `llama3.1:70b` | Primary conversational/summarization model. |
| `CODE_MODEL` | Yes | `codellama:34b` | Specialized model for code analysis tasks. |

## Correlation & Search Tuning
| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `CORRELATION_THRESHOLD` | No | `0.7` | Minimum link confidence before a thread pair is surfaced automatically. |
| `SEMANTIC_THRESHOLD` | No | `0.8` | Cosine similarity cutoff for matching embeddings. |
| `TEMPORAL_WINDOW_DAYS` | No | `30` | Restricts automatic correlations to conversations within N days. |
| `MAX_BATCH_SIZE` | No | `32` | Maximum documents/messages processed per inference batch. |
| `WORKER_CONCURRENCY` | No | `6` | Number of concurrent background workers ingesting or reweaving. |
| `CACHE_SIZE_MB` | No | `1024` | In-memory cache budget (MB) for search/materialized snippets. |

## Network & Security
| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `API_KEY` | No | _(empty)_ | Optional bearer token required when exposing APIs beyond localhost. Leave unset for local-only mode. |
| `BIND_ADDRESS` | No | `127.0.0.1` | Interface the API server listens on. Change when enabling LAN access. |
| `CORS_ORIGINS` | No | _(empty)_ | Comma-separated origins allowed to call the API. Empty disables CORS. |

## Feature Flags
| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `ENABLE_WEBHOOKS` | No | `false` | Toggle delivery of webhook notifications for imports and correlations. |
| `ENABLE_REWEAVE_SCHEDULER` | No | `true` | Controls auto-scheduling of correlation jobs. |
| `BACKUP_ENABLED` | No | `true` | Enables scheduled backups for the PostgreSQL database. |

## General Runtime
| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `APP_ENV` | No | `development` | Logical environment label (`development`, `test`, `production`). Affects logging and diagnostics. |

> Keep `.env` files out of version control. Update both this document and `.env.example` whenever configuration changes.
