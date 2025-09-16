# Repository Map

See also: Blueprint Cross-Reference (CROSSREF.md) · Open Tasks (TODO.md).

## High-Level Layout
- root/
  - .editorconfig
  - .pre-commit-config.yaml
  - .husky/ (pre-commit hook scripts)
  - AGENTS.md
  - blueprint.md
  - docs/ (ENV.md, REPO_MAP.md, CROSSREF.md, TODO.md, VALIDATION.md, TASKLOG.md, BRANCH_PROTECTION.md, ONBOARDING.md, BUILD_PLAN.md, TEST_MATRIX.md, API_SURFACE.md, DB_SCHEMA.sql, CHANGELOG.md, SECURITY.md)
  - package.json
  - pnpm-lock.yaml
  - pyproject.toml
  - scripts/ (setup.sh, smoke_test.sh)
  - src/ns_codex/ (cli.py, db.py, ingest.py, local_ai.py, web.py, types.py, __main__.py)
  - tests/ (fixtures/, python/, js/)
  - .github/ (CODEOWNERS, workflows/ci.yml, workflows/route-compliance.yml, PULL_REQUEST_TEMPLATE.md)
  - .env.example

> node_modules/, .venv/, and VCS metadata omitted for brevity.

## Inventory
| Area | Entry | Build Tool | Configs | Tests? | Notes |
| --- | --- | --- | --- | --- | --- |
| Governance | AGENTS.md; prompts.md; personas.md | n/a | n/a | n/a | Process, personas, and runbook; must stay authoritative. |
| Product Scope | blueprint.md | n/a | n/a | Referenced by sanity tests | Single-line Markdown; contains full system blueprint defining features. |
| Docs & Logs | docs/ | n/a | BUILD_PLAN.md; TEST_MATRIX.md; API_SURFACE.md; DB_SCHEMA.sql; ENV.md; REPO_MAP.md; CROSSREF.md; TODO.md; VALIDATION.md; TASKLOG.md; BRANCH_PROTECTION.md; ONBOARDING.md; CHANGELOG.md; SECURITY.md | n/a | Planning, schema, env, and security documentation. |
| Backend (Python) | src/ns_codex/ | stdlib + sqlite | n/a | tests/python/* | Implements data layer, ingestion pipeline, CLI, web UI, and Ollama tooling. |
| Python Tooling | pyproject.toml | pytest | pyproject.toml | tests/python/* | Pytest configured for expanded suite. |
| Frontend/API | src/ns_codex/web.py | WSGI (stdlib) | docs/API_SURFACE.md | tests/python/test_web.py | Minimal HTML/JSON endpoints served via WSGI. |
| Node Tooling | package.json; pnpm-lock.yaml | pnpm + vitest | package.json; pnpm-lock.yaml | tests/js/sanity.test.ts | Vitest sanity check ensures docs/blueprint exist. |
| Automation | scripts/setup.sh; scripts/smoke_test.sh | bash | scripts | Indirect via smoke tests | Setup bootstrap + smoke script running pytest/pnpm. |
| CI/CD | .github/workflows/*.yml | GitHub Actions | ci.yml; route-compliance.yml | Runs pytest & pnpm tests; compliance enforces doc sync | Route compliance blocks code changes without plan/TODO updates. |
| Tests | tests/python/, tests/js/ | pytest, vitest | n/a | yes | Python suite covers schema/import/web/CLI; JS keeps legacy sanity checks. |
| Local Guardrails | .pre-commit-config.yaml; .husky/pre-commit; .editorconfig | pre-commit, husky | same | Hooks pending developer install | Developers must run `pre-commit install` and `pnpm prepare` locally. |
| Ownership | .github/CODEOWNERS; PULL_REQUEST_TEMPLATE.md | GitHub | CODEOWNERS; PR template | n/a | CODEOWNERS + template enforce persona review & attestations. |

## Notable Observations
- Planning deliverables now exist and are linked from `docs/BUILD_PLAN.md`.
- SQLite backend provides a stand-in for the Postgres/pgvector design; migration path tracked in TODO.
- Web UI is intentionally read-only for P1; tagging/editing flows remain future work.
- Keep blueprint.md normalization on the radar—plan docs mitigate the single-line format for now.
