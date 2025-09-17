# API Surface — Personal AI Chat Manager

## Design Principles
- RESTful JSON interface hosted locally; default binding 127.0.0.1 with no auth for single-user mode.
- Versioned routes under /v1 for forward compatibility.
- Consistent response envelope: { "data": ..., "meta": { "request_id": string, "duration_ms": integer } }.
- Errors follow { "error": { "code": string, "message": string, "details": array } }.

## Endpoint Catalog
### Search & Discovery
| Method | Path | Description | Key Params | Success Response |
| --- | --- | --- | --- | --- |
| GET | /v1/search | Hybrid search across messages, threads, attachments. | q (required), filters (JSON), limit, offset, sort, explain. | 200 with ranked results, snippets, scoring metadata when explain flag true. |
| GET | /v1/search/suggest | Auto-complete for queries, entities, topics. | q (required), type (query, entity, topic), limit. | 200 with suggestion list ordered by confidence. |
| POST | /v1/search/saved | Save a search definition for quick recall. | Body with name, query, filters, pin flag. | 201 with saved-search identifier and timestamps. |
| GET | /v1/search/saved | List saved searches for the user. | pagination params. | 200 with array of saved searches. |

### Content Access
| Method | Path | Description | Key Params | Success Response |
| --- | --- | --- | --- | --- |
| GET | /v1/threads | List threads matching filters; supports pagination. | filters (platform, topic, tag, date range), limit, offset, sort (date, quality). | 200 with thread summaries and aggregate stats. |
| GET | /v1/threads/{id} | Retrieve a single thread with full message history. | include_entities flag, include_attachments flag. | 200 with thread metadata, messages, related entities/topics. |
| GET | /v1/threads/{id}/related | Fetch correlated threads with scores and evidence. | limit, link_type, min_score. | 200 with related thread list plus score breakdown. |
| GET | /v1/messages/{id} | Fetch individual message with context window. | include_thread flag, include_links flag. | 200 with message payload, attachments, neighbor messages. |
| GET | /v1/attachments/{id} | Download or fetch metadata for attachment. | variant=metadata or download. | 200 with metadata or file stream; 404 if not owned. |

### Entity & Topic Management
| Method | Path | Description | Key Params | Success Response |
| --- | --- | --- | --- | --- |
| GET | /v1/entities | List canonical entities with filters and stats. | type, name query, confidence range, sort. | 200 with entity records and mention counts. |
| GET | /v1/entities/{id} | Fetch entity detail plus related threads/messages. | include_topics flag, include_links flag. | 200 with entity metadata, alias list, connections. |
| POST | /v1/entities/{id}/merge | Merge duplicate entities into canonical record. | Body specifying target_id and conflict resolution notes. | 202 accepted; merge job queued with audit trail. |
| GET | /v1/topics | Return topic hierarchy with engagement stats. | parent_id, auto_generated flag, confidence threshold. | 200 with nested topic structure. |
| POST | /v1/topics | Create custom topic. | Body with name, description, keywords, parent_topic_id. | 201 with new topic identifier. |
| PUT | /v1/topics/{id} | Update topic metadata or status. | Body with fields to update; supports toggling auto_generated. | 200 with updated topic. |

### Link Management
| Method | Path | Description | Key Params | Success Response |
| --- | --- | --- | --- | --- |
| GET | /v1/links | List correlation edges with filtering. | source_thread_id, link_type, validation status, min_score. | 200 with edges including evidence bits and policy version. |
| POST | /v1/links | Create manual link between threads. | Body with source_thread_id, target_thread_id, link_type, notes. | 201 with new edge record. |
| PUT | /v1/links/{id} | Update link score or validation flags. | Body with score adjustments, validated_by_human, human_override. | 200 with updated edge. |
| DELETE | /v1/links/{id} | Remove a correlation edge. | none. | 204 on success. |
| POST | /v1/links/reweave | Trigger correlation re-analysis across corpus. | query scope, policy_version, dry_run flag. | 202 accepted; job identifier returned for monitoring. |
| GET | /v1/links/queue | Retrieve human review queue for pending edges. | limit, reviewer filters. | 200 with queue entries sorted by priority. |

### Import & Export
| Method | Path | Description | Key Params | Success Response |
| --- | --- | --- | --- | --- |
| POST | /v1/import | Upload conversation exports (multipart). | files array, platform hints, dry_run flag. | 202 accepted; import job identifier returned. |
| GET | /v1/import/jobs | List import jobs with status. | pagination, status filters. | 200 with job list including progress metrics and errors. |
| GET | /v1/import/jobs/{id} | Fetch single job status plus per-file breakdown. | none. | 200 with job status; 410 if job purged per retention policy. |
| POST | /v1/export | Request corpus export. | Body with scope (threads/topics/time), format options. | 202 accepted; export job identifier returned. |
| GET | /v1/export/jobs/{id} | Download export artifact or check status. | variant=metadata or download. | 200 with metadata or file stream when ready; 202 while processing. |

### System & Maintenance
| Method | Path | Description | Success Response |
| --- | --- | --- | --- |
| GET | /v1/health | Lightweight liveness probe. | 200 with status=healthy and timestamp. |
| GET | /v1/ready | Deep readiness verifying Postgres, Redis, model loading, disk space. | 200 when all checks pass; 503 with failing components listed. |
| GET | /v1/stats | System metrics snapshot (counts, storage, latency percentiles). | 200 with metrics payload; cached for short TTL. |
| POST | /v1/maintenance/reindex | Trigger rebuild of search/vector indexes. | 202 accepted; maintenance job identifier returned. |

## Pagination & Filtering
- Default limit 25, maximum 100. Responses include meta.total_count and meta.next_offset when more data exists.
- Filters accept JSON object with keys: platforms, roles, topics, entities, tags, date_range, content_type.
- Sorting options vary per resource but share keywords: relevance (default), created_at, updated_at, quality_score.

## Conventions
- All timestamps use ISO 8601 UTC.
- Text fields support Markdown; attachments reference storage paths resolved via server-side streaming.
- Long-running jobs (import, export, reweave) emit job identifiers and surface progress percent plus error arrays.
- Optional webhooks for local automations; otherwise polling via job endpoints.

## Authentication & Security
- Default local mode: no authentication, bind to loopback interface only.
- Optional LAN mode: single API key passed in Authorization Bearer header plus IP allowlist configuration.
- Rate limiting: soft limit 60 requests per minute per allowed IP when LAN mode enabled.
- Request and response logging stored locally with rotation; sensitive fields (API key, tokens) redacted in logs.

## Error Codes (examples)
| Code | Meaning | Typical HTTP |
| --- | --- | --- |
| validation_failed | Input failed schema or business validation. | 400 |
| not_found | Resource missing or not visible to user. | 404 |
| conflict | Concurrent update or duplicate detection triggered. | 409 |
| model_offline | Required local model unavailable. | 503 |
| rate_limited | Request exceeded configured limits. | 429 |

## Extensibility Notes
- Future versions may add GraphQL overlay or websocket channel for live updates; keep /v1 stable and version new features under /v2 when required.
- Consider fine-grained scopes when introducing multi-user mode; reuse API key mechanism as stepping stone.
- Document delta in docs/API_SURFACE.md and capture change summary in docs/CHANGELOG.md release notes.
