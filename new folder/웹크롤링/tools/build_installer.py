from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILD_ROOT = PROJECT_ROOT / "_installer_build"
PAYLOAD = BUILD_ROOT / "payload.zip"
DIST_DIR = PROJECT_ROOT / "_배포"
RUNTIME = PROJECT_ROOT / "tools" / "installer_runtime.py"
PYTHON_EMBED_ZIP = PROJECT_ROOT / "tools" / "runtime_cache" / "python-3.10.11-embed-amd64.zip"
GET_PIP = PROJECT_ROOT / "tools" / "runtime_cache" / "get-pip.py"

EXCLUDE_DIR_NAMES = {
    ".venv",
    "__pycache__",
    "inputs",
    "easyocr",
    ".git",
    ".agents",
    ".codex",
    "build",
    "dist",
    "outputs",
    "생성보고서",
    "전세모집공고",
}

EXCLUDE_FILE_NAMES = {
    "setup_state.json",
    "_detected_regions.json",
    "화면캡처기.exe",
    "screen_scraper_gui.py",
    "화면캡처기.spec",
}

EXCLUDE_SUFFIXES = {".pyc", ".pyo"}

INCLUDE_TOP_LEVEL_FILES = [
    "통합프로그램실행.bat",
    "다른PC_첫실행안내.txt",
    "통합프로그램_기획서.txt",
]

INCLUDE_DIRS = ["app", "lh", "hug"]

EMPTY_DIRS = [
    "lh/outputs",
    "hug/outputs",
    "app/cache/hug",
]


def should_exclude(path: Path) -> bool:
    relative = path.relative_to(PROJECT_ROOT)
    parts = set(relative.parts)
    if parts & EXCLUDE_DIR_NAMES:
        return True
    if path.name in EXCLUDE_FILE_NAMES:
        return True
    if path.suffix.lower() in EXCLUDE_SUFFIXES:
        return True
    if path.name.startswith("웹크롤링_원클릭_이동용_") and path.suffix.lower() == ".zip":
        return True
    return False


def add_file(archive: zipfile.ZipFile, path: Path) -> None:
    if should_exclude(path):
        return
    archive.write(path, path.relative_to(PROJECT_ROOT).as_posix())


def build_payload() -> None:
    if BUILD_ROOT.exists():
        shutil.rmtree(BUILD_ROOT)
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)

    if not PYTHON_EMBED_ZIP.exists():
        raise SystemExit(f"portable Python zip not found: {PYTHON_EMBED_ZIP}")
    if not GET_PIP.exists():
        raise SystemExit(f"get-pip.py not found: {GET_PIP}")

    with zipfile.ZipFile(PAYLOAD, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for folder in EMPTY_DIRS:
            archive.writestr(folder.rstrip("/") + "/", "")

        with zipfile.ZipFile(PYTHON_EMBED_ZIP, "r") as py_zip:
            for member in py_zip.infolist():
                if member.is_dir():
                    continue
                data = py_zip.read(member.filename)
                name = member.filename
                if name.endswith("._pth"):
                    pth_text = data.decode("utf-8").replace("#import site", "import site")
                    if "../../.." not in pth_text.splitlines():
                        pth_text = pth_text.replace("import site", "../../..\nimport site")
                    data = pth_text.encode("utf-8")
                archive.writestr("runtime/python/" + name, data)
        archive.write(GET_PIP, "runtime/get-pip.py")

        for name in INCLUDE_TOP_LEVEL_FILES:
            path = PROJECT_ROOT / name
            if path.exists():
                add_file(archive, path)

        for dirname in INCLUDE_DIRS:
            root = PROJECT_ROOT / dirname
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if path.is_file():
                    add_file(archive, path)

    print(f"payload: {PAYLOAD} ({PAYLOAD.stat().st_size:,} bytes)")


def build_exe() -> None:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        "--name",
        "LH_HUG_통합프로그램_설치",
        "--add-data",
        f"{PAYLOAD};.",
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_ROOT / "pyinstaller_work"),
        "--specpath",
        str(BUILD_ROOT),
        str(RUNTIME),
    ]
    print("running:", " ".join(command))
    subprocess.check_call(command, cwd=str(PROJECT_ROOT))


def main() -> int:
    build_payload()
    build_exe()
    exe = DIST_DIR / "LH_HUG_통합프로그램_설치.exe"
    if not exe.exists():
        raise SystemExit("installer exe was not created")
    print(f"installer: {exe} ({exe.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
