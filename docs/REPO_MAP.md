# Repository Map

See also: Blueprint Cross-Reference (CROSSREF.md) · Open Tasks (TODO.md).

## High-Level Layout
- root/
  - .editorconfig
  - .pre-commit-config.yaml
  - .husky/
  - AGENTS.md
  - blueprint.md
  - chat_manager/
  - docs/
  - package.json · pnpm-lock.yaml
  - pyproject.toml
  - scripts/
  - tests/
  - .github/

> node_modules/, .venv/, and VCS metadata omitted for brevity.

## Inventory
| Area | Entry | Build Tool | Configs | Tests? | Notes |
| --- | --- | --- | --- | --- | --- |
| Governance | AGENTS.md; prompts.md; personas.md | n/a | n/a | n/a | Process, personas, and runbooks. |
| Product Scope | blueprint.md | n/a | n/a | sanity tests | Single-line Markdown blueprint driving all phases. |
| Python Backend | chat_manager/ | pytest | pyproject.toml | tests/python/test_ingestion_pipeline.py | SQLite-backed ingestion pipeline and persistence helpers. |
| Docs & Logs | docs/ | markdown tooling | ENV.md; BUILD_PLAN.md; TEST_MATRIX.md; API_SURFACE.md; DB_SCHEMA.sql; TODO.md; VALIDATION.md; CHANGELOG.md | n/a | Planning, environment, and validation docs. |
| Automation | scripts/ | bash/python | setup.sh; smoke_test.sh; import_conversations.py | smoke script runs pytest/pnpm | CLI helper for running ingestion from exports. |
| Tests | tests/ | pytest; vitest | pyproject.toml; package.json | yes | Pytest covers ingestion pipeline; Vitest sanity remains for blueprint/docs presence. |
| CI/CD | .github/workflows/*.yml | GitHub Actions | ci.yml; route-compliance.yml | yes | CI runs pytest then pnpm; route compliance enforces doc updates. |
| Tooling | .pre-commit-config.yaml; .husky/ | pre-commit; husky | same | n/a | Local lint/test hooks (manual install). |

## Notable Observations
- Blueprint remains a single-line markdown file; normalization task is open in docs/TODO.md.
- SECURITY.md and risk register still outstanding for later phases.
- Future phases must replace the SQLite helper with Postgres/pgvector migrations (tracked in docs/TODO.md).
