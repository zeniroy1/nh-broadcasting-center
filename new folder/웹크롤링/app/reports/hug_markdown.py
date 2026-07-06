from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


def md_cell(value: Any) -> str:
    return str(value).replace("|", "/")


def distance_text(row: dict[str, Any]) -> str:
    value = row.get("서대문역5번출구_추정거리_km")
    return "-" if value is None or value == "" else f"{float(value):.2f}"


def top_rows(rows: list[dict[str, Any]], top_n: int) -> tuple[list[dict[str, Any]], ...]:
    by_deposit = sorted(rows, key=lambda row: (row["임대보증금_숫자"], row["신청자수"]))[:top_n]
    by_distance = sorted(
        [row for row in rows if row.get("서대문역5번출구_추정거리_km") is not None],
        key=lambda row: (row["서대문역5번출구_추정거리_km"], row["임대보증금_숫자"], row["신청자수"]),
    )[:top_n]
    by_apply = sorted(rows, key=lambda row: (row["신청자수"], row["임대보증금_숫자"]))[:top_n]
    combined = sorted(
        [row for row in rows if "거리순위" in row],
        key=lambda row: (row["종합점수"], row["임대보증금_숫자"], row["신청자수"]),
    )[:top_n]
    return by_deposit, by_distance, by_apply, combined


def table(title: str, rows: list[dict[str, Any]], include_score: bool) -> list[str]:
    lines = ["", f"## {title}", ""]
    if include_score:
        lines.extend(
            [
                "| 순위 | 시군구 | 주소 | 임대보증금 | 거리(km) | 최단 지하철 예상시간 | 신청자수 | 종합점수 |",
                "| ---: | --- | --- | ---: | ---: | --- | ---: | ---: |",
            ]
        )
    else:
        lines.extend(
            [
                "| 순위 | 시군구 | 주소 | 임대보증금 | 거리(km) | 최단 지하철 예상시간 | 신청자수 |",
                "| ---: | --- | --- | ---: | ---: | --- | ---: |",
            ]
        )
    for index, row in enumerate(rows, 1):
        line = (
            f"| {index} | {md_cell(row['시군구'])} | {md_cell(row['주소'])} | "
            f"{row['임대보증금']} | {distance_text(row)} | "
            f"{row['서대문역_최단지하철예상시간']} | {row['신청자수']}"
        )
        if include_score:
            line += f" | {row['종합점수']}"
        lines.append(line + " |")
    return lines


def write_hug_summary(
    path: Path,
    region_name: str,
    rows: list[dict[str, Any]],
    last_page: int,
    settings: dict[str, Any],
) -> None:
    top_n = int(settings["hug"]["summary_top_n"])
    target_name = settings["hug"]["target_location"]["name"]
    by_deposit, by_distance, by_apply, combined = top_rows(rows, top_n)
    lines = [
        f"# HUG {region_name} 요약",
        "",
        f"- 생성시각: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- 대상 데이터: HUG {region_name} 전체 {len(rows):,}건",
        f"- 수집 페이지: 1~{last_page}",
        f"- 거리 기준: 주소에서 추출한 지역 단위 중심 좌표 기준 {target_name}까지의 추정 직선거리입니다.",
        "- 지하철 시간 기준: 서대문역까지 최단 지하철 이동 기준 예상 소요시간입니다. 도보, 대기, 실시간 운행상황은 반영하지 않은 참고값입니다.",
        "- 종합점수 기준: 보증금 낮은 순위 + 거리 가까운 순위 + 신청자수 적은 순위의 합산이며 낮을수록 좋습니다.",
    ]
    lines.extend(table(f"임대보증금 저렴한 TOP {top_n}", by_deposit, False))
    lines.extend(table(f"{target_name} 거리 가까운 TOP {top_n}", by_distance, False))
    lines.extend(table(f"신청자수 적은 TOP {top_n}", by_apply, False))
    lines.extend(table(f"보증금+거리+신청자수 종합 TOP {top_n}", combined, True))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8-sig")
