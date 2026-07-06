from __future__ import annotations

from app.core.config import load_settings
from app.core.paths import app_root, project_root
from app.core.validation import check_required_layout, missing_required_files


def main() -> int:
    settings = load_settings()
    enabled = ", ".join(settings.get("enabled_sources", []))
    print(f"Project root: {project_root()}")
    print(f"App root: {app_root()}")
    print(f"Enabled sources: {enabled}")
    print("Required files:")
    for check in check_required_layout(settings):
        status = "OK" if check.exists else "MISSING"
        print(f"- {check.key}: {status} ({check.path})")
    missing = missing_required_files(settings)
    if missing:
        print("Missing required files. Fix the standard layout before running collectors.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
