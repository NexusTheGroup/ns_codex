# Changelog — Personal AI Chat Manager

## [Unreleased]

### Release Notes
- Kickstarted Phase 1 data foundations with ChatGPT/Claude ingestion pipeline, filesystem attachment storage, and ingestion CLI.

### Added
- `chat_manager` Python package providing SQLite persistence, format detection, and normalization logic.
- Pytest coverage for ingestion flows plus fixtures for ChatGPT and Claude exports.
- `scripts/import_conversations.py` CLI to run imports from the command line.

### Changed
- Expanded `docs/ENV.md`, `.env.example`, and README with ingestion-focused guidance.
- Updated `docs/CROSSREF.md`, `docs/TODO.md`, and `docs/TASKLOG.md` to reflect P1 progress.

### Fixed
- n/a (initial implementation for P1).

