from __future__ import annotations

import csv
import html
import io
import json
import re
import time
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from app.core.config import load_settings
from app.core.paths import project_root
from app.metrics.registry import load_metric_registry


LIST_URL = (
    "https://www.i-sh.co.kr/main/lay2/program/S1T294C295/www/brd/m_241/list.do"
    "?multi_itm_seqs=1,2,4,8,16,32,64,128,256,512,1024"
)
DETAIL_URL = "https://www.i-sh.co.kr/main/lay2/program/S1T294C295/www/brd/m_241/view.do"
DOWNLOAD_URL = "https://www.i-sh.co.kr/main/com/file/innoFD.do"


@dataclass(frozen=True)
class ShNoticeCandidate:
    id: str
    requested_region: str
    notice_region: str
    title: str
    seq: str
    department: str
    notice_date: str
    views: str
    status: str
    apply_start: str
    apply_end: str
    detail_url: str


@dataclass(frozen=True)
class ShDirectRun:
    region: str
    rows: int
    report: str
    csv: str
    title: str


def project_relative(path: Path) -> str:
    return path.resolve().relative_to(project_root().resolve()).as_posix()


def safe_filename_part(value: object, fallback: str = "unknown") -> str:
    text = re.sub(r"\s+", "_", str(value or "").strip())
    text = re.sub(r'[\\/:*?"<>|]+', "_", text)
    text = re.sub(r"_+", "_", text).strip("._")
    return text[:80] or fallback


def output_stem(region: str, records: list[dict[str, str]]) -> str:
    region_part = safe_filename_part(region, "지역")
    if len(records) == 1:
        seq = safe_filename_part(records[0].get("게시글번호"), "공고")
        return f"sh_{region_part}_{seq}"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"sh_{region_part}_선택{len(records)}건_{stamp}"


def sh_settings() -> dict[str, Any]:
    settings = load_settings()
    return settings.get("sh", {})


def output_folder() -> Path:
    folder = project_root() / sh_settings().get("output_folder", "sh/outputs")
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def fetch_html(url: str, data: dict[str, str] | None = None) -> str:
    encoded = None
    if data is not None:
        encoded = urllib.parse.urlencode(data).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=encoded,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "ko-KR,ko;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    raw = urllib.request.urlopen(request, timeout=40).read()
    return raw.decode("utf-8", errors="replace")


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/pdf,application/octet-stream,*/*",
            "Accept-Language": "ko-KR,ko;q=0.9",
        },
    )
    return urllib.request.urlopen(request, timeout=40).read()


def normalize_space(value: object) -> str:
    return re.sub(r"\s+", " ", html.unescape(str(value or ""))).strip()


def compact(value: object) -> str:
    return re.sub(r"\s+", "", str(value or ""))


def notice_matches_region(text: str, region: str) -> bool:
    needle = compact(region)
    haystack = compact(text)
    if not needle:
        return False
    if needle in haystack:
        return True
    aliases = {
        "서울": ("서울특별시",),
        "서울특별시": ("서울",),
        "경기": ("경기도",),
        "경기도": ("경기",),
        "인천": ("인천광역시",),
        "인천광역시": ("인천",),
        "부산": ("부산광역시",),
        "부산광역시": ("부산",),
    }
    return any(compact(alias) in haystack for alias in aliases.get(needle, ()))


def list_post_data(region: str, page: int) -> dict[str, str]:
    return {
        "page": str(page),
        "seq": "",
        "itm_seq_1": "0",
        "multi_itm_seq": "0",
        "multi_itm_seqsStr": "1,2,4,8,16,32,64,128,256,512,1024",
        "isRecrnoti": "",
        "notType1": "0",
        "splyTy": "",
        "recrnotiState": "",
        "srchTp": "0",
        "srchWord": region,
    }


def parse_list_rows(document: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(document, "html.parser")
    rows: list[dict[str, str]] = []
    for tr in soup.select("#listTb tbody tr"):
        cells = tr.find_all("td")
        if len(cells) < 5:
            continue
        link = cells[1].find("a")
        if link is None:
            continue
        onclick = str(link.get("onclick", ""))
        seq_match = re.search(r"getDetailView\('([^']+)'\)", onclick)
        if not seq_match:
            continue
        title = normalize_space(link.get_text(" ", strip=True)).replace("NEW ", "").strip()
        rows.append(
            {
                "seq": seq_match.group(1),
                "title": title,
                "department": normalize_space(cells[2].get_text(" ", strip=True)),
                "notice_date": normalize_space(cells[3].get_text(" ", strip=True)),
                "views": normalize_space(cells[4].get_text(" ", strip=True)),
            }
        )
    return rows


def detail_post_data(seq: str) -> dict[str, str]:
    return {
        "page": "1",
        "seq": seq,
        "itm_seq_1": "0",
        "multi_itm_seq": "0",
        "multi_itm_seqsStr": "1,2,4,8,16,32,64,128,256,512,1024",
        "isRecrnoti": "",
    }


def detail_url(seq: str) -> str:
    return f"{DETAIL_URL}?seq={urllib.parse.quote(seq)}"


def parse_attachments(document: str) -> list[dict[str, str]]:
    match = re.search(r"initParam\.downList\s*=\s*(\[.*?\]);", document, flags=re.S)
    if not match:
        return []
    try:
        values = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []
    attachments: list[dict[str, str]] = []
    for item in values:
        if not isinstance(item, dict):
            continue
        params = {
            "brdId": str(item.get("brdId", "")),
            "seq": str(item.get("seq", "")),
            "fileTp": str(item.get("fileTp", "A")),
            "fileSeq": str(item.get("fileSeq", "")),
        }
        attachments.append(
            {
                "name": str(item.get("oriFileNm", "")),
                "brd_id": params["brdId"],
                "seq": params["seq"],
                "file_seq": params["fileSeq"],
                "file_tp": params["fileTp"],
                "download_url": DOWNLOAD_URL + "?" + urllib.parse.urlencode(params),
            }
        )
    return attachments


def extract_pdf_text(url: str) -> str:
    try:
        from pypdf import PdfReader
    except Exception:
        return ""
    try:
        reader = PdfReader(io.BytesIO(fetch_bytes(url)))
        texts = []
        for page in reader.pages[:12]:
            texts.append(page.extract_text() or "")
        return normalize_space("\n".join(texts))
    except Exception:
        return ""


def extract_hwpx_text(url: str) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(fetch_bytes(url))) as archive:
            names = archive.namelist()
            texts: list[str] = []
            if "Preview/PrvText.txt" in names:
                texts.append(archive.read("Preview/PrvText.txt").decode("utf-8", errors="ignore"))
            for name in names:
                lower_name = name.lower()
                if not lower_name.endswith(".xml"):
                    continue
                if not lower_name.startswith("contents/section"):
                    continue
                raw = archive.read(name).decode("utf-8", errors="ignore")
                text = re.sub(r"<[^>]+>", " ", raw)
                if any(keyword in text for keyword in ("접수", "신청", "모집", "공급")):
                    texts.append(text)
            return normalize_space("\n".join(texts))
    except Exception:
        return ""


def attachment_text(attachments: list[dict[str, str]]) -> str:
    texts: list[str] = []
    for item in attachments[:3]:
        name = item.get("name", "")
        lower_name = name.lower()
        if lower_name.endswith(".pdf"):
            text = extract_pdf_text(item.get("download_url", ""))
        elif lower_name.endswith(".hwpx"):
            text = extract_hwpx_text(item.get("download_url", ""))
        else:
            text = ""
        if text:
            texts.append(text)
    return normalize_space("\n".join(texts))


def parse_detail(seq: str) -> dict[str, Any]:
    document = fetch_html(DETAIL_URL, detail_post_data(seq))
    soup = BeautifulSoup(document, "html.parser")
    title = ""
    title_node = soup.select_one(".detailTable th, .gs0401Table th")
    if title_node:
        title = normalize_space(title_node.get_text(" ", strip=True))
    content_node = soup.select_one(".cont")
    body = normalize_space(content_node.get_text("\n", strip=True)) if content_node else ""
    full_text = normalize_space(soup.get_text("\n", strip=True))
    return {
        "document": document,
        "title": title,
        "body": body,
        "full_text": full_text,
        "attachments": parse_attachments(document),
    }


def parse_date(value: str, end_of_day: bool = False) -> datetime | None:
    match = re.search(r"(\d{2,4})\D{0,4}(\d{1,2})\D{0,4}(\d{1,2})", value)
    if not match:
        return None
    year = int(match.group(1))
    if year < 100:
        year += 2000
    hour = 23 if end_of_day else 0
    minute = 59 if end_of_day else 0
    time_match = re.search(r"(\d{1,2})\s*[:시]\s*(\d{2})?", value)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
    return datetime(year, int(match.group(2)), int(match.group(3)), hour, minute)


def parse_month_day(value: str, year: int, end_of_day: bool = False) -> datetime | None:
    match = re.search(r"(\d{1,2})\s*[.\-/월]\s*(\d{1,2})", value)
    if not match:
        return None
    hour = 23 if end_of_day else 0
    minute = 59 if end_of_day else 0
    return datetime(year, int(match.group(1)), int(match.group(2)), hour, minute)


def format_date(value: datetime, original: str = "") -> str:
    source = normalize_space(original)
    if source and re.search(r"\d{4}|\d{2}\s*[.\-/년]", source):
        return source
    return value.strftime("%Y.%m.%d")


def date_texts(value: str) -> list[str]:
    patterns = [
        r"(?<!\d)\d{4}\s*[.\-/년]\s*\d{1,2}\s*[.\-/월]\s*\d{1,2}\s*\.?\s*(?:일)?(?:\s*\(?[월화수목금토일]\)?)?(?:\s*\d{1,2}\s*[:시]\s*\d{0,2})?",
        r"(?<!\d)\d{2}\s*[.\-/년]\s*\d{1,2}\s*[.\-/월]\s*\d{1,2}\s*\.?\s*(?:일)?(?:\s*\(?[월화수목금토일]\)?)?(?:\s*\d{1,2}\s*[:시]\s*\d{0,2})?",
        r"(?<!\d)\d{4}\d{2}\d{2}",
    ]
    found: list[str] = []
    spans: list[tuple[int, int]] = []
    for pattern in patterns:
        for match in re.finditer(pattern, value):
            span = match.span()
            if any(not (span[1] <= used[0] or used[1] <= span[0]) for used in spans):
                continue
            spans.append(span)
            found.append(match.group(0))
    return found


def schedule_from_range_context(context: str) -> dict[str, str | bool] | None:
    range_patterns = [
        r"(?P<start>\d{2,4}\s*[.\-/년]\s*\d{1,2}\s*[.\-/월]\s*\d{1,2}\s*\.?\s*(?:일)?(?:\s*\([^)]+\))?)\s*[~∼\-–]\s*(?P<end>\d{2,4}\s*[.\-/년]\s*\d{1,2}\s*[.\-/월]\s*\d{1,2}\s*\.?\s*(?:일)?(?:\s*\([^)]+\))?)",
        r"(?P<start>\d{2,4}\s*[.\-/년]\s*\d{1,2}\s*[.\-/월]\s*\d{1,2}\s*\.?\s*(?:일)?(?:\s*\([^)]+\))?)\s*[~∼\-–]\s*(?P<end>\d{1,2}\s*[.\-/월]\s*\d{1,2}\s*\.?\s*(?:일)?(?:\s*\([^)]+\))?)",
    ]
    for pattern in range_patterns:
        match = re.search(pattern, context)
        if not match:
            continue
        start_text = match.group("start")
        end_text = match.group("end")
        start_at = parse_date(start_text)
        if not start_at:
            continue
        end_at = parse_date(end_text, end_of_day=True) or parse_month_day(end_text, start_at.year, end_of_day=True)
        if not end_at:
            continue
        now = datetime.now()
        if now < start_at:
            status = "접수예정"
        elif now <= end_at:
            status = "접수중"
        else:
            status = "접수마감"
        return {
            "status": status,
            "apply_start": format_date(start_at, start_text),
            "apply_end": format_date(end_at, end_text),
            "active": now <= end_at,
        }
    return None


def extract_apply_schedule(text: str) -> dict[str, str | bool]:
    keywords = ("신청접수", "접수기간", "신청기간", "청약접수", "접수", "신청", "청약")
    contexts: list[str] = []
    for keyword in keywords:
        for match in re.finditer(keyword, text):
            contexts.append(text[max(0, match.start() - 180) : match.end() + 240])
    for context in contexts:
        range_schedule = schedule_from_range_context(context)
        if range_schedule:
            return range_schedule
        dates = date_texts(context)
        if len(dates) < 2:
            continue
        start_text = dates[0]
        end_text = dates[1]
        start_at = parse_date(start_text)
        end_at = parse_date(end_text, end_of_day=True)
        if not start_at or not end_at:
            continue
        now = datetime.now()
        if now < start_at:
            status = "접수예정"
        elif now <= end_at:
            status = "접수중"
        else:
            status = "접수마감"
        return {
            "status": status,
            "apply_start": start_text.strip(),
            "apply_end": end_text.strip(),
            "active": now <= end_at,
        }
    return {"status": "일정확인필요", "apply_start": "", "apply_end": "", "active": False}


def number_after(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.I)
    return normalize_space(match.group(1)) if match else ""


def extract_metrics(text: str) -> dict[str, str]:
    patterns = {
        "공급호수": r"(?:공급호수|공급세대수|모집세대|모집호수)[^\d]{0,20}([\d,]+)",
        "신청건수": r"(?:신청건수|신청자수|접수건수|청약자수)[^\d]{0,20}([\d,]+)",
        "경쟁률": r"(?:경쟁률)[^\d]{0,20}([\d,.]+\s*:?\s*1?)",
        "임대보증금": r"(?:임대보증금|보증금)[^\d]{0,20}([\d,]+(?:\s*원)?)",
        "월임대료": r"(?:월임대료|월\s*임대료|임대료)[^\d]{0,20}([\d,]+(?:\s*원)?)",
        "전용면적": r"(?:전용면적|전용)[^\d]{0,20}([\d,.]+\s*(?:㎡|m2|m²)?)",
    }
    return {label: number_after(pattern, text) for label, pattern in patterns.items()}


def discover_sh_notices(region_names: list[str]) -> list[ShNoticeCandidate]:
    settings = sh_settings()
    max_pages = int(settings.get("max_search_pages", 3))
    include_status = set(settings.get("notice_filter", {}).get("include_status", ["접수예정", "접수중"]))
    candidates: list[ShNoticeCandidate] = []
    seen: set[str] = set()
    for region in [name.strip() for name in region_names if name.strip()]:
        for page in range(1, max_pages + 1):
            document = fetch_html(LIST_URL, list_post_data(region, page))
            rows = parse_list_rows(document)
            if not rows:
                break
            for row in rows:
                key = f"{region}:{row['seq']}"
                if key in seen:
                    continue
                seen.add(key)
                try:
                    detail = parse_detail(row["seq"])
                except Exception:
                    continue
                combined = " ".join(
                    [
                        row["title"],
                        str(detail.get("title", "")),
                        str(detail.get("body", "")),
                        " ".join(item.get("name", "") for item in detail.get("attachments", [])),
                    ]
                )
                attachment_body = attachment_text(detail.get("attachments", []))
                schedule = extract_apply_schedule(" ".join([str(detail.get("body", "")), attachment_body]))
                if schedule["status"] not in include_status or not schedule["active"]:
                    continue
                notice_region = region
                candidates.append(
                    ShNoticeCandidate(
                        id=key,
                        requested_region=region,
                        notice_region=notice_region,
                        title=row["title"],
                        seq=row["seq"],
                        department=row["department"],
                        notice_date=row["notice_date"],
                        views=row["views"],
                        status=str(schedule["status"]),
                        apply_start=str(schedule["apply_start"]),
                        apply_end=str(schedule["apply_end"]),
                        detail_url=detail_url(row["seq"]),
                    )
                )
                time.sleep(0.15)
    return sorted(candidates, key=lambda item: (item.apply_start, item.requested_region, item.title))


def record_for_notice(notice: dict[str, object]) -> dict[str, str]:
    seq = str(notice.get("seq", ""))
    detail = parse_detail(seq)
    attachments = detail.get("attachments", [])
    attachment_body = attachment_text(attachments)
    combined = " ".join(
        [
            str(notice.get("title", "")),
            str(detail.get("title", "")),
            str(detail.get("body", "")),
            attachment_body,
            " ".join(item.get("name", "") for item in attachments),
        ]
    )
    schedule = extract_apply_schedule(" ".join([str(detail.get("body", "")), attachment_body]))
    if not schedule["active"]:
        raise ValueError(f"SH {notice.get('title', '')} 공고는 현재 접수예정/접수중 일정이 아닙니다.")
    metrics = extract_metrics(combined)
    registry = load_metric_registry()
    registry.profile_record(metrics, "sh")
    attachment_names = " / ".join(item.get("name", "") for item in attachments)
    attachment_urls = " / ".join(item.get("download_url", "") for item in attachments)
    return {
        "기관": "SH",
        "요청지역": str(notice.get("requested_region", "")),
        "공고지역": str(notice.get("notice_region") or notice.get("requested_region", "")),
        "공고명": str(notice.get("title", "")),
        "게시글번호": seq,
        "담당부서": str(notice.get("department", "")),
        "등록일": str(notice.get("notice_date", "")),
        "조회수": str(notice.get("views", "")),
        "접수상태": str(schedule["status"]),
        "접수시작": str(schedule["apply_start"]),
        "접수마감": str(schedule["apply_end"]),
        "공급호수": metrics.get("공급호수", ""),
        "신청건수": metrics.get("신청건수", ""),
        "경쟁률": metrics.get("경쟁률", ""),
        "임대보증금": metrics.get("임대보증금", ""),
        "월임대료": metrics.get("월임대료", ""),
        "전용면적": metrics.get("전용면적", ""),
        "첨부파일": attachment_names,
        "첨부다운로드": attachment_urls,
        "상세URL": str(notice.get("detail_url") or detail_url(seq)),
        "본문요약": str(detail.get("body", ""))[:260],
    }


def write_csv(path: Path, records: list[dict[str, str]]) -> None:
    headers = [
        "기관",
        "요청지역",
        "공고지역",
        "공고명",
        "게시글번호",
        "담당부서",
        "등록일",
        "조회수",
        "접수상태",
        "접수시작",
        "접수마감",
        "공급호수",
        "신청건수",
        "경쟁률",
        "임대보증금",
        "월임대료",
        "전용면적",
        "첨부파일",
        "첨부다운로드",
        "상세URL",
        "본문요약",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def write_summary(path: Path, region: str, records: list[dict[str, str]]) -> None:
    lines = [
        f"# SH {region} 요약",
        "",
        f"- 생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 분석 공고 수: {len(records):,}건",
        "- 기준: 접수예정/접수중 일정이 확인된 공고만 포함",
        "",
        "## 공고 목록",
    ]
    for index, record in enumerate(records, start=1):
        lines.extend(
            [
                "",
                f"{index}. {record['공고명']}",
                f"   - 게시글번호: {record['게시글번호']}",
                f"   - 등록일: {record['등록일']}",
                f"   - 상태: {record['접수상태']}",
                f"   - 접수기간: {record['접수시작']} ~ {record['접수마감']}",
                f"   - 담당부서: {record['담당부서']}",
                f"   - 상세URL: {record['상세URL']}",
                f"   - 첨부파일: {record['첨부파일'] or '없음'}",
                f"   - 추출 지표: 공급호수 {record['공급호수'] or '-'}, 신청건수 {record['신청건수'] or '-'}, 경쟁률 {record['경쟁률'] or '-'}",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def collect_sh_notice_payloads(notices: list[dict[str, object]]) -> list[ShDirectRun]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for notice in notices:
        region = str(notice.get("requested_region", "")).strip()
        if not region:
            continue
        grouped.setdefault(region, []).append(notice)
    if not grouped:
        raise ValueError("분석할 SH 공고를 하나 이상 선택하세요.")

    runs: list[ShDirectRun] = []
    folder = output_folder()
    for region, region_notices in grouped.items():
        records = [record_for_notice(notice) for notice in region_notices]
        if not records:
            raise ValueError(f"SH {region} 지역은 현재 생성할 수 있는 결과가 없습니다.")
        stem = output_stem(region, records)
        data_path = folder / f"{stem}_분석데이터.csv"
        summary_path = folder / f"{stem}_요약.txt"
        write_csv(data_path, records)
        write_summary(summary_path, region, records)
        runs.append(
            ShDirectRun(
                region=region,
                rows=len(records),
                report=project_relative(summary_path),
                csv=project_relative(data_path),
                title=f"SH {region} 공고 분석",
            )
        )
    return runs
