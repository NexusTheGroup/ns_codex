# Test Matrix — Personal AI Chat Manager

## Scope
Testing spans ingestion through user experience plus operational tooling. Each feature branch must keep CI green (GitHub Actions runs pytest and pnpm test) and ensure scripts/smoke_test.sh returns zero.

## Coverage Overview
| Layer / System | Objectives | Unit | Integration | End to End | Performance & Reliability | Security & Privacy | Tooling |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Data Ingestion (format detection, checksum dedup, attachment extraction) | Parse imports correctly, deduplicate payloads, extract attachments safely. | Parser helpers, checksum utilities, MIME detector rules. | Import pipeline combining detection, normalization, filesystem writes with Postgres fixtures. | Upload ZIP/JSON export via CLI or API and confirm normalized records. | Measure ingest throughput (msgs/min) and memory; assert retry backoff on large files. | Validate attachment scanning, path traversal protections, source attribution integrity. | pytest with factory fixtures; sample exports under tests/fixtures. |
| Canonical Data Model (PostgreSQL + Redis) | Persist normalized entities with referential integrity and performant indexes. | Schema migrations, constraint checks, JSON metadata serializers. | Database interactions through repositories/ORM; Redis caching for hot queries. | Simulate import→query flows validating message/thread lookup. | Benchmark query latency (FTS + vector) and cache hit ratios. | Ensure PII redaction, audit logging for mutations. | Alembic or sqitch migrations; data seeding scripts. |
| Analysis & Correlation (embeddings, entity/topic extraction, link engine) | Generate embeddings, classify entities/topics, score correlations. | Model wrapper utilities, scoring heuristics, feature extraction. | Pipelines combining embedding store, entity extraction, link scoring, human queue updates. | Scenario tests from conversation corpora verifying related-thread surfacing. | Evaluate correlation accuracy (>85 percent), embedding latency, reranker throughput. | Verify local-only model execution, no external calls, audit trails on overrides. | Pytest with GPU-aware marks; golden datasets for correlation expectations. |
| Search & Retrieval (hybrid ranking, saved searches) | Deliver relevant results across FTS and vector search with filters. | Query builders, filter serialization, scoring merge logic. | Postgres + Redis search stack with real data slices. | UI or API flows searching, filtering, saving queries. | Track search latency (p95) and cache warmup budgets. | Ensure result redaction for restricted attachments, enforce rate limits when remote access enabled. | Vitest for client libs, pytest for backend API contract tests. |
| API & Web Application (REST /v1, UI) | Provide stable API contracts and accessible UI for single-user workflows. | Controller serializers, validation schemas, React/Vue components. | API contract tests via pytest + httpx; UI integration tests with Vitest or Playwright. | Browser-level flows: search, thread view, link validation, saved searches. | Monitor UI bundle size, API response times, websocket or SSE if added. | Enforce local auth defaults, optional API key/IP whitelist, CSRF protection. | Vitest, Playwright/Cypress, contract tests in pytest. |
| Operations & Observability (health, jobs, metrics, backups) | Keep system observable, recoverable, and documented. | Cron/job schedulers, metrics emitters, configuration parsers. | Full stack smoke invoking import job, link reweave, backup routine. | Disaster recovery drill restoring from backup; failover of vector index. | Track health/ready endpoints, backup duration, restore success. | Access control on maintenance endpoints, ensure audit logging on admin actions. | Bash smoke script, promtool/unit tests for alert rules. |
| Docs & Governance (docs, TODO, Finding Cards) | Keep docs accurate and guardrails enforced. | Markdown linting helpers, template validators. | Route compliance workflow verifying plan/TODO updates. | Release review checklists and persona sign-off. | Monitor doc build time (if static site) and link validation. | Review that no secrets or PII land in docs. | pre-commit hooks, markdown link checker. |

## Test Execution Matrix
- **Local default:** pytest -q, pnpm test, scripts/smoke_test.sh.
- **CI (GitHub Actions):** primary workflow runs Python tests then Node tests; extend with linting, perf, and security jobs as they come online.
- **Scheduled jobs:** nightly smoke (same as scripts/smoke_test.sh) plus weekly longer-running perf/security suites once implemented.

## Data & Fixtures
- Maintain sample exports (ChatGPT, Claude, Ollama) under tests/fixtures for deterministic ingestion tests.
- Provide synthetic threads with entities/topics and correlation ground truth for analytics validation.
- Use anonymized attachments (code, markdown, binary) to test extraction and indexing without leaking PII.

## Quality Gates by Phase
| Phase | Minimum Coverage | Additional Notes |
| --- | --- | --- |
| P0 | Planning docs accounted for; sanity tests remain green. | Route Compliance ensures docs/BUILD_PLAN.md, TEST_MATRIX.md, API_SURFACE.md, DB_SCHEMA.sql tracked. |
| P1 | Parsers, normalization, and schema migrations covered by unit/integration tests; smoke runs import pipeline. | Begin tracking ingest throughput metrics and error handling. |
| P2 | Analytics pipelines validated with golden datasets; correlation accuracy measured. | Add GPU-aware tests and ensure reproducibility with seeded random values. |
| P3 | API contract tests and UI end-to-end coverage protecting core workflows. | Introduce accessibility and UX regression checks. |
| P4 | Observability, backup/restore, and perf thresholds enforced. | Include chaos or fault-injection scenarios for job runners. |
| P5 | Scale, security, and recovery drills automated; load tests gate releases. | Document fallback procedures and DR rehearsal evidence. |

## Reporting & Tooling
- Capture test results via CI artifacts; integrate coverage reports before end of P2.
- Align Finding Cards with failing tests or risk areas to keep governance tight.
- Track key metrics (import throughput, search latency, correlation accuracy) in docs/CHANGELOG.md or dashboards once available.

