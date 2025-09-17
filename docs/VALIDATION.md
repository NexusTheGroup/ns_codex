# Documentation Validation

Summary of gaps or contradictions discovered during repository scan. Update this file whenever guardrails reveal issues that
still need resolution.

## Outstanding Artifacts
- `SECURITY.md` and initial risk register remain todo (see docs/TODO.md).
- PostgreSQL/pgvector migration workflow (Alembic) still pending; current implementation relies on SQLite helper.
- Blueprint formatting is still single-line, complicating diff reviews; normalization task remains open.

## Alignment Notes
- P0 deliverables (BUILD_PLAN, TEST_MATRIX, API_SURFACE, DB_SCHEMA) now live in `docs/` as required.
- Environment documentation and `.env.example` are synchronized with the ingestion pipeline defaults.
- docs/CHANGELOG.md includes Release Notes tracking for ongoing phases.

## Checks Performed
- Reviewed markdown/doc set after P1 ingestion work.
- Verified CI workflow still executes pytest and pnpm tests; smoke script exercises new ingestion tests.
