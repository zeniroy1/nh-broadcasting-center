from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HOST = "127.0.0.1"
PORT = 8765
URL = f"http://{HOST}:{PORT}/"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_FOLDER = PROJECT_ROOT / "app" / "logs"
LOG_PATH = LOG_FOLDER / "launcher.log"
STATUS = {"state": "preparing", "message": "필수 환경을 확인하고 있습니다.", "progress": 2}


def runtime_python() -> Path:
    included = PROJECT_ROOT / "runtime" / "python" / "python.exe"
    return included if included.exists() else Path(sys.executable)


def runtime_pythonw() -> Path:
    included = PROJECT_ROOT / "runtime" / "python" / "pythonw.exe"
    if included.exists():
        return included
    sibling = Path(sys.executable).with_name("pythonw.exe")
    return sibling if sibling.exists() else Path(sys.executable)


def port_is_open() -> bool:
    try:
        with socket.create_connection((HOST, PORT), timeout=0.5):
            return True
    except OSError:
        return False


def hidden_flags() -> int:
    return getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0


def loading_page() -> bytes:
    return """<!doctype html>
<html lang=\"ko\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>LH/HUG/SH/GH 통합 프로그램</title>
<style>body{margin:0;background:#f3f6fa;color:#172033;font-family:Arial,'Malgun Gothic',sans-serif}.wrap{min-height:100vh;display:grid;place-items:center}.box{width:min(520px,calc(100% - 40px));background:#fff;border:1px solid #d9e1ec;border-radius:8px;padding:32px;box-shadow:0 18px 50px rgba(31,48,77,.10)}h1{font-size:22px;margin:0 0 12px}p{color:#556176;line-height:1.7;min-height:28px}.progress-head{display:flex;align-items:center;justify-content:space-between;margin-top:22px;color:#556176}.progress-head strong{font-size:20px;color:#168f6a}.track{height:10px;background:#e7edf5;overflow:hidden;border-radius:5px;margin-top:10px}.bar{height:100%;width:2%;background:#168f6a;transition:width .35s ease}small{display:block;color:#7a879b;margin-top:18px}</style>
</head><body><main class=\"wrap\"><section class=\"box\"><h1>통합 프로그램을 준비하고 있습니다</h1><p id=\"message\">필수 환경을 확인하고 있습니다.</p><div class=\"progress-head\"><span>설치 진행률</span><strong id=\"percent\">2%</strong></div><div class=\"track\"><div class=\"bar\"></div></div><small>처음 실행할 때는 필요한 패키지 설치로 시간이 걸릴 수 있습니다.</small></section></main>
<script>async function check(){try{const r=await fetch('/api/state',{cache:'no-store'});if(r.ok){location.reload();return}}catch(e){}try{const r=await fetch('/api/launcher-status',{cache:'no-store'});const d=await r.json();const p=Math.max(0,Math.min(100,Number(d.progress)||0));document.getElementById('message').textContent=d.message;document.getElementById('percent').textContent=Math.round(p)+'%';document.querySelector('.bar').style.width=p+'%';if(d.state==='error'){document.querySelector('.bar').style.background='#c23b3b';document.getElementById('percent').style.color='#c23b3b'}}catch(e){}setTimeout(check,700)}check()</script></body></html>""".encode("utf-8")


class LoadingHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path.startswith("/api/state"):
            payload = json.dumps({"ok": False, "state": STATUS["state"]}, ensure_ascii=False).encode("utf-8")
            self.send_response(503)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if self.path.startswith("/api/launcher-status"):
            payload = json.dumps(STATUS, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        payload = loading_page()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, _format: str, *_args: object) -> None:
        return


def run_bootstrap() -> int:
    LOG_FOLDER.mkdir(parents=True, exist_ok=True)
    STATUS.update(state="preparing", message="필수 패키지와 폴더 구조를 준비하고 있습니다.", progress=3)
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    with LOG_PATH.open("a", encoding="utf-8") as log:
        log.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] launcher start\n")
        log.flush()
        process = subprocess.Popen(
            [str(runtime_python()), "-m", "app.bootstrap"],
            cwd=str(PROJECT_ROOT),
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=hidden_flags(),
        )
        assert process.stdout is not None
        for line in process.stdout:
            log.write(line)
            log.flush()
            match = re.match(r"\[progress\]\s+(\d+)\s+(.+)", line.strip())
            if match:
                percent = max(int(STATUS.get("progress", 0)), int(match.group(1)))
                STATUS.update(progress=min(percent, 96), message=match.group(2))
                continue
            if re.search(r"Collecting|Downloading|Using cached|Installing collected|Successfully installed", line, re.I):
                current = int(STATUS.get("progress", 0))
                STATUS["progress"] = min(89, current + 1)
        return process.wait()


def start_app_server() -> bool:
    LOG_FOLDER.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["APP_SKIP_BROWSER"] = "1"
    server_log = LOG_FOLDER / "server.log"
    STATUS.update(state="preparing", message="웹 프로그램 서버를 시작하고 있습니다.", progress=97)
    for attempt in range(1, 4):
        with server_log.open("a", encoding="utf-8") as log:
            log.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] server start attempt {attempt}\n")
            process = subprocess.Popen(
                [str(runtime_pythonw()), "-m", "app.server"],
                cwd=str(PROJECT_ROOT),
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
                creationflags=hidden_flags(),
            )
        for _ in range(50):
            if port_is_open():
                STATUS.update(state="ready", message="프로그램 준비가 완료되었습니다.", progress=100)
                return True
            if process.poll() is not None:
                break
            time.sleep(0.2)
        time.sleep(0.8)
    return False


def main() -> int:
    os.chdir(PROJECT_ROOT)
    if port_is_open():
        webbrowser.open(URL)
        return 0

    loading_server = ThreadingHTTPServer((HOST, PORT), LoadingHandler)
    thread = threading.Thread(target=loading_server.serve_forever, daemon=True)
    thread.start()
    webbrowser.open(URL)

    if run_bootstrap() != 0:
        STATUS.update(state="error", message=f"환경 준비에 실패했습니다. 로그를 확인하세요: {LOG_PATH}")
        while True:
            time.sleep(60)

    STATUS.update(state="preparing", message="환경 준비가 완료되었습니다. 서버로 전환하고 있습니다.", progress=97)
    loading_server.shutdown()
    loading_server.server_close()
    thread.join(timeout=3)
    time.sleep(0.8)
    if start_app_server():
        return 0

    STATUS.update(state="error", message=f"서버 시작에 실패했습니다. 로그를 확인하세요: {LOG_FOLDER / 'server.log'}")
    error_server = ThreadingHTTPServer((HOST, PORT), LoadingHandler)
    error_server.serve_forever()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
