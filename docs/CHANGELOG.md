# Changelog

## 2025-09-17 – Phase P1 Foundation
- Added planning artifacts (build plan, test matrix, API surface, DB schema) and documented environment/security requirements.
- Implemented SQLite-backed data layer, ingestion pipeline for ChatGPT & Claude, and Ollama manifest generation.
- Delivered minimal WSGI web UI + JSON API along with CLI commands for ingesting exports and running the server.
- Expanded automated test suite to cover schema, importers, web/API, CLI, and local AI tooling.
