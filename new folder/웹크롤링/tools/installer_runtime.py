from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

APP_NAME = "LH_HUG_통합프로그램"
DEFAULT_FOLDER = "LH_HUG_통합프로그램"


def base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parent


def payload_path() -> Path:
    return base_dir() / "payload.zip"


def default_install_dir() -> Path:
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        return Path(local_app) / DEFAULT_FOLDER
    return Path.home() / DEFAULT_FOLDER


def prompt_install_dir(default_dir: Path) -> Path:
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askdirectory(
            parent=root,
            title=f"{APP_NAME} 설치 위치 선택",
            initialdir=str(default_dir.parent if default_dir.parent.exists() else Path.home()),
            mustexist=False,
        )
        root.destroy()
        if selected:
            return Path(selected)
    except Exception:
        pass
    return default_dir


def show_error(message: str) -> None:
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, message, f"{APP_NAME} 설치 오류", 0x10)
    except Exception:
        pass


def vbs_launcher_text(install_dir: Path) -> str:
    pythonw = install_dir / "runtime" / "python" / "pythonw.exe"
    working = str(install_dir).replace('"', '""')
    executable = str(pythonw).replace('"', '""')
    return (
        'Set shell = CreateObject("WScript.Shell")\r\n'
        f'shell.CurrentDirectory = "{working}"\r\n'
        f'shell.Run """{executable}"" -m app.launcher", 0, False\r\n'
    )


def create_installed_launcher(install_dir: Path) -> Path:
    launcher = install_dir / "통합프로그램실행.vbs"
    launcher.write_text(vbs_launcher_text(install_dir), encoding="utf-16")
    return launcher


def desktop_folder() -> Path:
    try:
        import ctypes

        buffer = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.shell32.SHGetFolderPathW(None, 0x10, None, 0, buffer) == 0 and buffer.value:
            return Path(buffer.value)
    except Exception:
        pass
    return Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"


def powershell_quote(value: object) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def safe_extract(zip_path: Path, target_dir: Path) -> None:
    target_root = target_dir.resolve()
    with zipfile.ZipFile(zip_path, "r") as archive:
        for member in archive.infolist():
            destination = (target_root / member.filename).resolve()
            if target_root != destination and target_root not in destination.parents:
                raise RuntimeError(f"Unsafe archive path: {member.filename}")
            if member.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member, "r") as source, destination.open("wb") as output:
                shutil.copyfileobj(source, output)


def create_desktop_launcher(install_dir: Path) -> None:
    desktop = desktop_folder()
    if not desktop.exists():
        return
    shortcut_path = desktop / "LH_HUG_통합프로그램.lnk"
    launcher = install_dir / "통합프로그램실행.vbs"
    wscript = Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32" / "wscript.exe"
    icon = Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32" / "shell32.dll"
    script = "; ".join(
        [
            "$shell = New-Object -ComObject WScript.Shell",
            f"$shortcut = $shell.CreateShortcut({powershell_quote(shortcut_path)})",
            f"$shortcut.TargetPath = {powershell_quote(wscript)}",
            f"$shortcut.Arguments = {powershell_quote(chr(34) + str(launcher) + chr(34))}",
            f"$shortcut.WorkingDirectory = {powershell_quote(install_dir)}",
            f"$shortcut.IconLocation = {powershell_quote(str(icon) + ',220')}",
            "$shortcut.Description = 'LH/HUG/SH/GH 통합 청약 프로그램'",
            "$shortcut.Save()",
        ]
    )
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", script],
        cwd=str(install_dir),
        capture_output=True,
        text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if completed.returncode != 0 or not shortcut_path.exists():
        raise RuntimeError("바탕화면 바로가기를 만들지 못했습니다.")
    for obsolete_name in ("LH_HUG_통합프로그램_실행.bat", "LH_HUG_통합프로그램_실행.vbs"):
        (desktop / obsolete_name).unlink(missing_ok=True)


def run_program(install_dir: Path) -> int:
    launcher = install_dir / "통합프로그램실행.vbs"
    if not launcher.exists():
        show_error(f"실행 파일을 찾지 못했습니다:\n{launcher}")
        return 1
    subprocess.Popen(
        ["wscript.exe", str(launcher)],
        cwd=str(install_dir),
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LH/HUG 통합 프로그램 설치기")
    parser.add_argument("--dir", help="설치 폴더를 직접 지정합니다.")
    parser.add_argument("--no-run", action="store_true", help="설치 후 프로그램을 바로 실행하지 않습니다.")
    parser.add_argument("--no-shortcut", action="store_true", help="바탕화면 바로가기를 만들지 않습니다.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    zip_path = payload_path()
    if not zip_path.exists():
        print(f"payload.zip을 찾지 못했습니다: {zip_path}")
        return 1

    install_dir = Path(args.dir).expanduser() if args.dir else prompt_install_dir(default_install_dir())
    install_dir = install_dir.resolve()

    print(f"[{APP_NAME}] 설치 폴더: {install_dir}")
    install_dir.mkdir(parents=True, exist_ok=True)
    safe_extract(zip_path, install_dir)
    print("파일 압축 해제 완료")
    create_installed_launcher(install_dir)

    if not args.no_shortcut:
        create_desktop_launcher(install_dir)
        print("바탕화면 실행 파일 생성 완료")

    guide = install_dir / "다른PC_첫실행안내.txt"
    if guide.exists():
        print(f"안내 파일: {guide}")

    if args.no_run:
        print("설치 완료. 통합프로그램실행.vbs를 실행하면 포함 Python으로 환경 셋업 후 프로그램이 열립니다.")
        return 0

    print("포함 Python 환경 셋업 및 프로그램 실행을 시작합니다.")
    print("Python은 설치 파일에 포함되어 있습니다. 첫 실행은 필수 패키지 설치 때문에 시간이 걸릴 수 있고 인터넷이 필요합니다.")
    return run_program(install_dir)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        show_error(str(error))
        raise
