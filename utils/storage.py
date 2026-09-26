"""
Simple JSON-file storage for user settings and generation history.
For production, replace with Redis or PostgreSQL.
"""

import json
import os
from pathlib import Path
from typing import Any

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def _user_file(user_id: int) -> Path:
    return DATA_DIR / f"{user_id}.json"


def _load(user_id: int) -> dict:
    f = _user_file(user_id)
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    return {"settings": {"provider": "kling", "resolution": "720p", "duration": 5},
            "history": []}


def _save(user_id: int, data: dict) -> None:
    _user_file(user_id).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ── Settings ──────────────────────────────────────────────────────────────────

def get_settings(user_id: int) -> dict:
    return _load(user_id)["settings"]


def set_setting(user_id: int, key: str, value: Any) -> None:
    data = _load(user_id)
    data["settings"][key] = value
    _save(user_id, data)


# ── History ───────────────────────────────────────────────────────────────────

def add_history(user_id: int, entry: dict) -> None:
    data = _load(user_id)
    data["history"].insert(0, entry)
    data["history"] = data["history"][:20]   # keep last 20
    _save(user_id, data)


def get_history(user_id: int) -> list:
    return _load(user_id)["history"]
