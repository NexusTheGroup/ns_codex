# Local Setup & Guardrails

Follow these steps after cloning to enable mandatory hooks and tooling.

## Prerequisites
- Python 3.10+
- Node 20+ with pnpm
- pre-commit (install via `pip install pre-commit` or `brew install pre-commit`)

## Initial Setup
1. `pnpm install`
2. `pnpm prepare` (runs husky install)
3. `pre-commit install`
4. `python3 -m venv .venv && source .venv/bin/activate` (optional but recommended)
5. `pre-commit run --all-files` (ensures baseline compliance)

## Before Each Commit
- Husky runs `pnpm test -- --passWithNoTests`
- pre-commit executes repo hooks when installed locally
- Update `docs/TODO.md` for any new tasks; Route Compliance will check

## Troubleshooting
- If Husky skips hooks, rerun `pnpm prepare`.
- To disable hooks temporarily (not recommended), run `HUSKY=0 git commit ...`.
- Ensure pre-commit is installed inside your Python environment if using virtualenv/uv.

## CI Expectations
- `bash scripts/smoke_test.sh` must pass locally before pushing.
- CI + Route Compliance + Smoke are required checks for protected branches.
