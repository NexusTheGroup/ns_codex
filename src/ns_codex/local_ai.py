from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

DEFAULT_MODELS = [
    {
        "name": "bge-m3",
        "tag": "bge-m3",
        "size_gb": 1.8,
        "purpose": "Multilingual embedding model",
    },
    {
        "name": "bge-reranker-v2-m3",
        "tag": "bge-reranker-v2-m3",
        "size_gb": 1.1,
        "purpose": "Cross-encoder reranker",
    },
    {
        "name": "llama3.1",
        "tag": "llama3.1:70b",
        "size_gb": 40.0,
        "purpose": "Primary chat/analysis model",
    },
    {
        "name": "codellama",
        "tag": "codellama:34b",
        "size_gb": 18.0,
        "purpose": "Code-focused assistant",
    },
]

DEFAULT_CONFIG_DIR = Path(os.getenv("NS_CODEX_OLLAMA_DIR", os.path.expanduser("~/.config/ns_codex/ollama")))


class OllamaConfigManager:
    def __init__(self, base_dir: Path | str | None = None, overwrite: bool = False) -> None:
        self.base_dir = Path(base_dir) if base_dir else DEFAULT_CONFIG_DIR
        self.overwrite = overwrite

    def ensure(self, models: Iterable[dict] | None = None) -> dict:
        manifest_path = self.write_manifest(models)
        script_path = self.write_pull_script(models)
        return {"manifest": manifest_path, "script": script_path}

    def write_manifest(self, models: Iterable[dict] | None = None) -> Path:
        models_list = list(models) if models is not None else list(DEFAULT_MODELS)
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "models": models_list,
        }
        path = self.base_dir / "ollama-manifest.json"
        self._write_text(path, json.dumps(payload, indent=2))
        return path

    def write_pull_script(self, models: Iterable[dict] | None = None) -> Path:
        models_list = list(models) if models is not None else list(DEFAULT_MODELS)
        path = self.base_dir / "pull-models.sh"
        lines = [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            "",  # blank line
        ]
        for model in models_list:
            tag = model.get("tag") or model.get("name")
            lines.append(f"ollama pull {tag}")
        lines.append("")
        self._write_text(path, "\n".join(lines))
        path.chmod(0o755)
        return path

    def _write_text(self, path: Path, data: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not self.overwrite:
            raise FileExistsError(f"Refusing to overwrite existing file: {path}")
        path.write_text(data, encoding="utf-8")


__all__ = ["OllamaConfigManager", "DEFAULT_MODELS", "DEFAULT_CONFIG_DIR"]
