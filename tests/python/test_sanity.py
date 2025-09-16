from pathlib import Path

def test_blueprint_exists_and_not_empty():
    p = Path("blueprint.md")
    assert p.exists(), "blueprint.md is missing"
    assert p.stat().st_size > 50, "blueprint.md looks empty"

def test_repo_has_docs_folder():
    assert Path("docs").exists(), "docs/ folder should exist"
