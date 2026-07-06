from __future__ import annotations

import importlib.util
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
import urllib.parse

from app.core.paths import project_root
from app.metrics.registry import load_metric_registry


@dataclass(frozen=True)
class LhDirectRun:
    region: str
    rows: int
    applications: int
    report: str
    csv: str
    distance_csv: str
    title: str


@dataclass(frozen=True)
class LhNoticeCandidate:
    id: str
    requested_region: str
    notice_region: str
    title: str
    pan_id: str
    ais_tp_cd: str
    ccr_cnnt_sys_ds_cd: str
    upp_ais_tp_cd: str
    status: str
    apply_start: str
    apply_end: str
    detail_url: str


def load_generator() -> Any:
    script = project_root() / "lh" / "scripts" / "generate_reports.py"
    spec = importlib.util.spec_from_file_location("lh_generate_reports", script)
    if spec is None or spec.loader is None:
        raise RuntimeError("LH 보고서 생성 스크립트를 불러오지 못했습니다.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module



def project_relative(path: Path) -> str:
    return path.resolve().relative_to(project_root().resolve()).as_posix()


def compact(value: str) -> str:
    return "".join(str(value or "").split())


def unique_notices(notices: list[dict[str, str]]) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    seen: set[str] = set()
    for notice in notices:
        pan_id = notice.get("pan_id", "")
        if not pan_id or pan_id in seen:
            continue
        seen.add(pan_id)
        selected.append(notice)
    return selected


def notice_matches_region(notice: dict[str, str], region: str) -> bool:
    needle = compact(region)
    if not needle:
        return False
    title = compact(notice.get("title", ""))
    notice_region = compact(notice.get("region", ""))
    if needle in title or needle in notice_region:
        return True
    aliases = {
        "경기": ("경기도",),
        "서울": ("서울특별시",),
        "인천": ("인천광역시",),
        "부산": ("부산광역시", "부산울산"),
        "울산": ("울산광역시", "부산울산"),
    }
    for alias in aliases.get(needle, ()): 
        alias_compact = compact(alias)
        if alias_compact in title or alias_compact in notice_region:
            return True
    return False


def available_notice_text(notices: list[dict[str, str]]) -> str:
    if not notices:
        return "현재 LH 공고 목록에서 분석 가능한 공고를 찾지 못했습니다."
    lines = []
    for notice in notices[:8]:
        region = notice.get("region", "지역 미표시")
        title = notice.get("title", "공고명 미표시")
        lines.append(f"{region} - {title}")
    return "현재 직접수집 가능한 LH 공고: " + " / ".join(lines)


def detail_url_for_notice(notice: dict[str, str]) -> str:
    params = urllib.parse.urlencode(
        {
            "aisTpCd": notice.get("ais_tp_cd", "26"),
            "ccrCnntSysDsCd": notice.get("ccr_cnnt_sys_ds_cd", "03"),
            "mi": "1026",
            "panId": notice["pan_id"],
            "uppAisTpCd": notice.get("upp_ais_tp_cd", "13"),
        }
    )
    return "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancInfo.do?" + params


def parse_lh_datetime(date_value: str, time_value: str, end_of_day: bool) -> datetime | None:
    date_match = re.search(r"(\d{4})\D*(\d{1,2})\D*(\d{1,2})", str(date_value or ""))
    if not date_match:
        return None
    time_match = re.search(r"(\d{1,2})\D*(\d{2})", str(time_value or ""))
    hour = int(time_match.group(1)) if time_match else (23 if end_of_day else 0)
    minute = int(time_match.group(2)) if time_match else (59 if end_of_day else 0)
    return datetime(
        int(date_match.group(1)),
        int(date_match.group(2)),
        int(date_match.group(3)),
        hour,
        minute,
    )


def schedule_for_notice(generator: Any, notice: dict[str, str]) -> dict[str, Any]:
    html = generator.fetch_text(detail_url_for_notice(notice))
    registry = load_metric_registry()
    try:
        tables = generator.pd.read_html(generator.StringIO(html))
        registry_match = any(registry.has_required_set(table.columns, "competition_core", "lh") for table in tables)
        if not registry_match:
            generator.select_supply_table(tables)
        analyzable = True
    except Exception:
        analyzable = False
    start_date = generator.extract_js_value(html, "sbscAcpStDt")
    end_date = generator.extract_js_value(html, "sbscAcpClsgDt")
    start_time = generator.extract_js_value(html, "sbscAcpStHm")
    end_time = generator.extract_js_value(html, "sbscAcpClsgHm")
    start_at = parse_lh_datetime(start_date, start_time, False)
    end_at = parse_lh_datetime(end_date, end_time, True)
    if not start_at or not end_at:
        return {
            "status": "일정확인필요",
            "apply_start": "",
            "apply_end": "",
            "active": False,
            "analyzable": analyzable,
        }
    now = datetime.now()
    if now < start_at:
        status = "접수예정"
    elif now <= end_at:
        status = "접수중"
    else:
        status = "접수마감"
    return {
        "status": status,
        "apply_start": f"{start_date} {start_time}".strip(),
        "apply_end": f"{end_date} {end_time}".strip(),
        "active": now <= end_at,
        "analyzable": analyzable,
    }


def discover_lh_notices(region_names: list[str]) -> list[LhNoticeCandidate]:
    generator = load_generator()
    notices = unique_notices(generator.search_lh_notices(""))
    candidates: list[LhNoticeCandidate] = []
    seen: set[str] = set()
    for region in [name.strip() for name in region_names if name.strip()]:
        for notice in notices:
            if not notice_matches_region(notice, region):
                continue
            pan_id = notice.get("pan_id", "")
            key = f"{region}:{pan_id}"
            if not pan_id or key in seen:
                continue
            seen.add(key)
            try:
                schedule = schedule_for_notice(generator, notice)
            except Exception:
                schedule = {
                    "status": "일정확인필요",
                    "apply_start": "",
                    "apply_end": "",
                    "active": False,
                }
            if not schedule.get("active") or not schedule.get("analyzable"):
                continue
            candidates.append(
                LhNoticeCandidate(
                    id=key,
                    requested_region=region,
                    notice_region=notice.get("region", ""),
                    title=notice.get("title", ""),
                    pan_id=pan_id,
                    ais_tp_cd=notice.get("ais_tp_cd", "26"),
                    ccr_cnnt_sys_ds_cd=notice.get("ccr_cnnt_sys_ds_cd", "03"),
                    upp_ais_tp_cd=notice.get("upp_ais_tp_cd", "13"),
                    status=str(schedule["status"]),
                    apply_start=str(schedule["apply_start"]),
                    apply_end=str(schedule["apply_end"]),
                    detail_url=detail_url_for_notice(notice),
                )
            )
    return sorted(candidates, key=lambda item: (item.apply_start, item.requested_region, item.title))


def meta_for_notice(generator: Any, requested_region: str, notice: dict[str, str]) -> dict[str, str]:
    display_region = requested_region.strip() or generator.extract_region_hint(notice.get("title", ""), notice.get("title", ""))
    if not display_region:
        display_region = notice.get("region") or notice.get("title") or "LH"
    output_stem = generator.safe_filename(f"{display_region}_{notice.get('title', '')}")
    return {
        "key": display_region,
        "detected_by": "LH 공고 목록 직접 검색",
        "pan_id": notice["pan_id"],
        "ais_tp_cd": notice.get("ais_tp_cd", "26"),
        "ccr_cnnt_sys_ds_cd": notice.get("ccr_cnnt_sys_ds_cd", "03"),
        "upp_ais_tp_cd": notice.get("upp_ais_tp_cd", "13"),
        "title": notice.get("title", ""),
        "out": f"{output_stem}_경쟁률_보고서.txt",
        "csv": f"{output_stem}_경쟁률_전체데이터.csv",
        "dist_csv": f"{output_stem}_경쟁률_거리_전체데이터.csv",
    }


def collect_lh_notice_payloads(notice_payloads: list[dict[str, Any]]) -> list[LhDirectRun]:
    generator = load_generator()
    selected: list[tuple[str, dict[str, str]]] = []
    seen_pan_ids: set[str] = set()

    for payload in notice_payloads:
        region = str(payload.get("requested_region") or payload.get("region") or "").strip()
        pan_id = str(payload.get("pan_id") or "").strip()
        if not region or not pan_id or pan_id in seen_pan_ids:
            continue
        seen_pan_ids.add(pan_id)
        selected.append(
            (
                region,
                {
                    "pan_id": pan_id,
                    "ccr_cnnt_sys_ds_cd": str(payload.get("ccr_cnnt_sys_ds_cd") or "03"),
                    "upp_ais_tp_cd": str(payload.get("upp_ais_tp_cd") or "13"),
                    "ais_tp_cd": str(payload.get("ais_tp_cd") or "26"),
                    "title": str(payload.get("title") or ""),
                    "region": str(payload.get("notice_region") or ""),
                },
            )
        )

    if not selected:
        raise ValueError("분석할 LH 공고를 하나 이상 선택하세요.")

    results: list[LhDirectRun] = []
    for region, notice in selected:
        meta = meta_for_notice(generator, region, notice)
        result = generator.build_report(meta)
        results.append(
            LhDirectRun(
                region=region,
                rows=int(result["rows"]),
                applications=int(result["applications"]),
                report=project_relative(Path(result["report"])),
                csv=project_relative(Path(result["csv"])),
                distance_csv=project_relative(Path(result["dist_csv"])),
                title=notice.get("title", ""),
            )
        )
    generator.write_combined_report([
        {
            "key": run.region,
            "report": project_root() / run.report,
            "csv": project_root() / run.csv,
            "dist_csv": project_root() / run.distance_csv,
            "rows": run.rows,
            "applications": run.applications,
        }
        for run in results
    ])
    return results


def collect_lh_regions(region_names: list[str]) -> list[LhDirectRun]:
    candidates = discover_lh_notices(region_names)
    if not candidates:
        raise ValueError("접수예정 또는 접수중인 LH 공고를 찾지 못했습니다. 접수마감 공고는 파싱목록에서 제외됩니다.")
    return collect_lh_notice_payloads([candidate.__dict__ for candidate in candidates])
