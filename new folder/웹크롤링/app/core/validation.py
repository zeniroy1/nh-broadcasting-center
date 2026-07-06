from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.paths import project_root


@dataclass(frozen=True)
class LayoutCheck:
    key: str
    path: Path
    exists: bool


def check_required_layout(settings: dict[str, Any]) -> list[LayoutCheck]:
    root = project_root()
    required = settings.get("required_layout", {})
    checks: list[LayoutCheck] = []
    for key, relative_path in required.items():
        path = root / relative_path
        checks.append(LayoutCheck(key=key, path=path, exists=path.exists()))
    return checks


def missing_required_files(settings: dict[str, Any]) -> list[LayoutCheck]:
    return [check for check in check_required_layout(settings) if not check.exists]
