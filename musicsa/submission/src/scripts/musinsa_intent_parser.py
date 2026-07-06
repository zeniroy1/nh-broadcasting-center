"""Parse Korean shopping intent into structured Musinsa search conditions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable


CURRENT_DIR = Path(__file__).resolve().parent
SRC_ROOT = CURRENT_DIR.parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from musinsa_runtime_paths import resource_path

CATEGORY_CONFIG_PATH = resource_path("config", "musinsa_category_keywords.json")


FALLBACK_CATEGORY_KEYWORDS = {
    "short_sleeve_tshirt": {
        "label": "반팔 티셔츠",
        "keywords": ["반팔", "반소매", "티셔츠", "티", "무지티", "무지 티"],
        "musinsa_hint": "상의 > 반소매 티셔츠",
    },
    "outer": {
        "label": "아우터",
        "keywords": ["아우터", "자켓", "재킷", "점퍼", "가디건"],
        "musinsa_hint": "아우터",
    },
    "pants": {
        "label": "바지",
        "keywords": ["바지", "팬츠", "슬랙스", "데님"],
        "musinsa_hint": "바지",
    },
}


def _load_category_keywords(path: Path = CATEGORY_CONFIG_PATH) -> dict[str, dict[str, object]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return FALLBACK_CATEGORY_KEYWORDS
    categories: dict[str, dict[str, object]] = {}
    for item in raw.get("categories", []):
        key = str(item.get("key") or "").strip()
        label = str(item.get("label") or "").strip()
        keywords = [str(keyword).strip() for keyword in item.get("keywords", []) if str(keyword).strip()]
        if not key or not label or not keywords:
            continue
        categories[key] = {
            "label": label,
            "keywords": keywords,
            "musinsa_hint": str(item.get("musinsa_hint") or label).strip(),
            "search_terms": [str(term).strip() for term in item.get("search_terms", []) if str(term).strip()],
        }
    return categories or FALLBACK_CATEGORY_KEYWORDS


CATEGORY_KEYWORDS = _load_category_keywords()

# Categories that bundle several distinct sub-items under one broad label.
# A matched category keyword that is NOT in the broad set is treated as a
# "specific item term" and preserved so a specific-term search (e.g. 래시가드)
# does not collapse into the whole category (e.g. 수영복 전체).
CATEGORY_BROAD_TERMS = {
    "swimwear": {"수영복", "비치웨어", "스윔웨어", "swimwear"},
    "one_piece_dress": {"원피스", "드레스", "dress", "one piece"},
    "skirt": {"스커트", "치마", "skirt"},
    "cap_hat": {"모자", "hat", "cap"},
    "padding": {"패딩", "다운", "puffer", "down"},
    "sandals_slippers": {"샌들", "샌달", "슬리퍼", "slippers", "sandals"},
    "outer": {"아우터"},
}

COLOR_KEYWORDS = {
    "black": ["검은색", "검정색", "검정", "블랙", "black"],
    "white": ["흰색", "화이트", "하얀색", "백색", "white"],
    "gray": ["회색", "그레이", "라이트그레이", "애쉬", "멜란지", "gray", "grey"],
    "charcoal": ["차콜", "챠콜", "먹색", "다크그레이", "charcoal"],
    "navy": ["네이비", "남색", "곤색", "navy"],
    "blue": ["파란색", "파랑", "블루", "청색", "blue"],
    "skyblue": ["하늘색", "소라색", "소라", "스카이블루", "라이트블루", "sky blue", "skyblue"],
    "red": ["빨간색", "빨강", "레드", "red"],
    "burgundy": ["버건디", "와인색", "와인", "burgundy", "wine"],
    "pink": ["분홍색", "분홍", "핑크", "연핑크", "pink"],
    "orange": ["주황색", "주황", "오렌지", "orange"],
    "yellow": ["노란색", "노랑", "옐로우", "yellow"],
    "green": ["초록색", "초록", "그린", "민트", "민트색", "green", "mint"],
    "khaki": ["카키", "올리브", "올리브그린", "olive", "khaki"],
    "beige": ["베이지", "아이보리", "크림", "오트밀", "샌드", "beige", "ivory", "cream", "oatmeal", "sand"],
    "brown": ["갈색", "브라운", "초코", "초콜릿", "카멜", "camel", "brown", "chocolate"],
    "purple": ["보라색", "보라", "퍼플", "라벤더", "purple", "lavender"],
    "silver": ["실버", "silver"],
    "gold": ["골드", "금색", "gold"],
}

STYLE_KEYWORDS = {
    "plain": ["무지", "로고 없는", "로고없", "프린트 없는", "프린트없"],
    "basic": ["기본", "베이직", "무난", "데일리"],
    "minimal": ["미니멀", "깔끔", "심플"],
    "oversized": ["오버핏", "오버 사이즈", "루즈핏"],
    "regular_fit": ["레귤러핏", "정핏", "스탠다드핏"],
}

GENDER_KEYWORDS = {
    "M": ["남성", "남자", "남편", "아빠", "남"],
    "F": ["여성", "여자", "엄마", "여"],
    "A": ["공용", "유니섹스", "남녀공용", "전체"],
}

ACTIVE_AGE_PATTERNS = [
    (re.compile(r"20\s*대|이십\s*대"), "20s"),
    (re.compile(r"30\s*대|삼십\s*대"), "30s"),
    (re.compile(r"40\s*대|사십\s*대"), "40s"),
    (re.compile(r"50\s*대|오십\s*대"), "50s"),
    (re.compile(r"60\s*대|육십\s*대"), "60s"),
]
TEEN_CONTEXT_PATTERNS = [
    re.compile(r"10\s*대|십\s*대"),
    re.compile(r"1\d\s*(?:세|살)"),
    re.compile(r"청소년|중학생|고등학생"),
]
AGE_VALUE_PATTERN = re.compile(r"(?:만\s*)?(?P<age>\d{1,2})\s*(?:세|살)")
SUPPORTED_AGE_BANDS = {20: "20s", 30: "30s", 40: "40s", 50: "50s", 60: "60s"}

STOPWORDS = {
    "제품",
    "상품",
    "추천",
    "검색",
    "찾아줘",
    "찾아",
    "사고",
    "싶어",
    "구매",
    "입기",
    "좋은",
    "많이",
    "사는",
    "산",
    "에서",
    "으로",
    "으로도",
    "대",
    "정도",
    "대략",
    "비교",
    "후보",
    "가격",
    "가격대",
    "색깔",
    "색상",
    "나는",
    "내",
    "지금",
    "이고",
    "이며",
    "있어",
    "찾고",
    "찾고있어",
    "여름용",
    "여름",
    "나",
    "내가",
    "좀",
    "하나",
    "그리고",
    "또",
    "바로",
}

PARTICLE_SUFFIXES = [
    "으로도",
    "으로는",
    "으로",
    "에서",
    "에게",
    "까지",
    "부터",
    "처럼",
    "보다",
    "이라는",
    "라는",
    "이고",
    "이며",
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
    "와",
    "과",
    "도",
    "에",
    "의",
    "로",
]


@dataclass
class ParsedIntent:
    raw_text: str
    product_group: str | None
    category_label: str | None
    category_hint: str | None
    colors: list[str] = field(default_factory=list)
    styles: list[str] = field(default_factory=list)
    price_min: int | None = None
    price_max: int | None = None
    gender: str | None = None
    age_band: str | None = None
    teen_context: bool = False
    specific_terms: list[str] = field(default_factory=list)
    free_terms: list[str] = field(default_factory=list)
    required_conditions: list[str] = field(default_factory=list)
    preferred_conditions: list[str] = field(default_factory=list)
    excluded_conditions: list[str] = field(default_factory=list)
    generated_keywords: list[str] = field(default_factory=list)
    confidence: float = 0.0
    notes: list[str] = field(default_factory=list)


def _contains_any(text: str, keywords: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _detect_category(text: str) -> tuple[str | None, str | None, str | None]:
    matches: list[tuple[int, int, str, str, str]] = []
    for key, config in CATEGORY_KEYWORDS.items():
        matched_keywords = [
            str(keyword)
            for keyword in config["keywords"]
            if str(keyword).strip() and str(keyword).lower() in text.lower()
        ]
        if matched_keywords:
            longest_keyword = max(len(keyword.replace(" ", "")) for keyword in matched_keywords)
            is_top_level = 1 if ">" not in str(config["musinsa_hint"]) else 0
            matches.append((longest_keyword, -is_top_level, key, config["label"], config["musinsa_hint"]))
    if not matches:
        return None, None, None
    _longest_keyword, _specificity, key, label, hint = max(matches)
    return key, label, hint


def _detect_specific_terms(text: str, product_group: str | None) -> list[str]:
    """Preserve the specific item word the user typed within a broad category.

    Returns matched category keywords that are more specific than the broad
    category label (e.g. 래시가드 within the 수영복 category). Categories without
    a broad-term table return an empty list, keeping existing behaviour.
    """
    if not product_group:
        return []
    broad = CATEGORY_BROAD_TERMS.get(product_group)
    if not broad:
        return []
    config = CATEGORY_KEYWORDS.get(product_group)
    if not config:
        return []
    lowered = text.lower()
    broad_lower = {term.lower() for term in broad}
    specific: list[str] = []
    for keyword in config["keywords"]:
        token = str(keyword).strip()
        if not token or token.lower() in broad_lower:
            continue
        if token.lower() in lowered:
            specific.append(token)
    return _unique(specific)


def _detect_colors(text: str) -> list[str]:
    return [key for key, keywords in COLOR_KEYWORDS.items() if _contains_any(text, keywords)]


def _detect_styles(text: str) -> list[str]:
    return [key for key, keywords in STYLE_KEYWORDS.items() if _contains_any(text, keywords)]


def _detect_gender(text: str) -> str | None:
    for gender, keywords in GENDER_KEYWORDS.items():
        if _contains_any(text, keywords):
            return gender
    return None


def _age_to_band(age: int) -> str | None:
    decade = (age // 10) * 10
    return SUPPORTED_AGE_BANDS.get(decade)


def _detect_age_band(text: str) -> str | None:
    for pattern, age_band in ACTIVE_AGE_PATTERNS:
        if pattern.search(text):
            return age_band
    match = AGE_VALUE_PATTERN.search(text)
    if not match:
        return None
    return _age_to_band(int(match.group("age")))


def _detect_teen_context(text: str) -> bool:
    return any(pattern.search(text) for pattern in TEEN_CONTEXT_PATTERNS)


def _known_keyword_set() -> set[str]:
    known: set[str] = set(STOPWORDS)
    for dictionary in (CATEGORY_KEYWORDS,):
        for config in dictionary.values():
            known.update(keyword.replace(" ", "") for keyword in config["keywords"])
            known.add(config["label"].replace(" ", ""))
    for dictionary in (COLOR_KEYWORDS, STYLE_KEYWORDS, GENDER_KEYWORDS):
        for keywords in dictionary.values():
            known.update(keyword.replace(" ", "") for keyword in keywords)
    return known


def _compact_known_terms(*dictionaries: dict) -> set[str]:
    known: set[str] = set()
    for dictionary in dictionaries:
        for value in dictionary.values():
            if isinstance(value, dict):
                known.update(keyword.replace(" ", "") for keyword in value.get("keywords", []))
                if value.get("label"):
                    known.add(value["label"].replace(" ", ""))
            else:
                known.update(keyword.replace(" ", "") for keyword in value)
    return known


def _is_attribute_token(compact: str) -> bool:
    color_terms = _compact_known_terms(COLOR_KEYWORDS)
    for prefix in ("색깔은", "색상은", "컬러는", "색깔", "색상", "컬러"):
        if compact.startswith(prefix):
            remainder = compact[len(prefix) :]
            if remainder in color_terms:
                return True
    return compact in {"가격", "가격대", "금액", "금액대"}


def _is_known_style_category_compound(compact: str) -> bool:
    remainder = compact
    known_parts = sorted(
        _compact_known_terms(STYLE_KEYWORDS, CATEGORY_KEYWORDS) | {config["label"].replace(" ", "") for config in CATEGORY_KEYWORDS.values()},
        key=len,
        reverse=True,
    )
    changed = True
    while changed and remainder:
        changed = False
        for part in known_parts:
            if part and part in remainder:
                remainder = remainder.replace(part, "", 1)
                changed = True
                break
    return remainder == ""


def _remove_price_text(text: str) -> str:
    money_number = r"(?:\d{1,3}(?:,\d{3})+|\d+|[일이삼사오육칠팔구십]+)"
    bare_won_number = r"(?:\d{1,3}(?:,\d{3})+|\d{5,})"
    patterns = [
        rf"{money_number}\s*(?:~|-|부터|에서)\s*{money_number}\s*(?:만원대|만원|만|원대|원)?",
        rf"{money_number}\s*(?:만원대|만원|만|원대|원)\s*(?:이하|미만|안쪽|까지|이상|부터|정도|쯤)?",
        rf"{bare_won_number}\s*(?:이하|미만|안쪽|까지|이상|부터|정도|쯤)?",
        r"(?<!\d)만원대",
    ]
    result = text
    for pattern in patterns:
        result = re.sub(pattern, " ", result)
    return result


KOREAN_DIGITS = {
    "영": 0,
    "공": 0,
    "일": 1,
    "하나": 1,
    "이": 2,
    "둘": 2,
    "삼": 3,
    "셋": 3,
    "사": 4,
    "넷": 4,
    "오": 5,
    "다섯": 5,
    "육": 6,
    "여섯": 6,
    "칠": 7,
    "일곱": 7,
    "팔": 8,
    "여덟": 8,
    "구": 9,
    "아홉": 9,
}


def _korean_number_to_int(raw_number: str) -> int | None:
    value = raw_number.strip()
    if not value:
        return None
    if value in KOREAN_DIGITS:
        return KOREAN_DIGITS[value]
    if value == "십":
        return 10
    if "십" in value:
        tens_raw, ones_raw = value.split("십", 1)
        tens = KOREAN_DIGITS.get(tens_raw, 1) if tens_raw else 1
        ones = KOREAN_DIGITS.get(ones_raw, 0) if ones_raw else 0
        return tens * 10 + ones
    return None


def _remove_age_text(text: str) -> str:
    result = text
    for pattern, _age_band in ACTIVE_AGE_PATTERNS:
        result = pattern.sub(" ", result)
    for pattern in TEEN_CONTEXT_PATTERNS:
        result = pattern.sub(" ", result)
    return AGE_VALUE_PATTERN.sub(" ", result)


def _strip_particle(token: str) -> str:
    for suffix in PARTICLE_SUFFIXES:
        if token.endswith(suffix) and len(token) > len(suffix) + 1:
            return token[: -len(suffix)]
    return token


def _detect_free_terms(text: str) -> list[str]:
    cleaned = _remove_age_text(_remove_price_text(text))
    known = _known_keyword_set()
    terms: list[str] = []
    for token in re.findall(r"[가-힣A-Za-z0-9]+", cleaned):
        original = token.strip()
        original_compact = original.replace(" ", "")
        if original_compact in known or _is_attribute_token(original_compact) or _is_known_style_category_compound(original_compact):
            continue
        normalized = _strip_particle(original)
        compact = normalized.replace(" ", "")
        if len(normalized) < 2 or normalized.isdigit():
            continue
        if compact in known:
            continue
        if _is_attribute_token(compact):
            continue
        if _is_known_style_category_compound(compact):
            continue
        terms.append(normalized)
    return _unique(terms)


def _money_to_won(raw_number: str, has_manwon: bool) -> int:
    compact = raw_number.replace(",", "").strip()
    number = int(compact) if compact.isdigit() else _korean_number_to_int(compact)
    if number is None:
        raise ValueError(f"Unsupported money expression: {raw_number}")
    return number * 10000 if has_manwon else number


def _detect_price_range(text: str) -> tuple[int | None, int | None]:
    money_number = r"(?:\d{1,3}(?:,\d{3})+|\d+|[일이삼사오육칠팔구십]+)"
    range_match = re.search(
        rf"(?P<min>{money_number})\s*(?:~|-|부터|에서)\s*"
        rf"(?P<max>{money_number})\s*(?P<unit>만원대|만원|만|원대|원)?",
        text,
    )
    if range_match:
        unit = range_match.group("unit") or ""
        has_manwon = "만" in unit or "만" in text[range_match.start() : range_match.end()]
        minimum = _money_to_won(range_match.group("min"), has_manwon)
        maximum = _money_to_won(range_match.group("max"), has_manwon)
        if unit == "만원대":
            maximum += 9999
        if unit == "원대":
            maximum = maximum // 10000 * 10000 + 9999
        return minimum, maximum

    band_match = re.search(rf"(?P<amount>{money_number})\s*(?P<unit>만원대|원대)", text)
    if band_match:
        amount = _money_to_won(band_match.group("amount"), band_match.group("unit") == "만원대")
        if band_match.group("unit") == "만원대":
            amount = amount // 10000 * 10000
        else:
            amount = amount // 10000 * 10000
        return amount, amount + 9999

    if re.search(r"(?<!\d)만원대", text):
        return 10000, 19999

    under_match = re.search(rf"(?P<amount>{money_number})\s*(?P<unit>만원|만|원)\s*(?:이하|미만|안쪽|까지)", text)
    if under_match:
        return None, _money_to_won(under_match.group("amount"), "만" in under_match.group("unit"))

    over_match = re.search(rf"(?P<amount>{money_number})\s*(?P<unit>만원|만|원)\s*(?:이상|부터)", text)
    if over_match:
        return _money_to_won(over_match.group("amount"), "만" in over_match.group("unit")), None

    exact_match = re.search(rf"(?P<amount>{money_number})\s*(?P<unit>만원|만|원)\s*(?:정도|쯤)?", text)
    if exact_match:
        return None, _money_to_won(exact_match.group("amount"), "만" in exact_match.group("unit"))

    exact_won_match = re.search(r"(?<!\d)(?P<amount>\d{1,3}(?:,\d{3})+|\d{5,})(?!\d)", text)
    if exact_won_match:
        return None, _money_to_won(exact_won_match.group("amount"), False)

    return None, None


def _build_conditions(intent: ParsedIntent) -> None:
    if intent.category_label:
        intent.required_conditions.append(f"category:{intent.category_label}")
    for color in intent.colors:
        intent.required_conditions.append(f"color:{color}")
    if intent.price_min is not None or intent.price_max is not None:
        intent.required_conditions.append(f"price:{intent.price_min or ''}-{intent.price_max or ''}")
    if intent.gender:
        intent.preferred_conditions.append(f"gender:{intent.gender}")
    if intent.age_band:
        intent.preferred_conditions.append(f"age_proxy:{intent.age_band}")
    for style in intent.styles:
        if style in {"plain", "basic", "minimal"}:
            intent.required_conditions.append(f"style:{style}")
        else:
            intent.preferred_conditions.append(f"style:{style}")
    for term in intent.specific_terms:
        intent.required_conditions.append(f"item:{term}")
    for term in intent.free_terms:
        intent.required_conditions.append(f"keyword:{term}")
    if "로고" in intent.raw_text and ("없는" in intent.raw_text or "없" in intent.raw_text):
        intent.excluded_conditions.append("visible_logo")
    if "과한" in intent.raw_text or "튀는" in intent.raw_text:
        intent.excluded_conditions.append("flashy_design")


def _generate_keywords(intent: ParsedIntent) -> list[str]:
    free_text = " ".join(intent.free_terms[:4])
    category = intent.category_label or free_text or "상품"
    color_terms = {
        "black": "블랙",
        "white": "화이트",
        "gray": "그레이",
        "charcoal": "차콜",
        "navy": "네이비",
        "blue": "블루",
        "skyblue": "소라",
        "red": "레드",
        "burgundy": "버건디",
        "pink": "핑크",
        "orange": "오렌지",
        "yellow": "옐로우",
        "green": "그린",
        "khaki": "카키",
        "beige": "베이지",
        "brown": "브라운",
        "purple": "퍼플",
        "silver": "실버",
        "gold": "골드",
    }
    gender_terms = {
        "M": "남성",
        "F": "여성",
        "A": "공용",
    }
    style_terms = {
        "plain": "무지",
        "basic": "베이직",
        "minimal": "미니멀",
        "oversized": "오버핏",
        "regular_fit": "레귤러핏",
    }

    color = color_terms.get(intent.colors[0], "") if intent.colors else ""
    gender = gender_terms.get(intent.gender or "", "")
    primary_styles = [style_terms[s] for s in intent.styles if s in style_terms]
    style = " ".join(primary_styles[:2])
    plain_fallback = "무지" if "plain" in intent.styles else ""
    basic_fallback = "기본" if "basic" in intent.styles else ""

    candidates = [
        " ".join(part for part in [color, style, free_text, intent.category_label or ""] if part),
        " ".join(part for part in [color, style, category] if part),
        " ".join(part for part in [color, plain_fallback, category] if part),
        " ".join(part for part in [gender, color, basic_fallback, category] if part),
        " ".join(part for part in [style, category] if part),
        category,
    ]
    return _unique(candidates)


def _confidence(intent: ParsedIntent) -> float:
    score = 0.0
    score += 0.25 if intent.product_group else 0.0
    score += 0.15 if intent.colors else 0.0
    score += 0.15 if intent.styles else 0.0
    score += 0.2 if intent.price_min is not None or intent.price_max is not None else 0.0
    score += 0.1 if intent.gender else 0.0
    score += 0.1 if intent.age_band else 0.0
    score += 0.05 if intent.free_terms else 0.0
    score += 0.05 if intent.generated_keywords else 0.0
    return round(min(score, 1.0), 2)


def parse_purchase_intent(text: str) -> ParsedIntent:
    cleaned = " ".join(text.strip().split())
    product_group, category_label, category_hint = _detect_category(cleaned)
    price_min, price_max = _detect_price_range(cleaned)
    intent = ParsedIntent(
        raw_text=cleaned,
        product_group=product_group,
        category_label=category_label,
        category_hint=category_hint,
        colors=_detect_colors(cleaned),
        styles=_detect_styles(cleaned),
        price_min=price_min,
        price_max=price_max,
        gender=_detect_gender(cleaned),
        age_band=_detect_age_band(cleaned),
        teen_context=_detect_teen_context(cleaned),
        specific_terms=_detect_specific_terms(cleaned, product_group),
        free_terms=_detect_free_terms(cleaned),
    )
    _build_conditions(intent)
    intent.generated_keywords = _generate_keywords(intent)
    intent.confidence = _confidence(intent)
    if intent.age_band:
        intent.notes.append("20대 이상 연령대는 실제 구매자 수가 아니라 공개 랭킹 필터 기반 대체 지표로 사용해야 합니다.")
    if intent.teen_context:
        intent.notes.append("10대/청소년 맥락은 현재 활성 나이 지표가 아니라 추후 확장 가능한 보조 맥락으로만 기록합니다.")
    if not intent.product_group:
        intent.notes.append("상품군이 명확하지 않아 추가 질문이 필요할 수 있습니다.")
    return intent


def parse_to_dict(text: str) -> dict:
    return asdict(parse_purchase_intent(text))


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse Korean Musinsa shopping intent.")
    parser.add_argument("query", help="Natural-language shopping request")
    args = parser.parse_args()
    print(json.dumps(parse_to_dict(args.query), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
