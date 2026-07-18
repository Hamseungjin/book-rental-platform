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


def normalize_profile(value: str | None) -> str:
    """Normalize an application profile value for safe comparisons."""
    return (value or "").strip().casefold()


def get_app_profile() -> str:
    """Return the normalized APP_PROFILE value, or an empty string when unset."""
    return normalize_profile(os.environ.get("APP_PROFILE"))
