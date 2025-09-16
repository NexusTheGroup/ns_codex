# AGENTS.md
## Mission
Implement the project described in `./blueprint.md` end-to-end inside **VS Code with Codex (GPT-5-Codex)**. Produce working code, tests, docs, and CI. Do **not** conclude until all acceptance checks are green.

## Model & Reasoning Modes
- **Model:** GPT-5-Codex (preferred for agentic coding in Codex surfaces).
- **Reasoning:** 
  - **High** -> planning, schema/API design, large refactors, data migrations, perf & security passes. 
  - **Medium** -> steady feature work, unit/integration tests, UI wiring. 
  - **Minimal/Low** -> bulk mechanical transforms only.
- Switch modes per task complexity; default to **Medium** during implementation.

## Guardrails & Permissions
- **Edit scope:** workspace files only. Ask before touching anything outside the repo.
- **Execution:** you may run local commands needed for builds/tests.
- **Network:** OFF by default. Only request **allow-listed** access when a specific task requires it (e.g., fetching a package index); provide the domain list and rationale.
- **Secrets:** never introduce plaintext secrets. If needed, reference `.env.example` and `docs/ENV.md`.

## Source of Truth
- `./blueprint.md` governs scope.
- This file (`AGENTS.md`) governs process, safety, and "no-stop" criteria.

## Branch & PR Protocol
- Create short-lived feature branches: `feat/<phase>-<task>` or `fix/<scope>`.
- Each PR must include:
  - Tests (unit/integration/e2e as applicable)
  - Updated docs (`docs/CHANGELOG.md`, `docs/ENV.md` if env vars changed)
  - A **Finding Card** (what/why/risk/acceptance)
- Request **@codex** review on every PR; resolve suggestions before merge.

## Phases & Outputs
- **P0 - Plan (High):** Generate `docs/BUILD_PLAN.md`, `docs/TEST_MATRIX.md`, `docs/API_SURFACE.md`, `docs/DB_SCHEMA.sql`.
- **P1..P3 - Build (Medium->High as needed):** Implement per plan with tests and smoke coverage.
- **P4 - Polish & Ops:** performance budgets, security posture, docs & DX.
- **P5 - Scale & Hardening:** tuning, caching, observability, backup/restore.

## No-Stop Acceptance (Global)
Do **not** conclude the project until **all** of the following are true:
1) All phase deliverables exist and are linked from `docs/BUILD_PLAN.md`.  
2) `scripts/smoke_test.sh` returns **0** locally.  
3) CI is green on the default branch (unit/integration/e2e that apply).  
4) `docs/ENV.md` lists all runtime env vars; `.env.example` is updated.  
5) A final **Release Notes** section is appended to `docs/CHANGELOG.md`.

If any acceptance fails: continue iterating, or open a TODO in `docs/TODO.md` and resolve it before concluding.

## Quality Gates
- **Testing:** add tests with each change; keep a fast "sanity" test set.
- **Performance:** add simple budgets where sensible; fail CI if regressed.
- **Security:** avoid dangerous sinks; prefer parameterized queries; verify dependency/license updates; no secrets in code.
- **Determinism:** lock deps; write deterministic build steps; document tool versions.

## Commands (expected defaults - adjust in setup)
- Python: `uv run pytest -q` or `pytest -q`
- Node: `pnpm test` (Vitest)
- Smoke: `bash scripts/smoke_test.sh`

## Don't Touch
- Any file marked with `# DO-NOT-EDIT` banner.
- Binary assets unless explicitly requested.

## Telemetry
- Write brief task notes to `docs/TASKLOG.md` (timestamp, task, result), append-only.
