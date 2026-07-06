"""Run the Musinsa buyer app as a local web server."""

from __future__ import annotations

import argparse
import json
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


CURRENT_DIR = Path(__file__).resolve().parent
SRC_ROOT = CURRENT_DIR.parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from musinsa_live_buyer_app import build_buyer_app_model
from musinsa_keyword_learning import update_keyword_discovery_from_terms
from musinsa_scoring_model import DEFAULT_QUERY
from musinsa_runtime_paths import app_data_root, is_frozen, resource_path

APP_PATH = resource_path("app", "musinsa_buyer_app.html")


TREND_API_URLS = [
    "https://client.musinsa.com/api/display/v1/search/web/keyword/search-home?popularCount=10&gf=A",
    "https://api.musinsa.com/api2/dp/v1/keyword/search-home?popularCount=10&gf=A",
]
KST = timezone(timedelta(hours=9))
HEARTBEAT_TIMEOUT_SECONDS = 20


class BuyerAppState:
    last_heartbeat = time.monotonic()
    shutdown_started = False
    lock = threading.Lock()

    @classmethod
    def touch(cls) -> None:
        with cls.lock:
            cls.last_heartbeat = time.monotonic()

    @classmethod
    def should_shutdown(cls) -> bool:
        with cls.lock:
            if cls.shutdown_started:
                return False
            stale_for = time.monotonic() - cls.last_heartbeat
            if stale_for < HEARTBEAT_TIMEOUT_SECONDS:
                return False
            cls.shutdown_started = True
            return True


def _json_bytes(payload: dict[str, Any], status: str = "ok") -> bytes:
    return json.dumps({"status": status, **payload}, ensure_ascii=False).encode("utf-8")


def build_recommendation_payload(
    query: str,
    fetch_live: bool = True,
    exclude_product_ids: list[str] | None = None,
) -> dict[str, Any]:
    model = build_buyer_app_model(query=query, fetch_live=fetch_live, exclude_product_ids=exclude_product_ids)
    return {
        "model": model,
        "summary": {
            "collection_mode": model["collection_mode"],
            "collected_public_product_count": model["collected_public_product_count"],
            "filtered_public_product_count": model["filtered_public_product_count"],
            "scored_candidate_count": model["scored_candidate_count"],
            "excluded_product_count": len(model["excluded_product_ids"]),
            "keyword_learning": {"updated": 0, "terms": [], "review_ready": []},
            "winner": model["recommendation_report"]["comparison_table"]["rows"][0]
            if model["recommendation_report"]["comparison_table"]["rows"]
            else None,
        },
    }


def fetch_search_trend_json(url: str, timeout: int = 8) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Origin": "https://www.musinsa.com",
            "Referer": "https://www.musinsa.com/",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", "ignore")


def parse_search_trends(raw_json: str) -> dict[str, Any]:
    payload = json.loads(raw_json)
    data = payload.get("data", payload)
    components = data.get("componentList") or []
    trends: dict[str, Any] = {
        "search_url": data.get("searchUrl") or "https://www.musinsa.com/search/goods?keyword={keyword}",
        "popular": {"title": "인기 검색어", "updated_at": "", "items": []},
        "rising": {"title": "급상승 검색어", "updated_at": "", "items": []},
    }

    for component in components:
        key = component.get("key")
        if key not in {"popular", "rising"}:
            continue
        meta = component.get("meta") or {}
        items = []
        for index, item in enumerate(component.get("items") or [], start=1):
            text = str(item.get("text") or "").strip()
            if not text:
                continue
            items.append(
                {
                    "rank": index,
                    "text": text,
                    "rank_increment": int(item.get("rankIncrement") or 0),
                    "landing_url": item.get("landingUrl") or "",
                }
            )
        trends[key] = {
            "title": meta.get("title") or trends[key]["title"],
            "updated_at": meta.get("updateDate") or "",
            "items": items,
        }
    return trends


def _trend_terms(trends: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    for section in ("popular", "rising"):
        for item in trends.get(section, {}).get("items") or []:
            text = str(item.get("text") or "").strip()
            if text:
                terms.append(text)
    return terms


def _record_trend_keyword_discovery(
    trends: dict[str, Any],
    source: str,
    discovery_path: str | Path | None,
    errors: list[str],
) -> dict[str, Any]:
    try:
        if discovery_path is None:
            return update_keyword_discovery_from_terms(_trend_terms(trends), f"search_trends:{source}")
        return update_keyword_discovery_from_terms(
            _trend_terms(trends),
            f"search_trends:{source}",
            path=discovery_path,
        )
    except Exception as exc:
        errors.append(f"keyword_discovery: {exc}")
        return {"updated": 0, "terms": [], "review_ready": [], "source": source, "error": str(exc)}


def build_search_trends_payload(
    fetch_live: bool = True,
    raw_json: str | None = None,
    record_discovery: bool = False,
    discovery_path: str | Path | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    if raw_json is not None:
        trends = parse_search_trends(raw_json)
        source = "raw_json"
    elif fetch_live:
        trends = None
        source = ""
        for url in TREND_API_URLS:
            try:
                trends = parse_search_trends(fetch_search_trend_json(url))
                source = url
                break
            except Exception as exc:
                errors.append(f"{url}: {exc}")
        if trends is None:
            trends = parse_search_trends('{"data":{"componentList":[]}}')
            source = "unavailable"
    else:
        trends = parse_search_trends(
            """
            {"data":{"searchUrl":"https://www.musinsa.com/search/goods?keyword={keyword}","componentList":[
              {"key":"popular","meta":{"title":"인기 검색어","updateDate":"샘플 기준"},"items":[{"text":"반팔","rankIncrement":0,"landingUrl":"https://www.musinsa.com/search/goods?keyword=반팔"},{"text":"반바지","rankIncrement":1,"landingUrl":"https://www.musinsa.com/search/goods?keyword=반바지"}]},
              {"key":"rising","meta":{"title":"급상승 검색어","updateDate":"샘플 기준"},"items":[{"text":"하객룩","rankIncrement":20,"landingUrl":"https://www.musinsa.com/search/goods?keyword=하객룩"},{"text":"트레이닝 팬츠","rankIncrement":18,"landingUrl":"https://www.musinsa.com/search/goods?keyword=트레이닝 팬츠"}]}
            ]}}
            """
        )
        source = "sample"

    keyword_discovery = (
        _record_trend_keyword_discovery(trends, source, discovery_path, errors)
        if record_discovery and source not in {"sample", "unavailable"}
        else {"updated": 0, "terms": [], "review_ready": [], "source": source}
    )
    return {
        "source": source,
        "fetched_at": datetime.now(KST).strftime("%m.%d %H:%M:%S"),
        "refresh_seconds": 60,
        "errors": errors,
        "keyword_discovery": keyword_discovery,
        "trends": trends,
    }


class BuyerAppHandler(BaseHTTPRequestHandler):
    server_version = "MusinsaBuyerServer/0.1"

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in {"/", "/app", "/app/"}:
            BuyerAppState.touch()
            self._send_html()
            return
        if parsed.path == "/api/recommend":
            BuyerAppState.touch()
            self._send_recommendation(parsed.query)
            return
        if parsed.path == "/api/search-trends":
            BuyerAppState.touch()
            self._send_search_trends(parsed.query)
            return
        if parsed.path == "/api/heartbeat":
            BuyerAppState.touch()
            self._send_json({"ok": True})
            return
        if parsed.path == "/health":
            self._send_json({"ok": True})
            return
        self.send_error(404, "Not found")

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))

    def _send_html(self) -> None:
        content = APP_PATH.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, payload: dict[str, Any], status_code: int = 200) -> None:
        content = _json_bytes(payload)
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_recommendation(self, raw_query: str) -> None:
        params = urllib.parse.parse_qs(raw_query)
        query = params.get("query", [DEFAULT_QUERY])[0].strip() or DEFAULT_QUERY
        fetch_live = params.get("live", ["1"])[0] != "0"
        exclude = [
            item
            for raw in params.get("exclude", [])
            for item in re.split(r"\|\||,", raw)
            if item
        ]
        try:
            self._send_json(
                build_recommendation_payload(
                    query,
                    fetch_live=fetch_live,
                    exclude_product_ids=exclude,
                )
            )
        except Exception as exc:
            self._send_json({"message": str(exc)}, status_code=500)

    def _send_search_trends(self, raw_query: str) -> None:
        params = urllib.parse.parse_qs(raw_query)
        fetch_live = params.get("live", ["1"])[0] != "0"
        try:
            self._send_json(build_search_trends_payload(fetch_live=fetch_live, record_discovery=True))
        except Exception as exc:
            self._send_json({"message": str(exc)}, status_code=500)


def _redirect_io_for_windowed_exe() -> None:
    """Keep print()/tracebacks from crashing a console-less frozen build.

    A --noconsole / --windowed PyInstaller build has no attached console, so
    sys.stdout/sys.stderr can be None. Any stray print() or unhandled
    traceback would then raise AttributeError and silently kill the app.
    Redirect both to a log file next to the executable instead, which also
    gives the user somewhere to look if something goes wrong.
    """
    if not is_frozen():
        return
    if sys.stdout is not None and sys.stderr is not None:
        return
    log_path = app_data_root() / "musinsa_buyer_app.log"
    try:
        log_file = open(log_path, "a", encoding="utf-8", buffering=1)
    except OSError:
        return
    sys.stdout = log_file
    sys.stderr = log_file


def _open_browser_when_ready(url: str, delay: float = 0.6) -> None:
    def _worker() -> None:
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    threading.Thread(target=_worker, daemon=True).start()


def _start_idle_shutdown_watch(server: ThreadingHTTPServer) -> None:
    def _worker() -> None:
        while True:
            time.sleep(2)
            if BuyerAppState.should_shutdown():
                print("No active browser heartbeat; shutting down Musinsa buyer app.", flush=True)
                server.shutdown()
                break

    threading.Thread(target=_worker, daemon=True).start()


def run_server(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = False) -> None:
    url = f"http://{host}:{port}/"
    try:
        server = ThreadingHTTPServer((host, port), BuyerAppHandler)
    except OSError:
        # Port already bound, most likely by a previous launch of this same
        # app (e.g. the user double-clicked the exe twice). Reuse it instead
        # of crashing with "Address already in use".
        print(f"Musinsa buyer app already running at {url}", flush=True)
        if open_browser:
            webbrowser.open(url)
        return
    print(f"Musinsa buyer app running at {url}", flush=True)
    if open_browser:
        _open_browser_when_ready(url)
        _start_idle_shutdown_watch(server)
    server.serve_forever()
    server.server_close()


def main() -> None:
    _redirect_io_for_windowed_exe()

    parser = argparse.ArgumentParser(description="Run Musinsa buyer app server.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind")
    parser.add_argument("--check", action="store_true", help="Build a sample API payload and exit")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically open the app in a browser on start",
    )
    args = parser.parse_args()

    if args.check:
        payload = build_recommendation_payload(DEFAULT_QUERY, fetch_live=False)
        print(json.dumps({"ok": True, "summary": payload["summary"]}, ensure_ascii=False, indent=2))
        return
    # Frozen (double-click) launches always auto-open the browser; running
    # from source defaults to auto-open too, but can be disabled for scripted use.
    run_server(args.host, args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
