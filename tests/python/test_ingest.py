from pathlib import Path

from ns_codex.ingest import ingest_file, parse_chatgpt_export, parse_claude_export

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_chatgpt_ingest_parses_messages(db):
    path = FIXTURES / "chatgpt_conversations.json"
    bundles = parse_chatgpt_export(path)
    assert len(bundles) == 1
    bundle = bundles[0]
    assert bundle.title == "Planning session"
    assert bundle.messages[0].role == "user"
    assert bundle.messages[1].attachments[0].filename == "notes.md"
    result = ingest_file(db, "chatgpt", path)
    assert result["inserted"] == 1


def test_claude_ingest_parses_messages(db):
    path = FIXTURES / "claude_conversations.jsonl"
    bundles = parse_claude_export(path)
    assert len(bundles) == 2
    assert bundles[0].messages[0].content.startswith("Claude")
    result = ingest_file(db, "claude", path)
    assert result["inserted"] == 2


def test_duplicate_checksum_skips_import(db, tmp_path):
    path = FIXTURES / "chatgpt_conversations.json"
    first = ingest_file(db, "chatgpt", path)
    second = ingest_file(db, "chatgpt", path)
    assert first["inserted"] == 1
    assert second["skipped"] is True
