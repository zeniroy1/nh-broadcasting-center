from __future__ import annotations

import csv
import json
import mimetypes
import os
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

from app.collectors.lh_direct import collect_lh_notice_payloads, collect_lh_regions, discover_lh_notices
from app.collectors.hug_direct import HugRegion, collect_region, parse_regions
from app.collectors.sh_direct import collect_sh_notice_payloads, discover_sh_notices
from app.collectors.gh_direct import collect_gh
from app.core.config import load_settings
from app.core.paths import app_root, project_root
from app.core.validation import check_required_layout, missing_required_files
from app.metrics.registry import load_metric_registry


HOST = "127.0.0.1"
PORT = 8765


def json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False).encode("utf-8")


def relative(path: Path) -> str:
    return path.resolve().relative_to(project_root().resolve()).as_posix()


def safe_project_path(value: str) -> Path:
    root = project_root().resolve()
    target = (root / unquote(value)).resolve()
    if root != target and root not in target.parents:
        raise ValueError("Path is outside project root.")
    return target


def csv_count(path: Path) -> int | None:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            return max(0, sum(1 for _ in csv.reader(file)) - 1)
    except Exception:
        return None


def result_files() -> list[dict[str, object]]:
    root = project_root()
    settings = load_settings()
    source_folders = (
        ("HUG", root / settings["hug"].get("output_folder", "hug/outputs")),
        ("LH", root / settings["lh"].get("output_folder", "lh/outputs")),
        ("SH", root / settings.get("sh", {}).get("output_folder", "sh/outputs")),
        ("GH", root / settings.get("gh", {}).get("output_folder", "gh/outputs")),
    )
    results: list[dict[str, object]] = []
    for source, folder in source_folders:
        if not folder.exists():
            continue
        patterns = ["*.csv", "*.txt"]
        for pattern in patterns:
            for path in sorted(folder.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True):
                if source == "LH" and "_capture_" in path.name:
                    continue
                status = "요약" if path.suffix.lower() == ".txt" else "데이터"
                rows = csv_count(path) if path.suffix.lower() == ".csv" else None
                if rows is not None:
                    status = f"{rows:,}건"
                results.append(
                    {
                        "source": source,
                        "name": path.name,
                        "relativePath": relative(path),
                        "status": status,
                        "size": path.stat().st_size,
                    }
                )
    return results



def app_state() -> dict[str, object]:
    settings = load_settings()
    checks = check_required_layout(settings)
    metrics = load_metric_registry()
    return {
        "settings": settings,
        "metrics": metrics.summary(),
        "layout": [{"key": item.key, "path": str(item.path), "exists": item.exists} for item in checks],
        "layoutOk": not missing_required_files(settings),
        "results": result_files(),
    }


def open_file(path: Path) -> None:
    if os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]
    else:
        webbrowser.open(path.as_uri())


def open_folder(path: Path) -> None:
    folder = path if path.is_dir() else path.parent
    open_file(folder)


def run_lh_regions(region_names: list[str]) -> list[dict[str, object]]:
    runs = collect_lh_regions(region_names)
    return [
        {
            "region": run.region,
            "rows": run.rows,
            "applications": run.applications,
            "report": run.report,
            "data": run.csv,
            "distanceData": run.distance_csv,
            "title": run.title,
        }
        for run in runs
    ]


def lh_notice_candidates(region_names: list[str]) -> list[dict[str, object]]:
    return [
        {
            "id": item.id,
            "requested_region": item.requested_region,
            "notice_region": item.notice_region,
            "title": item.title,
            "pan_id": item.pan_id,
            "ais_tp_cd": item.ais_tp_cd,
            "ccr_cnnt_sys_ds_cd": item.ccr_cnnt_sys_ds_cd,
            "upp_ais_tp_cd": item.upp_ais_tp_cd,
            "status": item.status,
            "apply_start": item.apply_start,
            "apply_end": item.apply_end,
            "detail_url": item.detail_url,
        }
        for item in discover_lh_notices(region_names)
    ]


def run_lh_notices(notices: list[dict[str, object]]) -> list[dict[str, object]]:
    runs = collect_lh_notice_payloads(notices)
    return [
        {
            "region": run.region,
            "rows": run.rows,
            "applications": run.applications,
            "report": run.report,
            "data": run.csv,
            "distanceData": run.distance_csv,
            "title": run.title,
        }
        for run in runs
    ]


def run_hug_regions(region_names: list[str]) -> list[dict[str, object]]:
    settings = load_settings()
    namespace = type("Args", (), {"preset": None, "region": region_names})()
    regions = parse_regions(namespace, settings)
    output: list[dict[str, object]] = []
    for region in regions:
        if not isinstance(region, HugRegion):
            continue
        data_path, summary_path, row_count, last_page = collect_region(region, settings)
        output.append(
            {
                "region": region.name,
                "rows": row_count,
                "pages": last_page,
                "data": relative(data_path),
                "summary": relative(summary_path),
            }
        )
    return output


def sh_notice_candidates(region_names: list[str]) -> list[dict[str, object]]:
    return [
        {
            "id": item.id,
            "requested_region": item.requested_region,
            "notice_region": item.notice_region,
            "title": item.title,
            "seq": item.seq,
            "department": item.department,
            "notice_date": item.notice_date,
            "views": item.views,
            "status": item.status,
            "apply_start": item.apply_start,
            "apply_end": item.apply_end,
            "detail_url": item.detail_url,
        }
        for item in discover_sh_notices(region_names)
    ]


def run_sh_notices(notices: list[dict[str, object]]) -> list[dict[str, object]]:
    runs = collect_sh_notice_payloads(notices)
    return [
        {
            "region": run.region,
            "rows": run.rows,
            "report": run.report,
            "data": run.csv,
            "title": run.title,
        }
        for run in runs
    ]


def run_gh(keyword_parts: list[str]) -> list[dict[str, object]]:
    keyword = " ".join(part.strip() for part in keyword_parts if part.strip())
    runs = collect_gh(keyword)
    return [
        {
            "status": run.status,
            "phase": run.phase,
            "rows": run.rows,
            "data": run.data,
            "summary": run.summary,
        }
        for run in runs
    ]


class AppHandler(BaseHTTPRequestHandler):
    server_version = "IntegratedCrawler/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/state":
            self.send_json(app_state())
            return
        if parsed.path == "/api/download":
            self.handle_download(parsed.query)
            return
        self.serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/lh/notices":
                payload = self.read_json()
                regions = [str(item).strip() for item in payload.get("regions", []) if str(item).strip()]
                if not regions:
                    self.send_json({"ok": False, "message": "LH 지역을 하나 이상 선택하세요."}, status=400)
                    return
                notices = lh_notice_candidates(regions)
                self.send_json(
                    {
                        "ok": True,
                        "notices": notices,
                        "message": f"접수예정/접수중 LH 공고 {len(notices):,}건을 찾았습니다.",
                    }
                )
            elif parsed.path == "/api/lh/collect":
                payload = self.read_json()
                notices = payload.get("notices", [])
                if isinstance(notices, list) and notices:
                    self.send_json({"ok": True, "runs": run_lh_notices(notices), "results": result_files(), "message": "LH 선택 공고 분석이 완료되었습니다."})
                    return
                regions = [str(item).strip() for item in payload.get("regions", []) if str(item).strip()]
                if not regions:
                    self.send_json({"ok": False, "message": "분석할 LH 공고 또는 지역을 하나 이상 선택하세요."}, status=400)
                    return
                self.send_json({"ok": True, "runs": run_lh_regions(regions), "results": result_files(), "message": "LH 직접수집이 완료되었습니다."})
            elif parsed.path == "/api/hug/collect":
                payload = self.read_json()
                regions = [str(item).strip() for item in payload.get("regions", []) if str(item).strip()]
                if not regions:
                    self.send_json({"ok": False, "message": "지역을 하나 이상 선택하세요."}, status=400)
                    return
                self.send_json({"ok": True, "runs": run_hug_regions(regions), "results": result_files()})
            elif parsed.path == "/api/sh/notices":
                payload = self.read_json()
                regions = [str(item).strip() for item in payload.get("regions", []) if str(item).strip()]
                if not regions:
                    self.send_json({"ok": False, "message": "SH 검색어를 하나 이상 입력하세요."}, status=400)
                    return
                notices = sh_notice_candidates(regions)
                self.send_json(
                    {
                        "ok": True,
                        "notices": notices,
                        "message": f"검색어 기준 접수예정/접수중 SH 공고 {len(notices):,}건을 찾았습니다.",
                    }
                )
            elif parsed.path == "/api/sh/collect":
                payload = self.read_json()
                notices = payload.get("notices", [])
                if not isinstance(notices, list) or not notices:
                    self.send_json({"ok": False, "message": "분석할 SH 공고를 하나 이상 선택하세요."}, status=400)
                    return
                self.send_json({"ok": True, "runs": run_sh_notices(notices), "results": result_files(), "message": "SH 선택 공고 분석이 완료되었습니다."})
            elif parsed.path == "/api/gh/collect":
                payload = self.read_json()
                keyword_parts = [str(item).strip() for item in payload.get("regions", []) if str(item).strip()]
                runs = run_gh(keyword_parts)
                self.send_json({"ok": True, "runs": runs, "results": result_files(), "message": "GH 일정 및 실시간/최종 경쟁률 수집이 완료되었습니다."})
            elif parsed.path == "/api/file/open":
                path = safe_project_path(str(self.read_json().get("path", "")))
                open_file(path)
                self.send_json({"ok": True})
            elif parsed.path == "/api/file/folder":
                path = safe_project_path(str(self.read_json().get("path", "")))
                open_folder(path)
                self.send_json({"ok": True})
            else:
                self.send_json({"ok": False, "message": "Unknown endpoint."}, status=404)
        except Exception as error:
            self.send_json({"ok": False, "message": str(error)}, status=500)

    def read_json(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def send_json(self, value: object, status: int = 200) -> None:
        body = json_bytes(value)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_static(self, path_value: str) -> None:
        ui_root = app_root() / "ui"
        path = "index.html" if path_value in ("", "/") else path_value.lstrip("/")
        target = (ui_root / path).resolve()
        if ui_root.resolve() != target and ui_root.resolve() not in target.parents:
            self.send_error(403)
            return
        if not target.exists() or not target.is_file():
            self.send_error(404)
            return
        body = target.read_bytes()
        mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_download(self, query: str) -> None:
        params = parse_qs(query)
        target = safe_project_path(params.get("path", [""])[0])
        if not target.exists() or not target.is_file():
            self.send_error(404)
            return
        body = target.read_bytes()
        mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", mime)
        safe_name = quote(target.name)
        self.send_header("Content-Disposition", f"attachment; filename=download; filename*=UTF-8''{safe_name}")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> int:
    os.chdir(project_root())
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    url = f"http://{HOST}:{PORT}/"
    print(f"통합 프로그램 실행: {url}")
    if os.environ.get("APP_SKIP_BROWSER") != "1":
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("종료")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())








