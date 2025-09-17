# Build Plan — Personal AI Chat Manager

## Purpose
Coordinate phased delivery of the local-first conversation intelligence platform defined in blueprint.md. The plan assumes a single-user deployment with PostgreSQL + pgvector, Redis caching, and local LLM hosting (Ollama or vLLM) per the architecture blueprint. Each phase ends with smoke coverage via scripts/smoke_test.sh and CI green on the default branch.

## Linked Deliverables
- [docs/TEST_MATRIX.md](./TEST_MATRIX.md)
- [docs/API_SURFACE.md](./API_SURFACE.md)
- [docs/DB_SCHEMA.sql](./DB_SCHEMA.sql)
- [docs/TODO.md](./TODO.md)

## Phase Overview
| Phase | Focus | Key Outcomes | Exit Gates |
| --- | --- | --- | --- |
| **P0 — Planning** | Align scope, architecture, and validation strategy. | This document plus linked specs; TODO and TASKLOG updated. | Route Compliance satisfied; blueprint cross-ref updated. |
| **P1 — Data Foundations** | Stand up storage, ingestion skeleton, and normalization pipeline (Layers 1–2). | PostgreSQL schema deployed; checksum and MIME detection services; unit and integration tests for ingestion. | Smoke and CI green; importer handles ChatGPT and Claude happy paths. |
| **P2 — Intelligence Core** | Implement analysis, entity/topic extraction, correlation engine (Layers 3–4). | Local model orchestration, embedding generation, correlation workflows with human review queue. | Regression and performance baselines met (<200ms search target pre-UI). |
| **P3 — Experience Layer** | Build hybrid search, API, and web experience (Layers 5–7). | REST API covering /v1 endpoints, search facets, thread explorer, saved searches. | E2E smoke covers core journeys; docs/API_SURFACE.md kept current. |
| **P4 — Polish & Ops** | Operational hardening, developer experience, observability (Layers 8–10). | Health/readiness probes, environment docs, release notes, automation for reindex, backups, performance budgets. | scripts/smoke_test.sh adds perf/security checks; docs/CHANGELOG.md updated. |
| **P5 — Scale & Hardening** | Optimization for sustained use, resilience, backup/recovery (Layers 9–11). | Caching strategies, failover drills, export pipelines, security posture docs. | Load and performance gates met; recovery runbooks tested. |

## Milestone Detail
### P0 — Planning
- Capture scope, constraints, and acceptance criteria (this plan, linked artifacts, TODO plus TASKLOG entries).
- Confirm repo guardrails (Route Compliance, CI) are ready for build phases.

### P1 — Data Foundations (Layers 1–2)
- Provision PostgreSQL plus pgvector and Redis in local dev; add migration workflow.
- Implement ingestion services: format detection, checksum deduplication, timestamp and identity normalization, attachment extraction.
- Deliver import CLI/API skeleton with retryable job metadata.
- Validate via unit tests on parsers and integration tests around normalization pipeline (see docs/TEST_MATRIX.md).

### P2 — Intelligence Core (Layers 3–4)
- Integrate local model runtime (Ollama or vLLM); configure embedding and reranker models.
- Implement entity/topic extraction jobs, metadata enrichment, and link-scoring policies.
- Build human-in-the-loop queue for link validation; persist audit logs.
- Extend tests for model wrappers, scoring heuristics, and correlation accuracy.

### P3 — Experience Layer (Layers 5–7)
- Stand up hybrid search stack (full-text plus vector fusion) with caching.
- Develop REST API endpoints covering search, threads, entities, links, import/export, health per docs/API_SURFACE.md.
- Build web UI: global search bar, facet rail, thread detail, saved searches, knowledge wiki integration.
- Add Vitest and E2E coverage for UI flows and API contract tests.

### P4 — Polish & Ops (Layers 8–10)
- Implement health/readiness probes, stats endpoints, structured logging, and metrics exporters.
- Harden configuration: .env management, secrets handling, backup/reindex automation, smoke/perf gates.
- Document operational playbooks, environment expectations (update docs/ENV.md, docs/CHANGELOG.md, release notes).

### P5 — Scale & Hardening (Layers 9–11)
- Tune PostgreSQL (partitioning, vacuum policies), Redis caching tiers, and vector index parameters.
- Add import/export resilience: resumable uploads, job queue monitoring, rollback/retry strategies.
- Implement backup/restore, disaster recovery rehearsals, monitoring dashboards, security reviews (auth, rate limiting, IP allowlists).
- Establish long-term metrics: correlation accuracy, search latency, storage efficiency, uptime.

## Cross-Cutting Tracks
- **Quality and Testing:** Follow docs/TEST_MATRIX.md for required coverage at each phase; keep scripts/smoke_test.sh in sync.
- **Documentation:** Update docs/TODO.md, docs/CHANGELOG.md, and personas/prompts as scope evolves; include Finding Cards in PRs.
- **Tooling:** Maintain deterministic installs (pnpm, uv/pytest), formatters, and pre-commit hooks; ensure CI parity.
- **Security and Privacy:** Enforce local-only defaults, audit trails, and safe attachment handling from the earliest data-ingestion work.

## Dependencies and Assumptions
- Local developer hardware with GPU (RTX 3090 or 3080 Ti) and 64GB RAM for model workloads.
- PostgreSQL 15 or later with pgvector extension; Redis 7 or later for caching/search.
- Ollama (or equivalent) capable of hosting Llama 3.1 70B, Mixtral 8x7B, CodeLlama 34B; embeddings via BGE-M3; reranker via bge-reranker-v2-m3.
- Network access is optional; default binding to 127.0.0.1 with optional API key/IP allowlist when opened.

## Success Tracking
- **Engineering KPIs:** Import throughput at least 1000 messages per minute, search latency at most 200ms p95, correlation acceptance at least 85 percent, storage at most 50MB per 1k messages.
- **Operational KPIs:** Health/readiness under 100ms/500ms, uptime at least 99.9 percent (local), backups validated per release.
- **Process KPIs:** Every feature branch includes tests, docs, Finding Cards, and passes smoke plus CI.

## Next Steps
- Validate this plan with stakeholders (codex personas) and begin P1 workstream execution.
- Flesh out docs/ENV.md and .env.example alongside infrastructure setup.
- Draft SECURITY.md and risk register early in P1 to track privacy and local-first guarantees.
