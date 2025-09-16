#!/usr/bin/env bash
set -euo pipefail
RED='\033[0;31m'; GRN='\033[0;32m'; NC='\033[0m'

echo "[smoke] Checking blueprint.md exists..."
test -s ./blueprint.md || { echo -e "${RED}Missing blueprint.md${NC}"; exit 1; }

echo "[smoke] Python sanity..."
if [ -d ".venv" ]; then . .venv/bin/activate; fi
if python -c "import sys" >/dev/null 2>&1; then
  pytest -q tests/python || { echo -e "${RED}Py tests failed${NC}"; exit 1; }
else
  echo "[smoke] Python not available, skipping"
fi

echo "[smoke] Node sanity..."
if command -v pnpm >/dev/null 2>&1; then
  pnpm test || { echo -e "${RED}JS tests failed${NC}"; exit 1; }
else
  echo "[smoke] pnpm not available, skipping"
fi

echo -e "${GRN}[smoke] OK${NC}"
