"""Shared path resolution for source runs and frozen (PyInstaller) executables.

The project is normally run as ``python scripts/musinsa_buyer_server.py`` from
``submission/src``, where every config/asset path can be derived from
``Path(__file__).resolve().parent``.

When the same entry point is packaged into a standalone .exe with PyInstaller
(``--onefile``), that assumption breaks in two ways:

- Read-only bundled assets (default config JSON, the buyer app HTML) are
  extracted at runtime into a temporary folder (``sys._MEIPASS``), not next to
  the executable.
- Anything the app needs to *write* at runtime (the keyword learning queue)
  must not go into that temporary folder, because it is wiped after every
  run. It has to live next to the .exe instead, so it persists across
  launches.

This module centralizes that split so every script can keep using a single
``resource_path(...)`` / ``writable_path(...)`` call instead of re-deriving
``sys.frozen`` handling in each file.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
SRC_ROOT = CURRENT_DIR.parent


def is_frozen() -> bool:
    """True when running inside a PyInstaller-built executable."""
    return bool(getattr(sys, "frozen", False))


def bundle_root() -> Path:
    """Root directory for read-only assets shipped with the app."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", CURRENT_DIR))
    return SRC_ROOT


def app_data_root() -> Path:
    """Root directory for files the running app may need to write."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return SRC_ROOT


def resource_path(*parts: str) -> Path:
    """Path to a read-only bundled resource (app HTML, default config JSON)."""
    return bundle_root().joinpath(*parts)


def writable_path(*parts: str) -> Path:
    """Path to a file the app can read and write at runtime.

    On first use under a frozen exe, seeds the writable copy from the bundled
    default (if one exists) so the shipped starter file is not lost the
    moment the temporary bundle folder is cleaned up.
    """
    target = app_data_root().joinpath(*parts)
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        seed = resource_path(*parts)
        if seed.exists() and seed.resolve() != target.resolve():
            shutil.copyfile(seed, target)
    return target
