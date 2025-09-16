# Test Matrix

| Area | Scenario | Test Coverage | Notes |
| --- | --- | --- | --- |
| Schema | Database bootstrap executes and tables exist | `tests/python/test_database.py::test_schema_installs` | Validates DDL script and FK wiring |
| Data Layer | Persist normalized thread with messages & attachments | `tests/python/test_database.py::test_store_and_fetch_thread` | Ensures token aggregation, ordering, attachments |
| Data Layer | Search threads by keyword | `tests/python/test_database.py::test_search_threads` | Exercises SQL search helper |
| Import | Parse ChatGPT conversations export | `tests/python/test_ingest.py::test_chatgpt_ingest` | Covers tree flattening + timezone normalization |
| Import | Parse Claude JSONL export | `tests/python/test_ingest.py::test_claude_ingest` | Covers metadata extraction |
| CLI | `ingest` command writes to db file | `tests/python/test_cli.py::test_cli_ingest_command` | Runs CLI entrypoint with temp files |
| Local AI | Ollama manifest + script creation | `tests/python/test_local_ai.py::test_manifest_and_script` | Ensures required models enumerated |
| Web UI | HTML root renders conversations | `tests/python/test_web.py::test_root_page_lists_threads` | Simulated WSGI request |
| Web API | JSON thread detail | `tests/python/test_web.py::test_api_thread_detail` | Validates API contract |
| Web API | Search endpoint honors query | `tests/python/test_web.py::test_api_search_threads` | Ensures search integration |
| Regression | Legacy sanity checks | `tests/python/test_sanity.py`, `tests/js/sanity.test.ts` | Protects blueprint/docs presence |

