# Repository Map

See also: Blueprint Cross-Reference (CROSSREF.md) · Open Tasks (TODO.md).

## High-Level Layout
- root/
  - .editorconfig
  - .pre-commit-config.yaml
  - .husky/ (pre-commit hook scripts)
  - AGENTS.md
  - blueprint.md
  - docs/ (ENV.md, REPO_MAP.md, CROSSREF.md, TODO.md, VALIDATION.md, TASKLOG.md, BRANCH_PROTECTION.md, ONBOARDING.md)
  - package.json
  - pnpm-lock.yaml
  - pyproject.toml
  - scripts/ (setup.sh, smoke_test.sh)
  - tests/ (js/sanity.test.ts, python/test_sanity.py)
  - .github/ (CODEOWNERS, workflows/ci.yml, workflows/route-compliance.yml, PULL_REQUEST_TEMPLATE.md)

> node_modules/, .venv/, and VCS metadata omitted for brevity.

## Inventory
| Area | Entry | Build Tool | Configs | Tests? | Notes |
| --- | --- | --- | --- | --- | --- |
| Governance | AGENTS.md; prompts.md; personas.md | n/a | n/a | n/a | Process, personas, and runbook; must stay authoritative. |
| Product Scope | blueprint.md | n/a | n/a | Referenced by sanity tests | Single-line Markdown; contains full system blueprint defining features. |
| Docs & Logs | docs/ | n/a | ENV.md; REPO_MAP.md; CROSSREF.md; TODO.md; VALIDATION.md; TASKLOG.md; BRANCH_PROTECTION.md; ONBOARDING.md | n/a | Discovery docs plus branch guardrails and onboarding guides. |
| Python Tooling | pyproject.toml | pytest | pyproject.toml | tests/python/test_sanity.py | Minimal pytest config pointing to sanity tests. |
| Node Tooling | package.json; pnpm-lock.yaml | pnpm + vitest | package.json; pnpm-lock.yaml | tests/js/sanity.test.ts | Vitest sanity check ensures docs/blueprint exist. |
| Automation | scripts/setup.sh; scripts/smoke_test.sh | bash | scripts | Indirect via smoke tests | Setup bootstrap + smoke script running pytest/pnpm. |
| CI/CD | .github/workflows/*.yml | GitHub Actions | ci.yml; route-compliance.yml | Runs pytest & pnpm tests; compliance enforces doc sync | Route compliance blocks code changes without plan/TODO updates. |
| Tests | tests/ | pytest, vitest | n/a | yes | Only smoke-level sanity coverage today. |
| Local Guardrails | .pre-commit-config.yaml; .husky/pre-commit; .editorconfig | pre-commit, husky | same | Hooks pending developer install | Developers must run `pre-commit install` and `pnpm prepare` locally. |
| Ownership | .github/CODEOWNERS; PULL_REQUEST_TEMPLATE.md | GitHub | CODEOWNERS; PR template | n/a | CODEOWNERS + template enforce persona review & attestations. |

## Notable Observations
- P0 planning artifacts (docs/BUILD_PLAN.md, etc.) are not present yet.
- blueprint.md lacks line breaks, so diffs and reviews are tricky—consider reformatting when editing.
- Branch protection must be configured in GitHub UI (see docs/BRANCH_PROTECTION.md).
- ENV documentation is placeholder text; real env var definitions pending later phases.

