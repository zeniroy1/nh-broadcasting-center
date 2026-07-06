from __future__ import annotations

from pathlib import Path


def app_root() -> Path:
    return Path(__file__).resolve().parents[1]


def project_root() -> Path:
    return app_root().parent
