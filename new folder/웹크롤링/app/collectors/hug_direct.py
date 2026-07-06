from __future__ import annotations

import argparse
import csv
import html
import json
import math
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from app.core.config import load_settings
from app.core.paths import project_root
from app.metrics.registry import load_metric_registry
from app.reports.hug_markdown import write_hug_summary

BASE_URL = (
    "https://www.khug.or.kr/jeonse/web/s07/s070102.jsp"
    "?BJAMT=ALL&sbGugun=ALL&view_Count=Y&BJAREA=ALL&BJORDER=ALL"
    "&CMB_SIDO={code}&cur_page={page}"
)

SEOUL_TRANSIT = {
    "서울특별시 강북구 수유동": "약 35~45분",
    "서울특별시 강서구 공항동": "약 35~45분",
    "서울특별시 강서구 내발산동": "약 25~35분",
    "서울특별시 강서구 등촌동": "약 25~35분",
    "서울특별시 강서구 방화동": "약 35~45분",
    "서울특별시 강서구 염창동": "약 25~35분",
    "서울특별시 강서구 화곡동": "약 25~35분",
    "서울특별시 관악구 신림동": "약 30~40분",
    "서울특별시 광진구 화양동": "약 30~40분",
    "서울특별시 구로구 개봉동": "약 35~45분",
    "서울특별시 구로구 고척동": "약 35~45분",
    "서울특별시 구로구 구로동": "약 35~45분",
    "서울특별시 구로구 궁동": "약 40~50분",
    "서울특별시 구로구 오류동": "약 40~50분",
    "서울특별시 구로구 온수동": "약 40~50분",
    "서울특별시 구로구 천왕동": "약 45~55분",
    "서울특별시 금천구 가산동": "약 40~50분",
    "서울특별시 금천구 독산동": "약 45~55분",
    "서울특별시 금천구 시흥동": "약 45~60분",
    "서울특별시 도봉구 도봉동": "약 45~55분",
    "서울특별시 도봉구 방학동": "약 40~50분",
    "서울특별시 동작구 사당동": "약 30~40분",
    "서울특별시 양천구 목동": "약 20~30분",
    "서울특별시 양천구 신월동": "약 25~35분",
    "서울특별시 양천구 신정동": "약 20~30분",
    "서울특별시 영등포구 당산동": "약 15~25분",
    "서울특별시 영등포구 당산동1가": "약 15~25분",
    "서울특별시 영등포구 대림동": "약 25~35분",
    "서울특별시 영등포구 양평동2가": "약 15~25분",
    "서울특별시 영등포구 영등포동7가": "약 15~20분",
    "서울특별시 은평구 역촌동": "약 25~35분",
    "서울특별시 은평구 응암동": "약 25~35분",
    "서울특별시 중랑구 상봉동": "약 35~45분",
}


@dataclass(frozen=True)
class HugRegion:
    name: str
    code: str


class HugTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_tr = False
        self.in_td = False
        self.rows: list[list[str]] = []
        self.row: list[str] = []
        self.buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self.in_tr = True
            self.row = []
        elif tag == "td" and self.in_tr:
            self.in_td = True
            self.buffer = []

    def handle_data(self, data: str) -> None:
        if self.in_td:
            self.buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self.in_td:
            text = re.sub(r"\s+", " ", "".join(self.buffer)).strip()
            self.row.append(html.unescape(text))
            self.in_td = False
        elif tag == "tr" and self.in_tr:
            if len(self.row) >= 11 and self.row[0].isdigit():
                self.rows.append(self.row[:11])
            self.in_tr = False


def fetch_html(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(request, timeout=40).read()
    return raw.decode("cp949", errors="replace")


def parse_pages(region: HugRegion) -> tuple[int, list[list[str]]]:
    first = fetch_html(BASE_URL.format(code=region.code, page=1))
    pages = [int(value) for value in re.findall(r"cur_page=(\d+)", first)]
    last_page = max(pages) if pages else 1
    rows: list[list[str]] = []
    for page in range(1, last_page + 1):
        document = first if page == 1 else fetch_html(BASE_URL.format(code=region.code, page=page))
        parser = HugTableParser()
        parser.feed(document)
        rows.extend(parser.rows)
        time.sleep(0.15)
    return last_page, rows


def has_valid_apply_period(value: str) -> bool:
    text = re.sub(r"\s+", "", str(value or ""))
    if not text or text in {"-", "없음", "해당없음"}:
        return False
    if "조회된데이터가없" in text:
        return False
    return bool(re.search(r"\d{2,4}[./-]\d{1,2}[./-]\d{1,2}", text))


def numeric(value: Any) -> float:
    match = re.search(r"-?\d+(?:\.\d+)?", str(value or "").replace(",", ""))
    return float(match.group()) if match else 0.0


def money_text(value: str) -> str:
    cleaned = re.sub(r"\s+", "", value or "")
    return cleaned if cleaned.endswith("원") else f"{cleaned}원"


def location_key(address: str) -> str:
    text = re.sub(r"\s+", " ", address or "").strip()
    for pattern in (
        r"^(서울특별시)\s+(\S+)\s+(\S+)",
        r"^(서울)\s+(\S+)\s+(\S+)",
        r"^(경기도)\s+(\S+)\s+(\S+)\s+(\S+)",
        r"^(경기)\s+(\S+)\s+(\S+)",
        r"^(인천광역시)\s+(\S+)\s+(\S+)",
        r"^(인천)\s+(\S+)\s+(\S+)",
    ):
        match = re.search(pattern, text)
        if match:
            parts = list(match.groups())
            parts[0] = {"서울": "서울특별시", "경기": "경기도", "인천": "인천광역시"}.get(parts[0], parts[0])
            return " ".join(parts)
    return ""


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0088
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    value = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(value))


def geocode(key: str, cache: dict[str, Any], cache_path: Path) -> dict[str, Any]:
    if not key:
        return {"lat": None, "lon": None}
    if key in cache:
        return cache[key]
    query = urllib.parse.quote(key)
    url = f"https://nominatim.openstreetmap.org/search?format=jsonv2&limit=3&countrycodes=kr&q={query}"
    request = urllib.request.Request(url, headers={"User-Agent": "CodexLocalHugCollector/1.0"})
    try:
        data = json.loads(urllib.request.urlopen(request, timeout=25).read().decode("utf-8"))
    except Exception:
        data = []
    if data:
        cache[key] = {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"])}
    else:
        cache[key] = {"lat": None, "lon": None}
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    time.sleep(1.0)
    return cache[key]


def estimate_transit_time(key: str, distance_km: float | None) -> str:
    if key in SEOUL_TRANSIT:
        return SEOUL_TRANSIT[key]
    if distance_km is None:
        return "확인필요"
    midpoint = max(20, min(95, round(16 + distance_km * 2.4)))
    return f"약 {max(15, midpoint - 7)}~{midpoint + 8}분"


def add_rank(rows: list[dict[str, Any]], field: str, rank_name: str) -> None:
    for index, row in enumerate(sorted(rows, key=lambda item: item[field]), 1):
        row[rank_name] = index


def build_rows(raw_rows: list[list[str]], settings: dict[str, Any], cache: dict[str, Any], cache_path: Path) -> list[dict[str, Any]]:
    target = settings["hug"]["target_location"]
    rows: list[dict[str, Any]] = []
    for raw in raw_rows:
        key = location_key(raw[5])
        geo = geocode(key, cache, cache_path)
        distance = None
        if geo.get("lat") is not None:
            distance = round(haversine(target["lat"], target["lon"], geo["lat"], geo["lon"]), 2)
        deposit = money_text(raw[9])
        rows.append(
            {
                "번호": raw[0],
                "공고일자": raw[1],
                "접수기간": raw[2],
                "시도": raw[3],
                "시군구": raw[4],
                "주소": raw[5],
                "주택유형": raw[6],
                "매입유형": raw[7],
                "전용면적": raw[8],
                "임대보증금": deposit,
                "임대보증금_숫자": int(numeric(deposit)),
                "신청자수": int(numeric(raw[10])),
                "서대문역5번출구_추정거리_km": distance,
                "서대문역_최단지하철예상시간": estimate_transit_time(key, distance),
                "거리좌표기준": key,
            }
        )
    add_rank(rows, "임대보증금_숫자", "보증금순위")
    distance_rows = [row for row in rows if row["서대문역5번출구_추정거리_km"] is not None]
    add_rank(distance_rows, "서대문역5번출구_추정거리_km", "거리순위")
    add_rank(rows, "신청자수", "신청자순위")
    for row in rows:
        row["종합점수"] = row.get("보증금순위", 9999) + row.get("거리순위", 9999) + row.get("신청자순위", 9999)
    return rows


def output_paths(settings: dict[str, Any], region_name: str) -> tuple[Path, Path]:
    root = project_root()
    folder = root / settings["hug"].get("output_folder", f"{settings['hug']['folder']}/outputs")
    patterns = settings["hug"]["output_patterns"]
    return folder / patterns["data"].format(region=region_name), folder / patterns["summary"].format(region=region_name)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    registry = load_metric_registry()
    columns = [
        "번호",
        "공고일자",
        "접수기간",
        "시도",
        "시군구",
        "주소",
        "주택유형",
        "매입유형",
        "전용면적",
        "임대보증금",
        "신청자수",
        "서대문역5번출구_추정거리_km",
        "서대문역_최단지하철예상시간",
        "종합점수",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            registry.profile_record({key: row.get(key, "") for key in columns}, "hug")
            writer.writerow({key: row.get(key, "") for key in columns})


def collect_region(region: HugRegion, settings: dict[str, Any]) -> tuple[Path, Path, int, int]:
    cache_path = project_root() / "app" / "cache" / "hug" / f"{region.name}_geocode.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8-sig")) if cache_path.exists() else {}
    last_page, raw_rows = parse_pages(region)
    data_path, summary_path = output_paths(settings, region.name)
    scheduled_rows = [row for row in raw_rows if len(row) > 2 and has_valid_apply_period(row[2])]
    if not scheduled_rows:
        for path in (data_path, summary_path):
            if path.exists():
                path.unlink()
        raise ValueError(f"HUG {region.name} 지역은 현재 공고일정이 없어 결과물을 생성하지 않았습니다.")
    rows = build_rows(scheduled_rows, settings, cache, cache_path)
    write_csv(data_path, rows)
    write_hug_summary(summary_path, region.name, rows, last_page, settings)
    return data_path, summary_path, len(rows), last_page

def discover_region_codes() -> dict[str, str]:
    document = fetch_html(BASE_URL.format(code="01", page=1))
    codes: dict[str, str] = {}
    for code, name in re.findall(r"<option value='([^']+)'>([^<]+)</option>", document):
        cleaned = re.sub(r"\s+", " ", html.unescape(name)).strip()
        if cleaned and code != "ALL":
            codes[cleaned] = code
    return codes


def resolve_region_code(region_name: str, settings: dict[str, Any], discovered: dict[str, str]) -> str:
    presets = settings["hug"]["region_presets"]
    if region_name in presets:
        return presets[region_name]
    if region_name in discovered:
        return discovered[region_name]
    matches = [(name, code) for name, code in discovered.items() if name == region_name or name.endswith(f" {region_name}")]
    if len(matches) == 1:
        return matches[0][1]
    if len(matches) > 1:
        choices = ", ".join(name for name, _ in matches[:10])
        raise SystemExit(f"Region name is ambiguous: {region_name}. Matches: {choices}")
    available = ", ".join(list(presets) + list(discovered)[:20])
    raise SystemExit(f"Unknown HUG region name: {region_name}. Available examples: {available}")

def parse_regions(args: argparse.Namespace, settings: dict[str, Any]) -> list[HugRegion]:
    presets = settings["hug"]["region_presets"]
    requested = list(args.preset or []) + list(args.region or [])
    if not requested:
        available = ", ".join(presets)
        raise SystemExit(f"Select at least one region. Presets: {available}")
    discovered: dict[str, str] | None = None
    regions: list[HugRegion] = []
    for name in requested:
        cleaned = name.strip()
        if cleaned in presets:
            regions.append(HugRegion(cleaned, presets[cleaned]))
            continue
        if discovered is None:
            discovered = discover_region_codes()
        regions.append(HugRegion(cleaned, resolve_region_code(cleaned, settings, discovered)))
    return regions


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect HUG region data.")
    parser.add_argument("--preset", action="append", help="Preset region name from settings.")
    parser.add_argument("--region", action="append", help="Region name to resolve from HUG options.")
    args = parser.parse_args()
    settings = load_settings()
    for region in parse_regions(args, settings):
        data_path, summary_path, row_count, last_page = collect_region(region, settings)
        print(f"{region.name}: pages={last_page}, rows={row_count}")
        print(f"  data: {data_path}")
        print(f"  summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



