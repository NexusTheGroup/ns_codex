import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ns_codex.db import Database  # noqa: E402


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "test.sqlite3"
    database = Database(str(path))
    yield database
    database.close()
