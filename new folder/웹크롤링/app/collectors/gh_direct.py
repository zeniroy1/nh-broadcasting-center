from __future__ import annotations

import csv
import html
import re
import ssl
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from app.core.config import load_settings
from app.core.paths import project_root


BASE_URL = "https://apply.gh.or.kr"
LIST_PATH = "/sb/sr/sr7150/selectPbancRentHouseList.do"
DETAIL_PATH = "/sb/sr/sr7150/selectPbancDetailView.do"
COMPETITION_PATH = "/sb/sr/sr7150/selectGetCompete.do"

STATUS_LABELS = {
    "1": "공고중",
    "2": "접수중",
    "3": "접수마감",
}


@dataclass(frozen=True)
class GhRun:
    status: str
    phase: str
    rows: int
    data: str
    summary: str | None


def project_relative(path: Path) -> str:
    return path.resolve().relative_to(project_root().resolve()).as_posix()


def settings() -> dict[str, Any]:
    return load_settings().get("gh", {})


def output_folder() -> Path:
    folder = project_root() / settings().get("output_folder", "gh/outputs")
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def normalize_space(value: object) -> str:
    return re.sub(r"\s+", " ", html.unescape(str(value or ""))).strip()


def direct_text(node: Any) -> str:
    if node is None:
        return ""
    return normalize_space(" ".join(str(value) for value in node.find_all(string=True, recursive=False)))


def safe_filename_part(value: object, fallback: str = "공고") -> str:
    text = normalize_space(value)
    text = re.sub(r"[\\/:*?\"<>|]+", "_", text)
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"_+", "_", text).strip("._")
    return text[:44] or fallback


def short_notice_name(title: str) -> str:
    cleaned = re.sub(r"\([^)]*\)", " ", normalize_space(title))
    words = [word for word in re.split(r"\s+", cleaned) if word and word not in {"최초", "추가"}]
    return safe_filename_part(words[0] if words else title)


def notice_stem(notice: dict[str, str], suffix: str) -> str:
    return f"gh_{safe_filename_part(notice.get('pbanc_no'), '번호')}_{short_notice_name(notice.get('title', ''))}_{suffix}"


def cleanup_output_folder() -> None:
    if not settings().get("clear_output_before_run", True):
        return
    for path in output_folder().glob("gh_*.csv"):
        path.unlink(missing_ok=True)
    for path in output_folder().glob("gh_*.txt"):
        path.unlink(missing_ok=True)


def post_html(path: str, data: dict[str, str]) -> str:
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    request = urllib.request.Request(
        BASE_URL + path,
        data=encoded,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "ko-KR,ko;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    context = ssl.create_default_context()
    try:
        context.set_ciphers("DEFAULT:@SECLEVEL=1")
    except ssl.SSLError:
        pass
    raw = urllib.request.urlopen(request, timeout=45, context=context).read()
    return raw.decode("utf-8", errors="replace")


def list_post_data(status_code: str, page: int, keyword: str = "") -> dict[str, str]:
    return {
        "searchArea": "",
        "searchCate": "",
        "searchState": status_code,
        "searchTitle": keyword,
        "previewYn": "",
        "pbancNo": "",
        "pbancKndCd": "",
        "bizTyNm": "",
        "pageIndex": str(page),
    }


def detail_post_data(notice: dict[str, str]) -> dict[str, str]:
    return {
        "searchArea": "",
        "searchCate": "",
        "searchState": notice.get("status_code", ""),
        "searchTitle": "",
        "previewYn": notice.get("preview_yn", "N"),
        "pbancNo": notice["pbanc_no"],
        "pbancKndCd": notice.get("pbanc_knd_cd", "01"),
        "bizTyNm": notice.get("type", ""),
        "pageIndex": notice.get("page", "1"),
    }


def total_pages(document: str) -> int:
    text = normalize_space(BeautifulSoup(document, "html.parser").get_text(" ", strip=True))
    match = re.search(r"페이지\s*:\s*\d+\s*/\s*(\d+)", text)
    return int(match.group(1)) if match else 1


def parse_list_rows(document: str, status_code: str, page: int) -> list[dict[str, str]]:
    soup = BeautifulSoup(document, "html.parser")
    rows: list[dict[str, str]] = []
    for tr in soup.select(".board_tbl tbody tr"):
        cells = tr.find_all("td")
        if len(cells) < 10:
            continue
        link = cells[2].find("a")
        if link is None:
            continue
        pbanc_no = str(link.get("data-pbancno") or link.get("data-pbancNo") or "")
        if not pbanc_no:
            continue
        comp_button = cells[8].find("button")
        rows.append(
            {
                "id": f"{status_code}:{pbanc_no}",
                "status_code": status_code,
                "status": STATUS_LABELS.get(status_code, normalize_space(cells[7].get_text(" ", strip=True))),
                "phase": phase_for_status_code(status_code),
                "number": normalize_space(cells[0].get_text(" ", strip=True)),
                "type": direct_text(cells[1]),
                "title": normalize_space(link.get_text(" ", strip=True)),
                "region": direct_text(cells[3]),
                "posted_at": direct_text(cells[5]),
                "close_at": direct_text(cells[6]),
                "competition_state": normalize_space(comp_button.get_text(" ", strip=True)) if comp_button else direct_text(cells[8]),
                "views": direct_text(cells[9]),
                "pbanc_no": pbanc_no,
                "pbanc_knd_cd": str(link.get("data-pbanckndcd") or link.get("data-pbancKndCd") or "01"),
                "preview_yn": str(link.get("data-previewyn") or link.get("data-previewYn") or "N"),
                "biz_ty_cd": str(comp_button.get("data-biztycd") or comp_button.get("data-bizTyCd") or "") if comp_button else "",
                "page": str(page),
            }
        )
    return rows


def phase_for_status_code(status_code: str) -> str:
    if status_code == "1":
        return "공고전"
    if status_code == "2":
        return "접수기간"
    if status_code == "3":
        return "접수마감"
    return "기타"


def parse_ymd(value: str) -> date | None:
    match = re.search(r"(\d{4})\D+(\d{1,2})\D+(\d{1,2})", value)
    if not match:
        return None
    try:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


def is_recent_closed_notice(notice: dict[str, str]) -> bool:
    closed_at = parse_ymd(notice.get("close_at", ""))
    if closed_at is None:
        return False
    today = date.today()
    recent_days = int(settings().get("closed_recent_days", 14))
    return closed_at <= today and (today - closed_at).days <= recent_days


def fetch_notices(status_code: str, keyword: str = "") -> list[dict[str, str]]:
    first = post_html(LIST_PATH, list_post_data(status_code, 1, keyword))
    max_pages = int(settings().get("max_pages", 25))
    pages = min(total_pages(first), max_pages)
    notices = parse_list_rows(first, status_code, 1)
    for page in range(2, pages + 1):
        notices.extend(parse_list_rows(post_html(LIST_PATH, list_post_data(status_code, page, keyword)), status_code, page))
        time.sleep(0.08)
    return notices


def parse_key_value_tables(document: str) -> dict[str, str]:
    soup = BeautifulSoup(document, "html.parser")
    values: dict[str, str] = {}
    for tr in soup.find_all("tr"):
        headers = tr.find_all("th")
        cells = tr.find_all("td")
        for index, header in enumerate(headers):
            if index >= len(cells):
                continue
            key = normalize_space(header.get_text(" ", strip=True))
            value = normalize_space(cells[index].get_text(" ", strip=True))
            if key and value:
                values[key] = value
    return values


def parse_attachments(document: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(document, "html.parser")
    attachments: list[dict[str, str]] = []
    for link in soup.select('a[href*="selectFileDown.do"]'):
        href = str(link.get("href", ""))
        name = normalize_space(link.get_text(" ", strip=True))
        attachments.append({"name": name, "url": urllib.parse.urljoin(BASE_URL, href)})
    return attachments


def parse_schedule(document: str) -> dict[str, str]:
    soup = BeautifulSoup(document, "html.parser")
    schedules: dict[str, str] = {}
    title_nodes = soup.find_all(["h5", "h4", "h3"])
    for title_node in title_nodes:
        if "공급일정" not in normalize_space(title_node.get_text(" ", strip=True)):
            continue
        cursor = title_node.find_next_sibling()
        while cursor is not None and cursor.name not in {"h5", "h4", "h3"}:
            for li in cursor.find_all("li") if hasattr(cursor, "find_all") else []:
                text = normalize_space(li.get_text(" ", strip=True))
                if ":" in text:
                    key, value = text.split(":", 1)
                    schedules[normalize_space(key)] = normalize_space(value)
            cursor = cursor.find_next_sibling()
        break
    return schedules


def parse_detail(notice: dict[str, str]) -> dict[str, Any]:
    document = post_html(DETAIL_PATH, detail_post_data(notice))
    values = parse_key_value_tables(document)
    attachments = parse_attachments(document)
    schedules = parse_schedule(document)
    return {
        "values": values,
        "attachments": attachments,
        "schedules": schedules,
        "detail_url": BASE_URL + DETAIL_PATH,
    }


def parse_count(value: object) -> int:
    match = re.search(r"-?[\d,]+", normalize_space(value))
    return int(match.group(0).replace(",", "")) if match else 0


def parse_ratio(value: object) -> float:
    match = re.search(r"([\d,.]+)\s*(?::|대)", normalize_space(value))
    if not match:
        return 0.0
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return 0.0


def format_ratio(value: float) -> str:
    return f"{value:.2f}:1"


def format_probability(supply: int, applications: int) -> str:
    probability = supply / applications if applications else 1.0
    return f"{probability * 100:.2f}%"


def expand_html_table(table: Any) -> list[dict[str, str]]:
    header_row = table.select_one("thead tr")
    if header_row is None:
        return []
    headers = [normalize_space(cell.get_text(" ", strip=True)) for cell in header_row.find_all(["th", "td"], recursive=False)]
    active_spans: dict[int, tuple[int, str]] = {}
    rows: list[dict[str, str]] = []
    for tr in table.select("tbody > tr"):
        values = [""] * len(headers)
        for column, (remaining, value) in list(active_spans.items()):
            values[column] = value
            if remaining <= 1:
                del active_spans[column]
            else:
                active_spans[column] = (remaining - 1, value)

        column = 0
        for cell in tr.find_all(["th", "td"], recursive=False):
            while column < len(headers) and values[column]:
                column += 1
            if column >= len(headers):
                break
            value = normalize_space(cell.get_text(" ", strip=True))
            colspan = max(1, int(cell.get("colspan", 1)))
            rowspan = max(1, int(cell.get("rowspan", 1)))
            for offset in range(colspan):
                target = column + offset
                if target >= len(headers):
                    break
                values[target] = value
                if rowspan > 1:
                    active_spans[target] = (rowspan - 1, value)
            column += colspan
        if any(values):
            rows.append(dict(zip(headers, values)))
    return rows


def parse_competition_rows(notice: dict[str, str]) -> list[dict[str, str]]:
    biz_ty_cd = notice.get("biz_ty_cd", "")
    if not biz_ty_cd:
        return []
    document = post_html(COMPETITION_PATH, {"pbancNo": notice["pbanc_no"], "bizTyCd": biz_ty_cd})
    soup = BeautifulSoup(document, "html.parser")
    rows: list[dict[str, str]] = []
    title_node = soup.select_one(".subcont_title")
    competition_title = normalize_space(title_node.get_text(" ", strip=True)) if title_node else notice["title"]
    table = soup.find("table")
    if table is None:
        return []
    collected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data_kind = "실시간 경쟁률" if notice.get("status_code") in {"1", "2"} else "최종 경쟁률"
    for raw in expand_html_table(table):
        supply = parse_count(raw.get("모집호수", ""))
        applications = parse_count(raw.get("청약접수", ""))
        official_ratio = normalize_space(raw.get("경쟁률", ""))
        calculated_ratio = applications / supply if supply else parse_ratio(official_ratio)
        row = {
            "기관": "GH",
            "데이터구분": data_kind,
            "수집시각": collected_at,
            "상태": notice["status"],
            "시기구분": notice["phase"],
            "공고번호": notice["pbanc_no"],
            "공고명": notice["title"],
            "경쟁률공고명": competition_title,
            "지역": notice["region"],
            "유형": notice["type"],
            "게시일": notice["posted_at"],
            "마감일": notice["close_at"],
            "지역명": notice["region"],
            "주택정보": notice["title"],
            "주택형": raw.get("주택유형", ""),
            "공급유형": raw.get("공급유형", ""),
            "공급대상": raw.get("공급대상", ""),
            "청약상태": notice["status"],
            "접수기간": notice.get("apply_period", ""),
            "공급호수(당첨자)": supply,
            "모집인원(예비자)": "미제공",
            "신청건수": applications,
            "당첨 경쟁률": official_ratio or format_ratio(calculated_ratio),
            "당첨확률(단순)": format_probability(supply, applications),
        }
        rows.append(row)
    return rows


def schedule_record(notice: dict[str, str]) -> dict[str, str]:
    detail = parse_detail(notice)
    schedules = detail["schedules"]
    attachments = detail["attachments"]
    values = detail["values"]
    return {
        "기관": "GH",
        "상태": notice["status"],
        "시기구분": notice["phase"],
        "공고번호": notice["pbanc_no"],
        "공고명": notice["title"],
        "지역": notice["region"],
        "유형": notice["type"],
        "게시일": notice["posted_at"],
        "마감일": notice["close_at"],
        "조회수": notice["views"],
        "공고상태": values.get("공고상태", notice["status"]),
        "공고일": values.get("공고일", notice["posted_at"]),
        "온라인접수기간": schedules.get("온라인접수기간", ""),
        "현장접수기간": schedules.get("현장접수기간", ""),
        "서류제출대상자 발표일": schedules.get("서류제출대상자 발표일", ""),
        "서류제출기간": schedules.get("서류제출기간", ""),
        "당첨자발표일": schedules.get("당첨자발표일", ""),
        "계약기간": schedules.get("계약기간", ""),
        "첨부파일": " / ".join(item["name"] for item in attachments),
        "첨부링크": " / ".join(item["url"] for item in attachments),
    }


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    headers: list[str] = []
    for row in rows:
        for key in row:
            if key not in headers:
                headers.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: Path, title: str, rows: list[dict[str, str]]) -> None:
    lines = [
        f"# {title}",
        "",
        f"- 생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 건수: {len(rows):,}건",
        "",
        "## 목록",
    ]
    for index, row in enumerate(rows[:40], start=1):
        lines.append(f"{index}. [{row.get('상태', '')}] {row.get('공고번호', '')} {row.get('공고명', '')} ({row.get('지역', '')})")
    if len(rows) > 40:
        lines.append(f"... 외 {len(rows) - 40:,}건")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def competition_table(rows: list[dict[str, str]]) -> list[str]:
    lines = [
        "| 주택형 | 공급유형 | 공급대상 | 공급호수 | 신청건수 | 경쟁률 | 단순 당첨확률 |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        cells = [
            row.get("주택형", ""),
            row.get("공급유형", ""),
            row.get("공급대상", ""),
            f"{parse_count(row.get('공급호수(당첨자)', 0)):,}",
            f"{parse_count(row.get('신청건수', 0)):,}",
            row.get("당첨 경쟁률", ""),
            row.get("당첨확률(단순)", ""),
        ]
        lines.append("| " + " | ".join(str(value).replace("|", "/") for value in cells) + " |")
    return lines


def general_supply_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if re.sub(r"\s+", "", row.get("공급유형", "")) == "일반공급"]


def notice_count(rows: list[dict[str, str]]) -> int:
    return len({str(row.get("공고번호", "")).strip() for row in rows if str(row.get("공고번호", "")).strip()})


def write_competition_summary(path: Path, title: str, rows: list[dict[str, str]]) -> None:
    total_supply = sum(parse_count(row.get("공급호수(당첨자)", 0)) for row in rows)
    total_applications = sum(parse_count(row.get("신청건수", 0)) for row in rows)
    overall_ratio = total_applications / total_supply if total_supply else 0.0
    ranked = sorted(rows, key=lambda row: (parse_ratio(row.get("당첨 경쟁률", "")), parse_count(row.get("신청건수", 0))), reverse=True)
    low_ranked = sorted(rows, key=lambda row: (parse_ratio(row.get("당첨 경쟁률", "")), parse_count(row.get("신청건수", 0))))
    general_rows = general_supply_rows(rows)
    general_ranked = sorted(general_rows, key=lambda row: (parse_ratio(row.get("당첨 경쟁률", "")), parse_count(row.get("신청건수", 0))), reverse=True)
    general_supply = sum(parse_count(row.get("공급호수(당첨자)", 0)) for row in general_rows)
    general_applications = sum(parse_count(row.get("신청건수", 0)) for row in general_rows)
    general_ratio = general_applications / general_supply if general_supply else 0.0
    sample = rows[0] if rows else {}
    lines = [
        f"# {title}",
        "",
        f"- 데이터 구분: {sample.get('데이터구분', '')}",
        f"- 공고명: {sample.get('공고명', '')}",
        f"- 청약상태: {sample.get('청약상태', '')}",
        f"- 접수기간: {sample.get('접수기간', '') or '확인 필요'}",
        f"- 생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 전체 요약",
        "",
        f"- 분석 주택형/공급대상 수: {len(rows):,}개",
        f"- 공급호수 합계: {total_supply:,}호",
        f"- 신청건수 합계: {total_applications:,}건",
        f"- 전체 경쟁률: {format_ratio(overall_ratio)}",
        "- 단순 당첨확률은 공급호수 / 신청건수의 산술값이며 자격심사, 중복신청, 부적격 및 포기는 반영하지 않습니다.",
        "",
        "## 경쟁이 치열한 항목 TOP 3",
        "",
        *competition_table(ranked[:3]),
        "",
        "## 신청 대비 당첨확률이 높은 항목 TOP 3",
        "",
        *competition_table(low_ranked[:3]),
        "",
        "## 일반공급 경쟁률",
        "",
        f"- 일반공급 항목 수: {len(general_rows):,}개",
        f"- 일반공급 공급호수 합계: {general_supply:,}호",
        f"- 일반공급 신청건수 합계: {general_applications:,}건",
        f"- 일반공급 전체 경쟁률: {format_ratio(general_ratio)}",
        "",
        *competition_table(general_ranked),
        "",
        "## 전체 경쟁률",
        "",
        *competition_table(ranked),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def write_notice_csv(row_or_rows: dict[str, str] | list[dict[str, str]], notice: dict[str, str], suffix: str) -> Path:
    rows = row_or_rows if isinstance(row_or_rows, list) else [row_or_rows]
    path = output_folder() / f"{notice_stem(notice, suffix)}.csv"
    write_csv(path, rows)
    return path


def write_notice_competition_summary(rows: list[dict[str, str]], notice: dict[str, str], suffix: str) -> Path:
    path = output_folder() / f"{notice_stem(notice, suffix)}.txt"
    scope = "일반공급 경쟁률 요약" if "일반공급" in suffix else "경쟁률 요약"
    write_competition_summary(path, f"GH {notice.get('title', '')} {scope}", rows)
    return path


def collect_gh(keyword: str = "") -> list[GhRun]:
    folder = output_folder()
    cleanup_output_folder()
    runs: list[GhRun] = []

    schedule_statuses = ("1", "2")
    for status_code in schedule_statuses:
        notices = fetch_notices(status_code, keyword)
        rows: list[dict[str, str]] = []
        live_competition_rows: list[dict[str, str]] = []
        for notice in notices:
            record = schedule_record(notice)
            rows.append(record)
            write_notice_csv(record, notice, "일정데이터")
            competition_notice = dict(notice)
            competition_notice["apply_period"] = record.get("온라인접수기간") or record.get("현장접수기간") or ""
            competition_rows = parse_competition_rows(competition_notice)
            if competition_rows:
                live_competition_rows.extend(competition_rows)
                write_notice_csv(competition_rows, notice, "실시간경쟁률데이터")
                write_notice_competition_summary(competition_rows, notice, "실시간경쟁률요약")
                general_rows = general_supply_rows(competition_rows)
                if general_rows:
                    write_notice_csv(general_rows, notice, "일반공급경쟁률데이터")
                    write_notice_competition_summary(general_rows, notice, "일반공급경쟁률요약")
            time.sleep(0.08)
        if rows:
            status = STATUS_LABELS[status_code]
            phase = phase_for_status_code(status_code)
            data_path = folder / f"gh_{phase}_일정데이터.csv"
            summary_path = folder / f"gh_{phase}_요약.txt"
            write_csv(data_path, rows)
            write_summary(summary_path, f"GH {phase} 일정 요약", rows)
            runs.append(GhRun(status=status, phase=phase, rows=len(rows), data=project_relative(data_path), summary=project_relative(summary_path)))
        if notice_count(live_competition_rows) >= 2:
            status = STATUS_LABELS[status_code]
            phase = phase_for_status_code(status_code)
            data_path = folder / f"gh_{phase}_실시간경쟁률데이터.csv"
            summary_path = folder / f"gh_{phase}_실시간경쟁률요약.txt"
            write_csv(data_path, live_competition_rows)
            write_competition_summary(summary_path, f"GH {phase} 실시간 경쟁률 요약", live_competition_rows)
            runs.append(
                GhRun(
                    status=status,
                    phase=f"{phase} 실시간경쟁률",
                    rows=len(live_competition_rows),
                    data=project_relative(data_path),
                    summary=project_relative(summary_path),
                )
            )
            general_rows = general_supply_rows(live_competition_rows)
            if general_rows:
                general_data_path = folder / f"gh_{phase}_일반공급경쟁률데이터.csv"
                general_summary_path = folder / f"gh_{phase}_일반공급경쟁률요약.txt"
                write_csv(general_data_path, general_rows)
                write_competition_summary(general_summary_path, f"GH {phase} 일반공급 경쟁률 요약", general_rows)
                runs.append(
                    GhRun(
                        status=status,
                        phase=f"{phase} 일반공급",
                        rows=len(general_rows),
                        data=project_relative(general_data_path),
                        summary=project_relative(general_summary_path),
                    )
                )

    closed_notices = [notice for notice in fetch_notices("3", keyword) if is_recent_closed_notice(notice)]
    competition_rows: list[dict[str, str]] = []
    for notice in closed_notices:
        rows = parse_competition_rows(notice)
        if not rows:
            continue
        competition_rows.extend(rows)
        write_notice_csv(rows, notice, "경쟁률데이터")
        write_notice_competition_summary(rows, notice, "경쟁률요약")
        general_rows = general_supply_rows(rows)
        if general_rows:
            write_notice_csv(general_rows, notice, "일반공급경쟁률데이터")
            write_notice_competition_summary(general_rows, notice, "일반공급경쟁률요약")
        time.sleep(0.08)
    if notice_count(competition_rows) >= 2:
        data_path = folder / "gh_접수마감_경쟁률데이터.csv"
        summary_path = folder / "gh_접수마감_경쟁률요약.txt"
        write_csv(data_path, competition_rows)
        write_competition_summary(summary_path, "GH 접수마감 최종 경쟁률 요약", competition_rows)
        runs.append(
            GhRun(
                status="접수마감",
                phase="접수마감",
                rows=len(competition_rows),
                data=project_relative(data_path),
                summary=project_relative(summary_path),
            )
        )
        general_rows = general_supply_rows(competition_rows)
        if general_rows:
            general_data_path = folder / "gh_접수마감_일반공급경쟁률데이터.csv"
            general_summary_path = folder / "gh_접수마감_일반공급경쟁률요약.txt"
            write_csv(general_data_path, general_rows)
            write_competition_summary(general_summary_path, "GH 접수마감 일반공급 최종 경쟁률 요약", general_rows)
            runs.append(
                GhRun(
                    status="접수마감",
                    phase="접수마감 일반공급",
                    rows=len(general_rows),
                    data=project_relative(general_data_path),
                    summary=project_relative(general_summary_path),
                )
            )
    return runs
