from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PYTHON = PROJECT_ROOT / "runtime" / "python" / "python.exe"
PYTHON_EXE = RUNTIME_PYTHON if RUNTIME_PYTHON.exists() else Path(sys.executable)
GET_PIP = PROJECT_ROOT / "runtime" / "get-pip.py"
REQUIREMENTS = PROJECT_ROOT / "app" / "requirements.txt"
STATE_FILE = PROJECT_ROOT / "app" / "config" / "setup_state.json"

REQUIRED_IMPORTS = {
    "pandas": "pandas",
    "lxml": "lxml",
    "html5lib": "html5lib",
    "beautifulsoup4": "bs4",
}

REQUIRED_DIRS = [
    "lh/outputs",
    "hug/outputs",
    "sh/outputs",
    "gh/outputs",
    "app/cache/hug",
]


def progress(percent: int, message: str) -> None:
    print(f"[progress] {percent} {message}", flush=True)


def hidden_flags() -> int:
    return getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0


def run(command: list[str], message: str) -> None:
    print(message)
    completed = subprocess.run(command, cwd=str(PROJECT_ROOT), creationflags=hidden_flags())
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def ensure_dirs() -> None:
    for relative in REQUIRED_DIRS:
        (PROJECT_ROOT / relative).mkdir(parents=True, exist_ok=True)


def configure_embedded_python() -> None:
    runtime_dir = PYTHON_EXE.parent
    for pth in runtime_dir.glob("python*._pth"):
        text = pth.read_text(encoding="utf-8")
        changed = text.replace("#import site", "import site")
        if "../../.." not in changed.splitlines():
            changed = changed.replace("import site", "../../..\nimport site")
        if changed != text:
            pth.write_text(changed, encoding="utf-8")


def ensure_pip() -> None:
    completed = subprocess.run(
        [str(PYTHON_EXE), "-m", "pip", "--version"],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=hidden_flags(),
    )
    if completed.returncode == 0:
        return
    if not GET_PIP.exists():
        raise SystemExit(f"get-pip.py not found: {GET_PIP}")
    run([str(PYTHON_EXE), str(GET_PIP)], "[setup] Installing pip into included Python...")


def missing_packages() -> list[str]:
    script = "\n".join(
        [
            "import importlib.util, json",
            f"mods = {json.dumps(REQUIRED_IMPORTS, ensure_ascii=False)}",
            "missing = [pkg for pkg, mod in mods.items() if importlib.util.find_spec(mod) is None]",
            "print(json.dumps(missing, ensure_ascii=False))",
        ]
    )
    completed = subprocess.run(
        [str(PYTHON_EXE), "-c", script],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=hidden_flags(),
    )
    if completed.returncode != 0:
        return list(REQUIRED_IMPORTS)
    try:
        return json.loads(completed.stdout.strip() or "[]")
    except json.JSONDecodeError:
        return list(REQUIRED_IMPORTS)


def install_requirements() -> None:
    missing = missing_packages()
    if not missing:
        print("[setup] Required packages already installed.")
        progress(90, "필수 패키지가 이미 준비되어 있습니다.")
        return
    print("[setup] Missing packages: " + ", ".join(missing))
    progress(40, "필요한 패키지 목록을 확인했습니다.")
    progress(45, "pip를 최신 상태로 준비하고 있습니다.")
    run([str(PYTHON_EXE), "-m", "pip", "install", "--upgrade", "pip"], "[setup] Updating pip...")
    progress(55, "필수 패키지를 내려받아 설치하고 있습니다.")
    run([str(PYTHON_EXE), "-m", "pip", "install", "-r", str(REQUIREMENTS)], "[setup] Installing required packages...")
    progress(90, "필수 패키지 설치가 완료되었습니다.")


def write_state() -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "python": str(PYTHON_EXE),
        "requirements": str(REQUIREMENTS),
        "required_dirs": REQUIRED_DIRS,
        "collection_mode": {"lh": "direct", "hug": "direct"},
        "python_included": RUNTIME_PYTHON.exists(),
    }
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    os.chdir(PROJECT_ROOT)
    progress(5, "설치 폴더 구조를 확인하고 있습니다.")
    ensure_dirs()
    progress(12, "결과 저장 폴더를 준비했습니다.")
    configure_embedded_python()
    progress(18, "포함된 Python 환경을 설정하고 있습니다.")
    ensure_pip()
    progress(35, "Python 패키지 상태를 확인하고 있습니다.")
    install_requirements()
    progress(94, "설정 상태를 저장하고 있습니다.")
    write_state()
    progress(96, "환경 준비가 완료되었습니다.")
    print("[setup] Ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
