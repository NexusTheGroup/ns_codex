# Security Overview (P1)

## Trust Boundary
- Single-user desktop deployment; all services run locally.
- HTTP server binds to loopback by default and serves read-only views.

## Data Handling
- Imports are stored on disk in SQLite under the configured `NS_CODEX_DB_PATH`.
- Attachments are currently inlined; future phases will move them to hashed object storage.
- Checksums (SHA-256) prevent duplicate ingestion of identical exports.

## Authentication & Authorization
- No multi-user support in P1. The CLI and web UI assume trusted local user.
- Future phases must introduce user authentication when remote access becomes possible.

## Dependencies & Supply Chain
- Python implementation uses the standard library only; no third-party runtime deps added in P1.
- Node toolchain remains unchanged (dev dependencies only for Vitest).

## Secrets Management
- No secrets stored. If API keys are introduced (e.g., for remote LLMs), they must reside in `.env` and never in source control.

## Known Gaps / Follow-Ups
- Transport security (HTTPS) not required for localhost but must be addressed before any remote deployment.
- SQLite lacks row-level encryption; evaluate filesystem encryption or migrate to Postgres with pgcrypto in later phases.
- No audit logging beyond schema definition; implement triggers in P2+ to populate `audits` table.
