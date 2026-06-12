from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"


def get_data_dir() -> Path:
    """Return the single data directory used by the app, CLI, and default store."""
    configured = os.environ.get("BOOKBRIDGE_DATA_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return DEFAULT_DATA_DIR.resolve()
