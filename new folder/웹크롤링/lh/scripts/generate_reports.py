from io import StringIO
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from datetime import datetime
import html as html_lib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import warnings

import pandas as pd


BASE = Path(__file__).resolve().parents[1]
INPUT_DIR = BASE / "inputs"
OUTPUT_DIR = BASE / "outputs"
PROJECT_ROOT = BASE.parent
TARGET_LAT = 37.56577
TARGET_LON = 126.96665

LEGACY_REPORTS = {
    "서울": {
        "pan_id": "2015122300019992",
        "title": "[서울지역본부] 26년 1차 비분양전환형 든든전세주택 입주자 모집공고",
        "ais_tp_cd": "26",
        "ccr_cnnt_sys_ds_cd": "03",
        "upp_ais_tp_cd": "13",
    },
    "경기북부": {
        "pan_id": "2015122300019989",
        "title": "[경기북부] 26년 1차 비분양전환형 든든전세주택 입주자 모집공고",
        "ais_tp_cd": "26",
        "ccr_cnnt_sys_ds_cd": "03",
        "upp_ais_tp_cd": "13",
    },
    "경기남부": {
        "pan_id": "2015122300019891",
        "title": "[경기남부] 2026년 든든전세 매입임대주택 예비입주자 모집공고",
        "ais_tp_cd": "26",
        "ccr_cnnt_sys_ds_cd": "03",
        "upp_ais_tp_cd": "13",
    },
}

LEGACY_REPORT_ALIASES = {
    "서울": ("서울", "서울지역본부"),
    "경기북부": ("경기북부",),
    "경기남부": ("경기남부",),
}

REGION_SUFFIX_RE = re.compile(r"(?:지역본부|본부|광역시|특별시|특별자치시|특별자치도|도|시)$")
NON_REGION_WORDS = {"당첨자", "당점자", "예비자", "신청자", "공급호수", "모집인원", "주택형", "바로보기", "다운로드"}
BROAD_REGION_PREFIXES = ("경기북부", "경기남부", "부산울산", "서울", "경기", "인천", "부산", "울산", "대구", "광주", "대전", "세종", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주")


def compact_text(text):
    return re.sub(r"\s+", "", str(text or ""))


def clean_space(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def strip_tags(value):
    value = re.sub(r"<script.*?</script>", " ", value, flags=re.S | re.I)
    value = re.sub(r"<style.*?</style>", " ", value, flags=re.S | re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html_lib.unescape(value)
    value = re.sub(r"\b\d+일전\b", " ", value)
    return clean_space(value)


def normalize_region_candidate(value):
    value = REGION_SUFFIX_RE.sub("", clean_space(value))
    value = re.sub(r"[^가-힣]", "", value)
    for prefix in BROAD_REGION_PREFIXES:
        if value.startswith(prefix):
            return prefix
    return value


def key_from_text(text):
    compact = compact_text(text)
    for key, aliases in LEGACY_REPORT_ALIASES.items():
        if any(alias in compact for alias in aliases):
            return key
    return ""


def extract_title_hint(text):
    lines = [clean_space(line) for line in str(text or "").splitlines()]
    candidates = []
    for line in lines:
        compact = compact_text(line)
        if "든든전세" in compact and ("공고" in compact or "입주자" in compact or "모집" in compact):
            candidates.append(line)
    if candidates:
        return max(candidates, key=len)

    compact = compact_text(text)
    match = re.search(r"(.{0,30}든든전세.{0,45}(?:공고|모집))", compact)
    return match.group(1) if match else ""


def extract_region_hint(text, title_hint=""):
    evidence = "\n".join(part for part in (title_hint, str(text or "")) if part)
    compact_evidence = compact_text(evidence)
    for pattern in (r"모집지역[:：]?([가-힣]{2,12})", r"공고([가-힣]{2,12})\)"):
        match = re.search(pattern, compact_evidence)
        if match:
            value = normalize_region_candidate(match.group(1))
            if value and value not in NON_REGION_WORDS:
                return value

    for pattern in (r"\[([^\]]{1,20})\]", r"\(([^)]{1,20})\)"):
        for match in re.finditer(pattern, evidence):
            value = normalize_region_candidate(match.group(1))
            if value and value not in NON_REGION_WORDS and not re.search(r"\d|차|공고|모집|주택|전세", value):
                return value

    compact = compact_text(title_hint or text)
    match = re.search(r"\d+년\d*차?([가-힣]{2,12})(?:비분양|든든전세|매입임대)", compact)
    if match:
        value = normalize_region_candidate(match.group(1))
        if value and value not in NON_REGION_WORDS:
            return value
    return key_from_text(evidence)


def safe_filename(value, fallback="lh_report"):
    value = clean_space(value) or fallback
    value = re.sub(r'[\\/:*?"<>|]+', "_", value)
    value = re.sub(r"\s+", "_", value).strip("._ ")
    return (value or fallback)[:90]


def read_image_text(path):
    warnings.filterwarnings("ignore", message=".*pin_memory.*", category=UserWarning)
    try:
        import cv2
        import easyocr
        import numpy as np
    except Exception:
        return ""
    try:
        raw = np.fromfile(str(path), dtype=np.uint8)
        image = cv2.imdecode(raw, cv2.IMREAD_COLOR)
        if image is None:
            return ""
        height = image.shape[0]
        crop = image[: min(height, 2400), :]
        reader = easyocr.Reader(["ko", "en"], gpu=False, verbose=False)
        texts = reader.readtext(crop, detail=0, paragraph=True)
        return "\n".join(str(item) for item in texts)
    except Exception:
        return ""


def manifest_entry(path):
    manifest = path.parent / "_detected_regions.json"
    if not manifest.exists():
        return {}
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception:
        return {}
    value = data.get(path.name, {})
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value:
        return {"legacy_key": value, "region_hint": value, "detected_by": "이전 감지 JSON"}
    return {}


def image_entry(path):
    text = read_image_text(path)
    title_hint = extract_title_hint(text)
    return {
        "image_text": text,
        "title_hint": title_hint,
        "region_hint": extract_region_hint(text, title_hint),
        "legacy_key": key_from_text("\n".join([title_hint, text, path.stem])),
        "detected_by": "PNG 내부 공고 문구 OCR",
    }

ACCESS_RULES = [
    ("고양시 백석동(네스트168)", "백석역 / 3호선", "백석역 -> 종로3가 -> 서대문", "약 45~50분", "약 50~60분"),
    ("고양시 대화동(계림웨스트벨리)", "대화역 / 3호선", "대화역 -> 종로3가 -> 서대문", "약 55~65분", "약 65~75분"),
    ("도봉창동(미래하이츠)", "쌍문역 / 4호선", "쌍문역 -> 동대문 -> 서대문", "약 35~40분", "약 45~55분"),
    ("노원상계동(시온빌리지)", "수락산역 / 7호선", "수락산역 -> 군자 -> 서대문", "약 50~60분", "약 60~70분"),
    ("동대문제기동(새울센스빌)", "제기동역 / 1호선", "제기동역 -> 종로3가 -> 서대문", "약 20~25분", "약 30~40분"),
    ("은평신사동(승윤노블리안)", "새절역 / 6호선", "새절역 -> 공덕 -> 서대문", "약 25~35분", "약 35~45분"),
    ("은평역촌동(예그리나8차)", "응암역 / 6호선", "응암역 -> 공덕 -> 서대문", "약 30~40분", "약 40~50분"),
]


def fetch_text(url, data=None):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancInfo.do",
    }
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
    req = urllib.request.Request(url, data=data, headers=headers)
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", errors="replace")


def clean_text(value):
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def num(value):
    if pd.isna(value):
        return 0
    match = re.search(r"-?\d+(?:\.\d+)?", str(value).replace(",", "").strip())
    return int(float(match.group())) if match else 0


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0


def fmt_ratio(value):
    return f"{value:,.2f}:1"


def fmt_pct(value):
    return f"{value * 100:.2f}%"


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0088
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * radius * asin(sqrt(a))


def parse_map_args(call):
    return re.findall(r"'([^']*)'", call)



def attr_value(tag, name):
    match = re.search(rf'{name}=["\']([^"\']*)["\']', tag)
    return html_lib.unescape(match.group(1)) if match else ""


def search_lh_notices(keyword):
    keyword = clean_space(keyword)
    url = "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancList.do?mi=1026&panNm=" + urllib.parse.quote(keyword)
    html = fetch_text(url)
    notices = []
    pattern = re.compile(r'<a\b[^>]*class=["\'][^"\']*wrtancInfoBtn[^"\']*["\'][^>]*>.*?</a>', re.S | re.I)
    for match in pattern.finditer(html):
        tag = match.group(0)
        pan_id = attr_value(tag, "data-id1")
        if not pan_id:
            continue
        row_end = html.find("</tr>", match.end())
        row_tail = html[match.end() : row_end if row_end != -1 else match.end() + 3000]
        region = ""
        region_match = re.search(r'<td\b[^>]*class=["\'][^"\']*(?:cate|col2)[^"\']*["\'][^>]*>(.*?)</td>', row_tail, re.S | re.I)
        if region_match:
            region = strip_tags(region_match.group(1))
        notices.append(
            {
                "pan_id": pan_id,
                "ccr_cnnt_sys_ds_cd": attr_value(tag, "data-id2") or "03",
                "upp_ais_tp_cd": attr_value(tag, "data-id3") or "13",
                "ais_tp_cd": attr_value(tag, "data-id4") or "26",
                "title": strip_tags(tag),
                "region": region,
            }
        )
    return notices


def search_queries(entry, png):
    queries = []
    for value in (entry.get("title_hint"), entry.get("region_hint"), png.stem):
        value = clean_space(value)
        if value and value not in queries:
            queries.append(value)
    if entry.get("region_hint"):
        region_query = clean_space(f"{entry.get('region_hint')} 든든전세")
        if region_query not in queries:
            queries.append(region_query)
    for value in ("든든전세", "비분양전환형 든든전세"):
        if value not in queries:
            queries.append(value)
    return queries


def score_notice(notice, entry, png):
    evidence = compact_text("\n".join(
        str(part or "")
        for part in (
            entry.get("title_hint"),
            entry.get("region_hint"),
            entry.get("image_text"),
            entry.get("legacy_key"),
            png.stem,
        )
    ))
    title = compact_text(notice.get("title"))
    region = compact_text(notice.get("region"))
    score = 0
    if title and (title in evidence or evidence in title):
        score += 80
    if region and region in evidence:
        score += 40
    hint_region = compact_text(entry.get("region_hint"))
    if hint_region and (hint_region in title or hint_region in region):
        score += 35
    legacy_key = compact_text(entry.get("legacy_key"))
    if legacy_key and (legacy_key in title or legacy_key in region):
        score += 30

    title_tokens = set(re.findall(r"[가-힣A-Za-z0-9]{2,}", notice.get("title", "")))
    evidence_tokens = set(re.findall(r"[가-힣A-Za-z0-9]{2,}", " ".join(
        str(part or "") for part in (entry.get("title_hint"), entry.get("image_text"), png.stem)
    )))
    score += min(len(title_tokens & evidence_tokens) * 5, 45)
    if "든든전세" in title:
        score += 10
    if "비분양전환형" in title:
        score += 5
    return score


def notice_to_meta(png, notice, detected_by):
    display_key = extract_region_hint(notice.get("title", ""), notice.get("title", ""))
    if not display_key:
        display_key = notice.get("region") or notice.get("title") or png.stem
    output_stem = safe_filename(f"{display_key}_{png.stem}")
    return {
        "key": display_key,
        "png": png.name,
        "detected_by": detected_by,
        "pan_id": notice["pan_id"],
        "ais_tp_cd": notice.get("ais_tp_cd", "26"),
        "ccr_cnnt_sys_ds_cd": notice.get("ccr_cnnt_sys_ds_cd", "03"),
        "upp_ais_tp_cd": notice.get("upp_ais_tp_cd", "13"),
        "title": notice.get("title", ""),
        "out": f"{output_stem}_경쟁률_보고서.txt",
        "csv": f"{output_stem}_경쟁률_전체데이터.csv",
        "dist_csv": f"{output_stem}_경쟁률_거리_전체데이터.csv",
    }


def legacy_notice_from_key(key):
    info = LEGACY_REPORTS.get(key)
    if not info:
        return None
    return {
        "pan_id": info["pan_id"],
        "ais_tp_cd": info.get("ais_tp_cd", "26"),
        "ccr_cnnt_sys_ds_cd": info.get("ccr_cnnt_sys_ds_cd", "03"),
        "upp_ais_tp_cd": info.get("upp_ais_tp_cd", "13"),
        "title": info["title"],
        "region": key,
    }


def resolve_notice_for_png(png):
    entry = manifest_entry(png)
    if not entry or not any(entry.get(key) for key in ("title_hint", "region_hint", "image_text", "legacy_key")):
        entry = image_entry(png)
    if not entry.get("legacy_key"):
        entry["legacy_key"] = key_from_text("\n".join([entry.get("title_hint", ""), entry.get("image_text", ""), png.stem]))
    if not entry.get("region_hint"):
        entry["region_hint"] = extract_region_hint(entry.get("image_text", ""), entry.get("title_hint", ""))

    seen = set()
    candidates = []
    for query in search_queries(entry, png):
        try:
            notices = search_lh_notices(query)
        except Exception:
            notices = []
        for notice in notices:
            pan_id = notice.get("pan_id")
            if pan_id and pan_id not in seen:
                seen.add(pan_id)
                candidates.append(notice)
        if candidates and query != "든든전세":
            break

    if candidates:
        ranked = sorted(candidates, key=lambda notice: score_notice(notice, entry, png), reverse=True)
        best = ranked[0]
        if score_notice(best, entry, png) >= 10 or len(ranked) == 1:
            return best, entry.get("detected_by") or "PNG 내부 공고 문구 OCR"

    legacy_key = entry.get("legacy_key") or key_from_text(png.stem)
    legacy_notice = legacy_notice_from_key(legacy_key)
    if legacy_notice:
        return legacy_notice, entry.get("detected_by") or "이전 기본 공고 매칭"
    return None, entry.get("detected_by", "")


def discover_reports():
    pngs = sorted(INPUT_DIR.glob("*.png"), key=lambda path: path.stat().st_mtime, reverse=True)
    selected = {}
    reports = []
    for png in pngs:
        notice, detected_by = resolve_notice_for_png(png)
        if not notice:
            continue
        pan_id = notice.get("pan_id")
        if pan_id in selected:
            continue
        selected[pan_id] = png
        reports.append(notice_to_meta(png, notice, detected_by))
    return reports

def select_supply_table(tables):
    preferred_indexes = [24] + [idx for idx in range(len(tables)) if idx != 24]
    for idx in preferred_indexes:
        if idx >= len(tables):
            continue
        table = tables[idx]
        if table.shape[1] < 8 or len(table) == 0:
            continue
        supply_sum = table.iloc[:, 5].map(num).sum()
        housing_count = table.iloc[:, 1].map(clean_text).astype(bool).sum()
        if supply_sum > 0 and housing_count > 0:
            return table
    raise RuntimeError("LH 페이지에서 공급/신청 데이터 표를 찾지 못했습니다.")


def load_location(apt_code, sbd_code):
    url = "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectListLatLtd.do"
    data = urllib.parse.urlencode({"aptBrndCd": apt_code, "sbdLgoNo": sbd_code}).encode()
    rows = json.loads(fetch_text(url, data=data))
    coords = []
    addresses = []
    for row in rows:
        lat = row.get("coaCodtXxs")
        lon = row.get("coaCodtYxs")
        if lat and lon:
            coords.append((float(lat), float(lon)))
        address = clean_text(row.get("dngHsAdr", ""))
        if address:
            addresses.append(address)
    if not coords:
        return {"주소": addresses[0] if addresses else "", "위도": pd.NA, "경도": pd.NA}
    return {
        "주소": addresses[0] if addresses else "",
        "위도": sum(lat for lat, _ in coords) / len(coords),
        "경도": sum(lon for _, lon in coords) / len(coords),
    }


def geocode_address(address):
    if not address:
        return None
    query = address.split("(")[0].strip()
    if not query:
        return None
    url = "https://nominatim.openstreetmap.org/search?format=json&limit=1&q=" + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers={"User-Agent": "lh-report-generator/1.0"})
    try:
        rows = json.loads(urllib.request.urlopen(req, timeout=20).read().decode("utf-8"))
    except Exception:
        return None
    if not rows:
        return None
    return float(rows[0]["lat"]), float(rows[0]["lon"])


def markdown_table(df, columns):
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[col]).replace("|", "/") for col in columns) + " |")
    return "\n".join(lines)


def extract_js_value(html, name):
    match = re.search(rf"var\s+{re.escape(name)}\s*=\s*'([^']*)'", html)
    return clean_text(match.group(1)) if match else ""


def application_schedule(html):
    start_date = extract_js_value(html, "sbscAcpStDt")
    end_date = extract_js_value(html, "sbscAcpClsgDt")
    start_time = extract_js_value(html, "sbscAcpStHm")
    end_time = extract_js_value(html, "sbscAcpClsgHm")
    if start_date and end_date:
        start = f"{start_date} {start_time}".strip()
        end = f"{end_date} {end_time}".strip()
        return f"{start} ~ {end}"
    return "확인 필요"


def application_status_from_table(raw):
    if raw.shape[1] < 9:
        return pd.Series(["확인 필요"] * len(raw), index=raw.index)
    return raw.iloc[:, 8].map(clean_text).replace("", "확인 필요")


def unique_join(values):
    cleaned = []
    for value in values:
        text = clean_text(value)
        if text and text not in cleaned:
            cleaned.append(text)
    return ", ".join(cleaned) if cleaned else "확인 필요"


def format_output(df):
    out = df.copy()
    out["당첨 경쟁률"] = out["당첨 경쟁률"].map(fmt_ratio)
    out["예비 포함 경쟁률"] = out["예비 포함 경쟁률"].map(fmt_ratio)
    out["당첨확률(단순)"] = out["당첨확률(단순)"].map(fmt_pct)
    out["예비포함 가능권(단순)"] = out["예비포함 가능권(단순)"].map(fmt_pct)
    for col in ["공급호수(당첨자)", "모집인원(예비자)", "신청건수"]:
        out[col] = out[col].map(lambda value: f"{int(value):,}")
    if "서대문역 5번출구 직선거리(km)" in out:
        out["서대문역 5번출구 직선거리(km)"] = out["서대문역 5번출구 직선거리(km)"].map(
            lambda value: "좌표 없음" if pd.isna(value) else f"{float(value):.2f}"
        )
    return out


def load_data(meta):
    params = urllib.parse.urlencode(
        {
            "aisTpCd": meta.get("ais_tp_cd", "26"),
            "ccrCnntSysDsCd": meta.get("ccr_cnnt_sys_ds_cd", "03"),
            "mi": "1026",
            "panId": meta["pan_id"],
            "uppAisTpCd": meta.get("upp_ais_tp_cd", "13"),
        }
    )
    url = "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancInfo.do?" + params
    html = fetch_text(url)
    raw = select_supply_table(pd.read_html(StringIO(html)))
    df = pd.DataFrame(
        {
            "지역명": raw.iloc[:, 0].map(clean_text),
            "주택정보": raw.iloc[:, 1].map(clean_text),
            "주택형": raw.iloc[:, 4].map(clean_text),
            "공급호수(당첨자)": raw.iloc[:, 5].map(num),
            "모집인원(예비자)": raw.iloc[:, 6].map(num),
            "신청건수": raw.iloc[:, 7].map(num),
            "청약상태": application_status_from_table(raw),
            "접수기간": application_schedule(html),
        }
    )
    df = df[
        (df["지역명"] != "")
        & (df["주택정보"] != "")
        & (df["주택형"] != "")
        & (df["공급호수(당첨자)"] > 0)
    ]
    df = df.drop_duplicates().reset_index(drop=True)

    table_match = re.search(r'<table id="htyListTb05".*?</table>', html, re.S)
    calls = re.findall(r"mapPop\((.*?)\)", table_match.group(0))[: len(df)] if table_match else []
    cache = {}
    locations = []
    for call in calls:
        args = parse_map_args(call)
        if len(args) < 2:
            locations.append({})
            continue
        key = (args[-2], args[-1])
        if key not in cache:
            cache[key] = load_location(*key)
        locations.append(cache[key])

    loc_df = pd.DataFrame(locations if locations else [{} for _ in range(len(df))])
    for col in ["주소", "위도", "경도"]:
        if col not in loc_df.columns:
            loc_df[col] = pd.NA
    df = pd.concat([df, loc_df.iloc[: len(df)].reset_index(drop=True)], axis=1)

    missing = df["위도"].isna() | df["경도"].isna()
    for idx, row in df[missing].iterrows():
        coords = geocode_address(str(row.get("주소", "")))
        if coords:
            df.at[idx, "위도"] = coords[0]
            df.at[idx, "경도"] = coords[1]
            time.sleep(1)

    has_coords = df["위도"].notna() & df["경도"].notna()
    df.loc[has_coords, "서대문역 5번출구 직선거리(km)"] = df[has_coords].apply(
        lambda row: haversine_km(TARGET_LAT, TARGET_LON, float(row["위도"]), float(row["경도"])),
        axis=1,
    )

    df["당첨 경쟁률"] = df.apply(lambda row: safe_div(row["신청건수"], row["공급호수(당첨자)"]), axis=1)
    df["예비 포함 경쟁률"] = df.apply(
        lambda row: safe_div(row["신청건수"], row["공급호수(당첨자)"] + row["모집인원(예비자)"]),
        axis=1,
    )
    df["당첨확률(단순)"] = df.apply(
        lambda row: safe_div(row["공급호수(당첨자)"], row["신청건수"]) if row["신청건수"] else 1,
        axis=1,
    )
    df["예비포함 가능권(단순)"] = df.apply(
        lambda row: safe_div(row["공급호수(당첨자)"] + row["모집인원(예비자)"], row["신청건수"])
        if row["신청건수"]
        else 1,
        axis=1,
    )
    return df, url


def access_info(row):
    housing = str(row["주택정보"])
    for pattern, station, route, subway, total in ACCESS_RULES:
        if pattern in housing:
            return station, route, subway, total
    return "인근 역 확인 필요", "대중교통 앱에서 실시간 경로 확인 권장", "추정 불가", "추정 불가"


def access_section(low):
    rows = []
    for _, row in low.iterrows():
        station, route, subway, total = access_info(row)
        dist = row.get("서대문역 5번출구 직선거리(km)", pd.NA)
        rows.append(
            {
                "지역명": row["지역명"],
                "주택정보": row["주택정보"],
                "주택형": row["주택형"],
                "청약상태": row.get("청약상태", "확인 필요"),
                "접수기간": row.get("접수기간", "확인 필요"),
                "직선거리(km)": "좌표 없음" if pd.isna(dist) else f"{float(dist):.2f}",
                "권장 접근역": station,
                "지하철 경로 요약": route,
                "지하철 구간 예상": subway,
                "출구까지 총 예상": total,
            }
        )
    return pd.DataFrame(rows)


def build_report(meta):
    df, url = load_data(meta)
    total_supply = int(df["공급호수(당첨자)"].sum())
    total_wait = int(df["모집인원(예비자)"].sum())
    total_apply = int(df["신청건수"].sum())

    high = df.sort_values(["당첨 경쟁률", "신청건수"], ascending=[False, False]).head(3)
    low = df.sort_values(["당첨 경쟁률", "신청건수"], ascending=[True, True]).head(3)
    nearest = df[df["서대문역 5번출구 직선거리(km)"].notna()].sort_values(
        ["서대문역 5번출구 직선거리(km)", "당첨 경쟁률"]
    ).head(3)
    all_ranked = df.sort_values(["당첨 경쟁률", "신청건수"], ascending=[False, False])

    short_cols = [
        "지역명",
        "주택정보",
        "주택형",
        "청약상태",
        "접수기간",
        "공급호수(당첨자)",
        "모집인원(예비자)",
        "신청건수",
        "당첨 경쟁률",
        "예비 포함 경쟁률",
        "당첨확률(단순)",
    ]
    all_cols = short_cols + ["예비포함 가능권(단순)"]
    nearest_cols = [
        "지역명",
        "주택정보",
        "주택형",
        "주소",
        "청약상태",
        "접수기간",
        "서대문역 5번출구 직선거리(km)",
        "공급호수(당첨자)",
        "모집인원(예비자)",
        "신청건수",
        "당첨 경쟁률",
    ]
    access_cols = [
        "지역명",
        "주택정보",
        "주택형",
        "청약상태",
        "접수기간",
        "직선거리(km)",
        "권장 접근역",
        "지하철 경로 요약",
        "지하철 구간 예상",
        "출구까지 총 예상",
    ]

    lines = [
        f"# {meta['key']} LH 경쟁률 보고서",
        "",
    ]
    if meta.get("png"):
        lines.append(f"- 기준 PNG: `{meta['png']}`")
    else:
        lines.append("- 수집 방식: LH 공고 페이지 직접 크롤링")
    lines.extend([
        f"- 공고명: {meta['title']}",
        f"- 공식 페이지: {url}",
        f"- 생성시각: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 분석 기준",
        "",
        "- 당첨 경쟁률 = 신청건수 / 공급호수(당첨자). 경쟁이 치열한 물건과 당첨확률 높은 물건을 가르는 주 기준입니다.",
        "- 예비 포함 경쟁률 = 신청건수 / (공급호수 + 모집인원). 4배수 예비자까지 포함했을 때의 보조 지표입니다.",
        "- 당첨확률(단순) = 공급호수 / 신청건수. 실제 추첨/자격심사/중복신청/부적격/포기 등은 반영하지 않은 단순 산술값입니다.",
        "",
        "## 전체 요약",
        "",
        f"- 분석 물건/주택형 수: {len(df):,}개",
        f"- 청약상태: {unique_join(df.get('청약상태', []))}",
        f"- 접수기간: {unique_join(df.get('접수기간', []))}",
        f"- 당첨자 공급호수 합계: {total_supply:,}호",
        f"- 예비자 모집인원 합계: {total_wait:,}명",
        f"- 신청건수 합계: {total_apply:,}건",
        f"- 전체 당첨 경쟁률: {fmt_ratio(safe_div(total_apply, total_supply))}",
        f"- 전체 예비 포함 경쟁률: {fmt_ratio(safe_div(total_apply, total_supply + total_wait))}",
        "",
        "## 서대문역 5번 출구 기준 가까운 물건 TOP 3",
        "",
        f"- 기준 좌표: 서대문역 5번 출구 인근 역 좌표({TARGET_LAT:.5f}, {TARGET_LON:.5f})",
        "- 거리 기준: LH 지도 좌표를 우선 사용하고, 좌표가 비어 있는 물건은 주소 기반 OSM 보조 지오코딩으로 보정한 직선거리입니다. 실제 도로 이동거리와는 다를 수 있습니다.",
        "",
        markdown_table(format_output(nearest), nearest_cols),
        "",
        "## 경쟁이 치열한 물건 TOP 3",
        "",
        markdown_table(format_output(high), short_cols),
        "",
        "## 신청 대비 당첨확률이 높은 물건 TOP 3",
        "",
        markdown_table(format_output(low), short_cols),
        "",
        "## 당첨확률 TOP 3 서대문역 5번 출구 접근성",
        "",
        "- 거리는 물건 좌표와 서대문역 5번 출구 인근 기준 좌표 간 직선거리입니다.",
        "- 예상 시간은 평상시 기준의 지하철 이동 추정치입니다. 권장 접근역까지의 도보/버스 접근과 환승 대기에 따라 달라질 수 있습니다.",
        "",
        markdown_table(access_section(low), access_cols),
        "",
        "## 전체 물건별 경쟁률",
        "",
        markdown_table(format_output(all_ranked), all_cols),
        "",
    ])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / meta["out"]
    full_csv_path = OUTPUT_DIR / meta["csv"]
    distance_csv_path = OUTPUT_DIR / meta["dist_csv"]
    report_path.write_text("\n".join(lines), encoding="utf-8-sig")
    format_output(all_ranked).to_csv(full_csv_path, index=False, encoding="utf-8-sig")
    dist_cols = [
        "지역명",
        "주택정보",
        "주택형",
        "주소",
        "위도",
        "경도",
        "청약상태",
        "접수기간",
        "서대문역 5번출구 직선거리(km)",
        "공급호수(당첨자)",
        "모집인원(예비자)",
        "신청건수",
        "당첨 경쟁률",
        "예비 포함 경쟁률",
        "당첨확률(단순)",
        "예비포함 가능권(단순)",
    ]
    distance_ranked = df.sort_values(["서대문역 5번출구 직선거리(km)", "당첨 경쟁률"], na_position="last")
    format_output(distance_ranked)[dist_cols].to_csv(distance_csv_path, index=False, encoding="utf-8-sig")
    return {
        "key": meta["key"],
        "report": report_path,
        "csv": full_csv_path,
        "dist_csv": distance_csv_path,
        "rows": len(df),
        "applications": total_apply,
    }


def write_combined_report(results):
    if not results:
        return None
    lines = [
        "# LH 경쟁률 통합 생성 결과",
        "",
        f"- 생성시각: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 그래프 생성은 제외하고, Markdown 보고서와 CSV 데이터만 생성했습니다.",
        "",
        "| 지역 | 개별 보고서 | 전체 데이터 CSV | 거리 데이터 CSV | 분석 건수 | 신청건수 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for result in results:
        lines.append(
            "| "
            + " | ".join(
                [
                    result["key"],
                    result["report"].name,
                    result["csv"].name,
                    result["dist_csv"].name,
                    f"{result['rows']:,}",
                    f"{result['applications']:,}",
                ]
            )
            + " |"
        )
    lines.extend(["", "## 개별 보고서 내용", ""])
    for result in results:
        text = result["report"].read_text(encoding="utf-8-sig").strip()
        lines.extend([f"---", "", text, ""])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "통합_경쟁률_보고서.txt"
    path.write_text("\n".join(lines), encoding="utf-8-sig")
    return path


def main():
    reports = discover_reports()
    if not reports:
        print("지원되는 PNG 파일을 찾지 못했습니다.")
        print("PNG 내부 공고명/지역명 또는 파일명으로 LH 공고를 찾지 못했습니다.")
        print("캡처 화면에 LH 공고 제목 또는 지역명이 보이도록 저장한 뒤 다시 실행해 주세요.")
        return 1

    print(f"작업 폴더: {BASE}")
    print(f"결과 폴더: {OUTPUT_DIR}")
    print("그래프 생성 제외: Markdown/CSV 보고서만 생성합니다.")
    results = []
    for meta in reports:
        print(f"[{meta['key']}] {meta['png']} 처리 중... 감지기준={meta.get('detected_by', '')}")
        result = build_report(meta)
        results.append(result)
        print(f"  - 보고서: {result['report'].name}")
        print(f"  - 전체 데이터: {result['csv'].name}")
        print(f"  - 거리 데이터: {result['dist_csv'].name}")

    combined = write_combined_report(results)
    if combined:
        print(f"통합 보고서: {combined.name}")
    print("완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())







