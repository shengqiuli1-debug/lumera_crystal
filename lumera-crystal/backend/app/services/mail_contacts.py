from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings


def _resolve_contacts_path() -> Path:
    path = Path(settings.mail_contacts_path)
    if path.is_absolute():
        return path
    # backend/ directory
    base_dir = Path(__file__).resolve().parents[2]
    return base_dir / path


def load_contacts() -> dict[str, str]:
    path = _resolve_contacts_path()
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Mail contacts file must be a JSON object")
    contacts: dict[str, str] = {}
    for key, value in data.items():
        if isinstance(key, str) and isinstance(value, str):
            contacts[key.strip()] = value.strip()
    return contacts
