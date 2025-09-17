# Blueprint Cross-Reference

Links the major sections from blueprint.md to current repo assets.

See also: Repository Map (REPO_MAP.md) and Open Tasks (TODO.md).

| Blueprint Concept | Current Coverage | Notes |
| --- | --- | --- |
| Layer 1: Data ingestion pipeline | In progress | chat_manager ingestion package with format detection, checksum dedupe, attachments, and CLI import script. |
| Layer 2: Canonical data model | In progress | SQLite schema mirrors ingestion tables with job tracking; Postgres migrations pending. |
| Layer 3: Analysis and modeling | Not implemented | No local model orchestration or summarization code; blueprint reference only. |
| Layer 4: Correlation and re-weaving | Not implemented | Human-in-the-loop queue, scoring, and auditing absent. |
| Layer 5: Hybrid search and retrieval | Not implemented | No search services, indexes, or query fusion logic in repo. |
| Local AI infrastructure (Ollama, vLLM) | Not implemented | No tooling scripts or configs for model downloads or runtime management. |
| Import/export and interoperability | Partial | CLI `scripts/import_conversations.py` ingests exports; API surface still pending. |
| Monitoring, metrics, and performance budgets | Not implemented | CI only runs sanity tests; no metrics dashboards or budgets codified. |
| Security posture | Not implemented | SECURITY.md missing; no authn/z or hardening implemented. |
| Phase roadmap (P1-P5) | Planned | docs/BUILD_PLAN.md links to TEST_MATRIX.md, API_SURFACE.md, DB_SCHEMA.sql with phase breakdowns. |
| Smoke and sanity validation | Improved | Smoke still runs pytest/vitest; ingestion pytest suite extends coverage beyond docs checks. |
| Environment configuration | Updated | docs/ENV.md documents all variables; .env.example now aligned with ingestion settings. |
