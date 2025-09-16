# TODO

Live task list maintained per AGENTS.md.

## Immediate
- [x] Configure branch protection on main/release branches (require CI, Route Compliance, Smoke, CODEOWNERS review, up-to-date merges). (documented in docs/BRANCH_PROTECTION.md)
- [x] Document local setup steps for new guardrails (run pre-commit install, pnpm prepare). (see docs/ONBOARDING.md)
- [x] Produce P0 planning deliverables (docs/BUILD_PLAN.md, TEST_MATRIX.md, API_SURFACE.md, DB_SCHEMA.sql).
- [ ] Normalize blueprint.md into readable multi-line format before editing. *(Still outstanding; plan docs mitigate review pain for now.)*
- [x] Flesh out docs/ENV.md with real variable definitions and align .env.example when ready.
- [x] Draft docs/CHANGELOG.md with Release Notes section framework.
- [x] Establish SECURITY.md and initial risk register before implementation.
- [ ] Harden SQLite implementation for concurrency and migrations (swap to Postgres/pgvector).
- [ ] Expand UI beyond read-only HTML to support tagging/notes once correlation layer exists.

## Discovery Follow-Ups
- [ ] Expand test suite beyond sanity checks once features exist. *(Partially addressed in P1; continue adding coverage as features grow.)*
- [ ] Define scripts/setup.sh parity for uv and pnpm lock usage (ensure deterministic installs).
- [ ] Outline CI enhancements (linting, smoke, future eval runners).
- [ ] Evaluate adding PR body validation step to enforce template attestations (optional guardrail).
