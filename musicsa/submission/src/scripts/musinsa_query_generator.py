"""Generate Musinsa search query candidates from parsed purchase intent."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


CURRENT_DIR = Path(__file__).resolve().parent
SRC_ROOT = CURRENT_DIR.parents[0]
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from musinsa_intent_parser import parse_to_dict
from musinsa_runtime_paths import resource_path


COLOR_TERMS = {
    "black": ["블랙", "검정", "검은색"],
    "white": ["화이트", "흰색"],
    "gray": ["그레이", "회색"],
    "charcoal": ["차콜", "챠콜"],
    "navy": ["네이비", "남색"],
    "blue": ["블루", "파랑"],
    "skyblue": ["소라", "스카이블루", "하늘색"],
    "red": ["레드", "빨강"],
    "burgundy": ["버건디", "와인"],
    "pink": ["핑크", "분홍"],
    "orange": ["오렌지", "주황"],
    "yellow": ["옐로우", "노랑"],
    "green": ["그린", "민트"],
    "khaki": ["카키", "올리브"],
    "beige": ["베이지", "아이보리", "크림"],
    "brown": ["브라운", "갈색", "카멜"],
    "purple": ["퍼플", "라벤더"],
    "silver": ["실버"],
    "gold": ["골드", "금색"],
}

STYLE_TERMS = {
    "plain": ["무지", "로고 없는", "프린트 없는"],
    "basic": ["베이직", "기본", "무난한"],
    "minimal": ["미니멀", "깔끔한", "심플"],
    "oversized": ["오버핏", "루즈핏"],
    "regular_fit": ["레귤러핏", "정핏", "스탠다드핏"],
}

FALLBACK_CATEGORY_TERMS = {
    "short_sleeve_tshirt": ["반팔 티셔츠", "반팔티", "반소매 티셔츠"],
    "outer": ["아우터", "자켓", "재킷"],
    "pants": ["바지", "팬츠"],
}


def _query_terms_from_value(value: str) -> list[str]:
    text = " ".join(str(value or "").split()).strip()
    if not text:
        return []
    raw_parts = text.split("/") if "/" in text else [text]
    normalized_parts = [" ".join(raw_part.split()).strip() for raw_part in raw_parts]
    terms: list[str] = []
    seen: set[str] = set()
    for index, part in enumerate(normalized_parts):
        if not part:
            continue
        variants = [part]
        if index == 0 and len(normalized_parts) > 1:
            next_words = normalized_parts[1].split()
            if len(next_words) > 1 and not part.endswith(next_words[-1]):
                variants.append(f"{part} {next_words[-1]}")
        compact = part.replace(" ", "")
        if compact != part:
            variants.append(compact)
        for variant in list(variants):
            compact_variant = variant.replace(" ", "")
            if compact_variant != variant:
                variants.append(compact_variant)
        for variant in variants:
            if variant not in seen:
                seen.add(variant)
                terms.append(variant)
    return terms


def _load_category_terms() -> dict[str, list[str]]:
    path = resource_path("config", "musinsa_category_keywords.json")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return FALLBACK_CATEGORY_TERMS
    terms: dict[str, list[str]] = {}
    for item in raw.get("categories", []):
        key = str(item.get("key") or "").strip()
        label = str(item.get("label") or "").strip()
        search_terms = [str(term).strip() for term in item.get("search_terms", []) if str(term).strip()]
        keywords = [str(keyword).strip() for keyword in item.get("keywords", []) if str(keyword).strip()]
        seen: set[str] = set()
        values: list[str] = []
        for value in [label, *search_terms, *keywords]:
            for normalized in _query_terms_from_value(value):
                if normalized and normalized not in seen:
                    seen.add(normalized)
                    values.append(normalized)
        if key and values:
            terms[key] = values
    return terms or FALLBACK_CATEGORY_TERMS


CATEGORY_TERMS = _load_category_terms()

GENDER_TERMS = {
    "M": ["남성", "남자"],
    "F": ["여성", "여자"],
    "A": ["공용", "유니섹스"],
}

PURPOSE_PRIORITY = {
    "exact_match": 100,
    "core_search": 90,
    "ranking_probe": 80,
    "review_probe": 70,
    "broad_discovery": 60,
    "fallback": 40,
}


@dataclass(frozen=True)
class QueryCandidate:
    query: str
    purpose: str
    priority: int
    reason: str
    expected_sources: list[str]
    must_apply_filters: list[str] = field(default_factory=list)
    avoid_terms: list[str] = field(default_factory=list)


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = " ".join(item.split())
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def _first_terms(intent: dict[str, Any], key: str, dictionary: dict[str, list[str]]) -> list[str]:
    values = intent.get(key) or []
    terms: list[str] = []
    for value in values:
        terms.extend(dictionary.get(value, []))
    return _unique(terms)


def _category_terms(intent: dict[str, Any]) -> list[str]:
    product_group = intent.get("product_group")
    if product_group and product_group in CATEGORY_TERMS:
        return CATEGORY_TERMS[product_group]
    label = intent.get("category_label")
    return [label] if label else ["상품"]


def _gender_terms(intent: dict[str, Any]) -> list[str]:
    return GENDER_TERMS.get(intent.get("gender"), [])


def _free_terms(intent: dict[str, Any]) -> list[str]:
    return _unique(intent.get("free_terms") or [])


def _specific_terms(intent: dict[str, Any]) -> list[str]:
    return _unique(intent.get("specific_terms") or [])


def _price_filter(intent: dict[str, Any]) -> str | None:
    price_min = intent.get("price_min")
    price_max = intent.get("price_max")
    if price_min is None and price_max is None:
        return None
    return f"price:{price_min or ''}-{price_max or ''}"


def _avoid_terms(intent: dict[str, Any]) -> list[str]:
    avoid: list[str] = []
    excluded = set(intent.get("excluded_conditions") or [])
    if "visible_logo" in excluded:
        avoid.extend(["로고", "그래픽", "프린트"])
    if "flashy_design" in excluded:
        avoid.extend(["화려한", "패턴", "그래픽"])
    return _unique(avoid)


def _clean_query_text(query: str) -> str:
    parts: list[str] = []
    for token in str(query or "").split():
        parts.extend(_query_terms_from_value(token))
    return " ".join(parts)


def _candidate(query: str, purpose: str, reason: str, sources: list[str], filters: list[str], avoid: list[str]) -> QueryCandidate:
    return QueryCandidate(
        query=_clean_query_text(query),
        purpose=purpose,
        priority=PURPOSE_PRIORITY[purpose],
        reason=reason,
        expected_sources=sources,
        must_apply_filters=filters,
        avoid_terms=avoid,
    )


def generate_query_candidates(text: str) -> dict[str, Any]:
    intent = parse_to_dict(text)
    colors = _first_terms(intent, "colors", COLOR_TERMS)
    styles = _first_terms(intent, "styles", STYLE_TERMS)
    categories = _category_terms(intent)
    genders = _gender_terms(intent)
    specific_terms = _specific_terms(intent)
    free_terms = _free_terms(intent)
    specific_text = " ".join(specific_terms[:3])
    free_text = " ".join([*specific_terms[:3], *free_terms[:4]])
    filters = [condition for condition in [_price_filter(intent), f"gender:{intent.get('gender')}" if intent.get("gender") else None] if condition]
    avoid = _avoid_terms(intent)

    primary_color = colors[0] if colors else ""
    primary_style = styles[0] if styles else ""
    primary_category = categories[0]
    primary_gender = genders[0] if genders else ""
    candidates: list[QueryCandidate] = []

    exact_target = specific_text or free_text or (primary_category if intent.get("product_group") else "")
    exact_parts = [primary_gender, primary_color, primary_style, exact_target]
    candidates.append(
        _candidate(
            " ".join(part for part in exact_parts if part),
            "exact_match",
            "사용자 조건을 가장 많이 포함한 1차 검색어입니다.",
            ["search_results_page", "product_detail_page"],
            filters,
            avoid,
        )
    )

    if specific_terms:
        for term in specific_terms[:4]:
            candidates.append(
                _candidate(
                    " ".join(part for part in [primary_gender, primary_color, term] if part),
                    "core_search",
                    "사용자가 입력한 구체 품목어를 우선 보존한 검색어입니다.",
                    ["search_results_page"],
                    filters,
                    avoid,
                )
            )

    for style in styles[:3]:
        candidates.append(
            _candidate(
                " ".join(part for part in [primary_color, style, free_text or primary_category] if part),
                "core_search",
                "색상, 스타일, 상품군을 조합한 핵심 검색어입니다.",
                ["search_results_page"],
                filters,
                avoid,
            )
        )

    for category in categories[:5]:
        candidates.append(
            _candidate(
                " ".join(part for part in [primary_gender, primary_color, free_text, category if intent.get("product_group") else ""] if part),
                "ranking_probe",
                "랭킹/카테고리 후보 수집에 사용할 검색어입니다.",
                ["ranking_page", "category_page"],
                filters,
                avoid,
            )
        )

    for color in colors[1:4]:
        for category in categories[:5]:
            candidates.append(
                _candidate(
                    " ".join(part for part in [primary_gender, color, free_text, category if intent.get("product_group") else ""] if part),
                    "fallback",
                    "대표 색상과 가까운 색상 표현을 함께 확인하는 보조 검색어입니다.",
                    ["search_results_page"],
                    filters,
                    avoid,
                )
            )

    candidates.append(
        _candidate(
            " ".join(part for part in [primary_style or "베이직", free_text or primary_category, "리뷰"] if part),
            "review_probe",
            "리뷰 기반 정제 지표를 확인하기 위한 검색어입니다.",
            ["review_area", "product_detail_page"],
            filters,
            avoid,
        )
    )

    candidates.append(
        _candidate(
            free_text or primary_category,
            "broad_discovery",
            "너무 좁은 검색 결과를 보완하기 위한 넓은 후보 검색어입니다.",
            ["search_results_page", "category_page"],
            filters,
            avoid,
        )
    )

    if intent.get("generated_keywords"):
        for generated in intent["generated_keywords"][:4]:
            candidates.append(
                _candidate(
                    generated,
                    "fallback",
                    "1단계 Intent Parser가 생성한 보조 검색어입니다.",
                    ["search_results_page"],
                    filters,
                    avoid,
                )
            )

    for term in free_terms[:6]:
        candidates.append(
            _candidate(
                " ".join(part for part in [primary_color, term] if part),
                "fallback",
                "사용자가 입력한 자유 키워드를 보존한 검색어입니다.",
                ["search_results_page"],
                filters,
                avoid,
            )
        )

    deduped: dict[str, QueryCandidate] = {}
    for candidate in candidates:
        existing = deduped.get(candidate.query)
        if existing is None or candidate.priority > existing.priority:
            deduped[candidate.query] = candidate

    ordered = sorted(deduped.values(), key=lambda item: (-item.priority, item.query))
    return {
        "raw_text": text,
        "parsed_intent": intent,
        "candidate_count": len(ordered),
        "candidates": [asdict(candidate) for candidate in ordered],
        "rule": "검색어 후보는 목적별로 생성하고, 실제 수집 단계에서 필터와 함께 사용합니다.",
    }


def validate_query_candidates(text: str) -> list[str]:
    errors: list[str] = []
    result = generate_query_candidates(text)
    candidates = result["candidates"]
    if not candidates:
        errors.append("No query candidates generated")
    queries = [candidate["query"] for candidate in candidates]
    if len(queries) != len(set(queries)):
        errors.append("Duplicate query candidates found")
    priorities = [candidate["priority"] for candidate in candidates]
    if priorities != sorted(priorities, reverse=True):
        errors.append("Candidates are not sorted by priority")
    for candidate in candidates:
        if candidate["purpose"] not in PURPOSE_PRIORITY:
            errors.append(f"Unknown purpose: {candidate['purpose']}")
        if not candidate["expected_sources"]:
            errors.append(f"No expected sources for query: {candidate['query']}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Musinsa search query candidates.")
    parser.add_argument("query", nargs="?", help="Natural-language shopping request")
    parser.add_argument("--validate", action="store_true", help="Validate generated query candidates")
    args = parser.parse_args()

    query = args.query or "검은색 반팔 무지티를 2~3만원대에서 40대 남성이 입기 좋은 제품으로 찾아줘"
    if args.validate:
        errors = validate_query_candidates(query)
        print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
        raise SystemExit(1 if errors else 0)
    print(json.dumps(generate_query_candidates(query), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
