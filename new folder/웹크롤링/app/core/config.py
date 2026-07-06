from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.paths import app_root


def settings_path() -> Path:
    return app_root() / "config" / "settings.json"


def load_settings() -> dict[str, Any]:
    with settings_path().open("r", encoding="utf-8") as file:
        return json.load(file)
