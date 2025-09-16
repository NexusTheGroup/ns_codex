# Blueprint Cross-Reference

Links the major sections from blueprint.md to current repo assets.

See also: Repository Map (REPO_MAP.md) and Open Tasks (TODO.md).

| Blueprint Concept | Current Coverage | Notes |
| --- | --- | --- |
| Layer 1: Data ingestion pipeline | Partial | `src/ns_codex/ingest.py` parses ChatGPT & Claude exports; CLI wired via `python -m ns_codex ingest`. Attachment metadata stored in SQLite. |
| Layer 2: Canonical data model | Partial | SQLite schema mirrors Postgres tables (`docs/DB_SCHEMA.sql`), implemented by `src/ns_codex/db.py`. Entities/topics/link edges defined but not populated yet. |
| Layer 3: Analysis and modeling | Not implemented | Model orchestration deferred to P2; only Ollama manifest scaffolding exists. |
| Layer 4: Correlation and re-weaving | Not implemented | No correlation engine yet; schema placeholders present. |
| Layer 5: Hybrid search and retrieval | Partial | SQLite LIKE search via `Database.search_threads`; hybrid vector search planned for Postgres in later phases. |
| Local AI infrastructure (Ollama, vLLM) | Partial | `src/ns_codex/local_ai.py` generates manifest and pull script for required models; runtime integration TBD. |
| Import/export and interoperability | Partial | CLI import command implemented; export endpoints pending. |
| Monitoring, metrics, and performance budgets | Not implemented | No observability tooling yet. |
| Security posture | Partial | `docs/SECURITY.md` documents assumptions; auth hardening pending. |
| Phase roadmap (P1-P5) | Partial | `docs/BUILD_PLAN.md` + linked deliverables published. |
| Smoke and sanity validation | Expanded | Pytest suite covers schema/import/web/CLI; existing JS sanity tests unchanged. |
| Environment configuration | Partial | `docs/ENV.md` + `.env.example` detail available variables. |
