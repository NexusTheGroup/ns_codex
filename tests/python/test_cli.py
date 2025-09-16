from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"

from ns_codex.cli import main
from ns_codex.db import Database


def test_cli_ingest_command(tmp_path):
    db_path = tmp_path / "cli.sqlite3"
    export = FIXTURES / "chatgpt_conversations.json"
    exit_code = main(["ingest", "--platform", "chatgpt", "--db", str(db_path), str(export)])
    assert exit_code == 0
    db = Database(str(db_path))
    try:
        threads = db.search_threads(None, limit=5)
        assert len(threads) == 1
    finally:
        db.close()


def test_cli_ollama_config(tmp_path):
    target = tmp_path / "ollama"
    exit_code = main(["ollama-config", "--dir", str(target)])
    assert exit_code == 0
    assert (target / "ollama-manifest.json").exists()
    assert (target / "pull-models.sh").exists()
    exit_code_dup = main(["ollama-config", "--dir", str(target)])
    assert exit_code_dup == 3
