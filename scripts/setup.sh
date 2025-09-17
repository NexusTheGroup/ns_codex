#!/usr/bin/env bash
set -euo pipefail

echo "[setup] Ensuring core tooling..."
# Python
if command -v uv >/dev/null 2>&1; then
  echo "[setup] Using uv for Python env"
  uv venv .venv
  . .venv/bin/activate
  uv pip install --upgrade pip pytest psycopg2-binary pgvector
else
  echo "[setup] Using python -m venv"
  python3 -m venv .venv
  . .venv/bin/activate
  pip install --upgrade pip pytest psycopg2-binary pgvector
fi

# Node
if ! command -v pnpm >/dev/null 2>&1; then
  npm i -g pnpm
fi
pnpm init -y >/dev/null 2>&1 || true
pnpm add -D vitest @types/node

# Test folders
mkdir -p tests/python tests/js docs scripts .github/workflows

# Example env
cat > .env.example <<'ENV_EOF'
# Copy to .env and fill values as needed
APP_ENV=development
DB_URL=postgresql://user:pass@localhost:5432/app
REDIS_URL=redis://localhost:6379/0
ENV_EOF

echo "[setup] Done."
