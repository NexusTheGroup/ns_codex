import json
from pathlib import Path

import pytest

from ns_codex.local_ai import DEFAULT_MODELS, OllamaConfigManager


def test_manifest_and_script(tmp_path):
    manager = OllamaConfigManager(tmp_path, overwrite=True)
    paths = manager.ensure()
    manifest = json.loads(Path(paths["manifest"]).read_text())
    assert len(manifest["models"]) == len(DEFAULT_MODELS)
    script = Path(paths["script"]).read_text().strip().splitlines()
    assert script[0].startswith("#!/")
    assert any("ollama pull" in line for line in script)


def test_prevent_overwrite(tmp_path):
    manager = OllamaConfigManager(tmp_path, overwrite=False)
    manager.ensure()
    with pytest.raises(FileExistsError):
        manager.ensure()
