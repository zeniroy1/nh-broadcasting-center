"""Collect public Musinsa product signals and build a buyer-facing app model."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


CURRENT_DIR = Path(__file__).resolve().parent
SRC_ROOT = CURRENT_DIR.parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from musinsa_runtime_paths import resource_path

ALIAS_CONFIG_PATH = resource_path("config", "search_keyword_aliases.json")

from musinsa_intent_parser import parse_to_dict
from musinsa_query_generator import generate_query_candidates
from musinsa_recommendation_output import SAMPLE_CANDIDATES, build_recommendation_report
from musinsa_scoring_model import DEFAULT_QUERY


DEFAULT_RANKING_URL = (
    "https://www.musinsa.com/main/musinsa/ranking?"
    "gf=A&storeCode=musinsa&sectionId=199&contentsId=&categoryCode=000&"
    "ageBand=AGE_BAND_ALL&subPan=product"
)
DEFAULT_SEARCH_URL_TEMPLATE = "https://www.musinsa.com/search/goods?keyword={keyword}"
DEFAULT_SEARCH_API_URL = "https://api.musinsa.com/api2/dp/v1/plp/goods"
USER_AGENT = "Mozilla/5.0 (compatible; MusinsaPublicSignalCollector/0.1; +public-signals)"
PRODUCT_NAME_KEYS = ["productName", "product_name", "goodsName", "goodsNm", "goods_nm", "name", "goodsTitle"]
BRAND_NAME_KEYS = ["brandName", "brand_name", "brand", "brandNm", "brand_nm"]
PRODUCT_ID_KEYS = ["productId", "product_id", "goodsNo", "goodsId", "goods_no", "id"]
PRICE_KEYS = ["salePrice", "finalPrice", "price", "normalPrice", "consumerPrice", "original_price"]
REVIEW_COUNT_KEYS = [
    "reviewCount",
    "reviewCnt",
    "review_count",
    "goodsReviewCount",
    "goodsReviewCnt",
    "totalReviewCount",
    "reviewTotalCount",
    "reviewsCount",
    "commentCount",
    "commentCnt",
    "commentsCount",
    "reviewCountText",
    "reviewCntText",
]
REVIEW_SCORE_KEYS = [
    "reviewScore",
    "reviewPoint",
    "reviewGrade",
    "reviewRating",
    "goodsReviewScore",
    "averageReviewScore",
    "averageRating",
    "avgScore",
    "avgRating",
    "starScore",
    "satisfactionScore",
    "rating",
    "score",
]
RANK_KEYS = [
    "rank",
    "rankNo",
    "ranking",
    "rankingNo",
    "rankingPosition",
    "displayRank",
    "displayRanking",
    "goodsRank",
    "listRank",
    "listIndex",
    "index",
]
SALE_LABEL_KEYS = [
    "saleCount",
    "saleCnt",
    "salesCount",
    "salesCnt",
    "purchaseCount",
    "purchaseCnt",
    "orderCount",
    "orderCnt",
    "accumulatedSales",
    "accumulatedSaleCount",
]
REVIEW_SCORE_DEEP_KEYS = [key for key in REVIEW_SCORE_KEYS if key not in {"score", "rating"}]
RANK_DEEP_KEYS = [key for key in RANK_KEYS if key != "index"]
COLOR_TERM_MAP = {
    "black": ["블랙", "검정", "검은색", "black"],
    "white": ["화이트", "흰색", "하얀색", "백색", "white"],
    "gray": ["그레이", "회색", "라이트그레이", "애쉬", "멜란지", "gray", "grey"],
    "charcoal": ["차콜", "챠콜", "먹색", "다크그레이", "charcoal"],
    "navy": ["네이비", "남색", "곤색", "navy"],
    "blue": ["블루", "파랑", "파란색", "청색", "blue"],
    "skyblue": ["소라", "소라색", "하늘색", "스카이블루", "라이트블루", "sky blue", "skyblue"],
    "red": ["레드", "빨강", "빨간색", "red"],
    "burgundy": ["버건디", "와인", "와인색", "burgundy", "wine"],
    "pink": ["핑크", "분홍", "분홍색", "연핑크", "pink"],
    "orange": ["오렌지", "주황", "주황색", "orange"],
    "yellow": ["옐로우", "노랑", "노란색", "yellow"],
    "green": ["그린", "초록", "초록색", "민트", "민트색", "green", "mint"],
    "khaki": ["카키", "올리브", "올리브그린", "olive", "khaki"],
    "beige": ["베이지", "아이보리", "크림", "오트밀", "샌드", "beige", "ivory", "cream", "oatmeal", "sand"],
    "brown": ["브라운", "갈색", "초코", "초콜릿", "카멜", "camel", "brown", "chocolate"],
    "purple": ["퍼플", "보라", "보라색", "라벤더", "purple", "lavender"],
    "silver": ["실버", "silver"],
    "gold": ["골드", "금색", "gold"],
}
PRODUCT_GROUP_TERMS = {
    "short_sleeve_tshirt": ["티셔츠", "반팔", "반소매", "t-shirt", "tee"],
    "sleeveless_tshirt": ["민소매", "나시", "슬리브리스", "탱크탑", "런닝", "sleeveless", "tank top"],
    "one_piece_dress": ["원피스", "드레스", "롱원피스", "미니원피스", "dress", "one piece"],
    "skirt": ["스커트", "치마", "미니스커트", "롱스커트", "skirt"],
    "short_pants": ["숏 팬츠", "숏팬츠", "반바지", "쇼츠", "shorts", "하프팬츠", "하프 팬츠"],
    "pants": ["바지", "팬츠", "하의", "긴바지"],
    "denim_pants": ["데님", "청바지", "데님 팬츠", "jeans", "denim"],
    "slacks": ["슬랙스", "슈트 팬츠", "수트 팬츠", "트라우저", "trouser"],
    "jogger_pants": ["조거", "조거 팬츠", "트레이닝 팬츠", "트레이닝 바지", "운동복 바지", "스웨트 팬츠", "jogger"],
    "leggings": ["레깅스", "타이즈", "요가팬츠", "leggings", "tights"],
    "outer": ["아우터", "자켓", "재킷", "점퍼", "코트", "바람막이", "윈드브레이커", "블루종"],
    "blazer": ["블레이저", "슈트 재킷", "수트 재킷", "정장 자켓"],
    "cardigan": ["카디건", "가디건", "cardigan"],
    "fleece": ["플리스", "후리스", "fleece"],
    "padding": ["패딩", "다운", "숏패딩", "롱패딩", "puffer", "down"],
    "belt": ["벨트", "belt"],
    "sneakers": ["스니커즈", "운동화", "러닝화", "런닝화", "워킹화", "신발", "슈즈", "sneakers", "running shoes"],
    "boots": ["부츠", "워커", "boots"],
    "sandals_slippers": ["샌들", "샌달", "슬리퍼", "쪼리", "플립플랍", "클로그", "뮬", "슬라이드", "flip flop", "sandals", "slippers", "clog", "mule", "slide"],
    "backpack": ["백팩", "배낭", "backpack"],
    "messenger_cross_bag": ["메신저백", "메신저 백", "크로스백", "크로스 백", "cross bag", "messenger bag"],
    "shoulder_bag": ["숄더백", "숄더 백", "shoulder bag"],
    "tote_bag": ["토트백", "토트 백", "tote bag"],
    "eco_bag": ["에코백", "에코 백", "eco bag"],
    "duffel_bag": ["더플백", "더플 백", "보스턴백", "보스턴 백", "duffel", "boston bag"],
    "cap_hat": ["모자", "볼캡", "캡", "비니", "버킷햇", "hat", "cap"],
    "wallet": ["지갑", "월렛", "wallet"],
    "socks": ["양말", "삭스", "레그웨어", "socks"],
    "sweatshirt": ["맨투맨", "스웨트셔츠", "스웻셔츠", "sweatshirt"],
    "swimwear": ["수영복", "비치웨어", "비키니", "래시가드", "래쉬가드", "스윔웨어", "swimwear", "rash guard"],
}


@dataclass(frozen=True)
class CollectedProduct:
    product_id: str
    product_name: str
    brand_name: str
    price: int | None
    review_count: int | None
    review_score: float | None
    ranking_position: int | None
    sales_label_count: int | None
    product_url: str | None
    image_url: str | None
    source: str


class _ScriptCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._capture = False
        self._current: list[str] = []
        self.scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "script":
            self._capture = True
            self._current = []

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._current.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._capture:
            script = "".join(self._current).strip()
            if script:
                self.scripts.append(script)
            self._capture = False


def _unique_text(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = " ".join(item.split())
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def _load_keyword_aliases(path: Path = ALIAS_CONFIG_PATH) -> dict[str, list[str]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    groups: list[set[str]] = []
    for group in raw.get("aliases", []):
        if not isinstance(group, list):
            continue
        variants = set(_unique_text([str(item).casefold().strip() for item in group if str(item).strip()]))
        if not variants:
            continue
        merged = set(variants)
        remaining: list[set[str]] = []
        for existing in groups:
            if existing & variants:
                merged.update(existing)
            else:
                remaining.append(existing)
        remaining.append(merged)
        groups = remaining
    aliases: dict[str, list[str]] = {}
    for group in groups:
        variants = _unique_text(sorted(group))
        for variant in variants:
            aliases[variant] = variants
    return aliases


KEYWORD_ALIASES = _load_keyword_aliases()

# One-way "umbrella" expansion: a broad category word matches all of its
# sub-items (recall), but a specific item word does NOT expand to its siblings
# (precision). Example: searching "가방" finds 백팩/크로스백 products, while
# searching "백팩" stays limited to backpacks. This complements the separated
# alias groups so broad-term recall is preserved without the old sibling bleed.
UMBRELLA_TERMS = {
    "가방": ["가방", "bag", "백팩", "배낭", "backpack", "크로스백", "메신저백", "cross bag", "messenger bag", "숄더백", "shoulder bag", "토트백", "tote bag", "에코백", "eco bag", "더플백", "보스턴백", "duffel", "boston bag"],
    "신발": ["신발", "슈즈", "shoes", "운동화", "스니커즈", "sneakers", "러닝화", "런닝화", "워킹화", "구두", "부츠", "boots", "샌들", "슬리퍼", "sandals", "slippers"],
    "모자": ["모자", "hat", "cap", "볼캡", "캡", "ball cap", "비니", "beanie", "버킷햇", "bucket hat"],
    "수영복": ["수영복", "비치웨어", "스윔웨어", "swimwear", "비키니", "bikini", "래시가드", "래쉬가드", "rash guard"],
    "스커트": ["스커트", "치마", "skirt", "미니스커트", "mini skirt", "롱스커트", "long skirt"],
    "원피스": ["원피스", "드레스", "dress", "롱원피스", "long dress", "미니원피스", "mini dress"],
}
UMBRELLA_TERMS_CF = {
    key.casefold(): _unique_text([str(member).casefold().strip() for member in members])
    for key, members in UMBRELLA_TERMS.items()
}


def _first_value(item: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in item and item[key] not in (None, ""):
            return item[key]
    return None


def _first_deep_value(value: Any, keys: list[str]) -> Any:
    if isinstance(value, dict):
        found = _first_value(value, keys)
        if found not in (None, ""):
            return found
        for child in value.values():
            found = _first_deep_value(child, keys)
            if found not in (None, ""):
                return found
    elif isinstance(value, list):
        for child in value:
            found = _first_deep_value(child, keys)
            if found not in (None, ""):
                return found
    return None


def _first_direct_then_deep(item: dict[str, Any], direct_keys: list[str], deep_keys: list[str]) -> Any:
    found = _first_value(item, direct_keys)
    if found not in (None, ""):
        return found
    return _first_deep_value(item, deep_keys)


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    digits = re.sub(r"[^\d]", "", str(value))
    return int(digits) if digits else None


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    cleaned = re.sub(r"[^\d.]", "", str(value))
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _to_review_score(value: Any) -> float | None:
    score = _to_float(value)
    if score is None:
        return None
    if 5 < score <= 100:
        return round(score / 20, 2)
    if score > 100:
        return None
    return score


def _absolute_url(value: Any) -> str | None:
    if not value:
        return None
    text = str(value)
    if text.startswith("//"):
        return "https:" + text
    if text.startswith("/"):
        return urllib.parse.urljoin("https://www.musinsa.com", text)
    if text.startswith("http"):
        return text
    return None


def _image_url(value: Any) -> str | None:
    if isinstance(value, dict):
        for key in ["url", "src", "imageUrl", "thumbnail", "img"]:
            url = _absolute_url(value.get(key))
            if url:
                return url
    return _absolute_url(value)


def _flatten_product_card(item: dict[str, Any]) -> dict[str, Any]:
    flattened = dict(item)
    info = item.get("info")
    if isinstance(info, dict):
        flattened.update(info)
    on_click = item.get("onClick")
    if isinstance(on_click, dict):
        flattened.setdefault("url", on_click.get("url"))
        event_log = on_click.get("eventLog")
        if isinstance(event_log, dict):
            amplitude = event_log.get("amplitude")
            payload = amplitude.get("payload") if isinstance(amplitude, dict) else None
            if isinstance(payload, dict):
                flattened.update({key: value for key, value in payload.items() if key not in flattened})
    image = item.get("image")
    if isinstance(image, dict):
        flattened.setdefault("imageUrl", image.get("url"))
        flattened.setdefault("rank", image.get("rank"))
    if "id" in item:
        flattened.setdefault("productId", item.get("id"))
    return flattened


def _looks_like_product(item: dict[str, Any]) -> bool:
    has_name = _first_value(item, PRODUCT_NAME_KEYS) is not None
    has_brand = _first_value(item, BRAND_NAME_KEYS) is not None
    has_price = _first_value(item, PRICE_KEYS) is not None
    has_id = _first_value(item, PRODUCT_ID_KEYS) is not None
    return has_name and (has_brand or has_price or has_id)


def _normalize_product(item: dict[str, Any], source: str) -> CollectedProduct | None:
    item = _flatten_product_card(item)
    if not _looks_like_product(item):
        return None
    product_name = str(_first_value(item, PRODUCT_NAME_KEYS) or "").strip()
    if not product_name:
        return None
    product_id = str(_first_value(item, PRODUCT_ID_KEYS) or product_name).strip()
    brand_name = str(_first_value(item, BRAND_NAME_KEYS) or "브랜드 미확인").strip()
    product_url = _absolute_url(
        item.get("goodsLinkUrl")
        or item.get("goods_link_url")
        or item.get("productLinkUrl")
        or item.get("product_link_url")
        or item.get("productUrl")
        or item.get("goodsUrl")
        or item.get("linkUrl")
        or item.get("url")
        or item.get("href")
    )
    image_url = _image_url(item.get("imageUrl") or item.get("thumbnail") or item.get("image") or item.get("img"))
    return CollectedProduct(
        product_id=product_id,
        product_name=product_name,
        brand_name=brand_name,
        price=_to_int(_first_value(item, PRICE_KEYS)),
        review_count=_to_int(_first_deep_value(item, REVIEW_COUNT_KEYS)),
        review_score=_to_review_score(_first_direct_then_deep(item, REVIEW_SCORE_KEYS, REVIEW_SCORE_DEEP_KEYS)),
        ranking_position=_to_int(_first_direct_then_deep(item, RANK_KEYS, RANK_DEEP_KEYS)),
        sales_label_count=_to_int(_first_deep_value(item, SALE_LABEL_KEYS)),
        product_url=product_url,
        image_url=image_url,
        source=source,
    )


def _walk_products(value: Any, source: str, found: list[CollectedProduct]) -> None:
    if isinstance(value, dict):
        normalized = _normalize_product(value, source)
        if normalized:
            found.append(normalized)
        for child in value.values():
            _walk_products(child, source, found)
    elif isinstance(value, list):
        for child in value:
            _walk_products(child, source, found)


def _json_objects_from_html(raw_html: str) -> list[Any]:
    parser = _ScriptCollector()
    parser.feed(raw_html)
    objects: list[Any] = []
    for script in parser.scripts:
        text = html.unescape(script)
        if not text.startswith(("{", "[")):
            continue
        try:
            objects.append(json.loads(text))
        except json.JSONDecodeError:
            continue
    return objects


def _clean_key_text(value: Any) -> str:
    text = re.sub(r"\[[^\]]+\]\s*", "", str(value or ""))
    return " ".join(text.casefold().split())


def _name_exclude_key(brand_name: Any, product_name: Any) -> str:
    return f"name:{_clean_key_text(brand_name)}:{_clean_key_text(product_name)}"


def _product_key(product: CollectedProduct) -> str:
    name_key = _name_exclude_key(product.brand_name, product.product_name)
    if name_key != "name::" and "미확인" not in product.product_name and "미확인" not in product.brand_name:
        return name_key
    return product.product_id or f"{product.brand_name}:{product.product_name}".strip()


def _exclude_keys_for_product(product: dict[str, Any]) -> set[str]:
    keys = {
        str(product.get("product_id") or ""),
        str(product.get("product_name") or ""),
        _name_exclude_key(product.get("brand_name"), product.get("product_name")),
    }
    return {key for key in keys if key and key != "name::"}


def _product_quality(product: CollectedProduct) -> int:
    fields = [
        product.product_id,
        product.price,
        product.review_count,
        product.review_score,
        product.ranking_position,
        product.sales_label_count,
        product.product_url,
        product.image_url,
    ]
    return sum(1 for field in fields if field not in (None, ""))


def _prefer_text(primary: str, secondary: str) -> str:
    if primary and "미확인" not in primary:
        return primary
    return secondary or primary


def _merge_product(existing: CollectedProduct, incoming: CollectedProduct) -> CollectedProduct:
    return CollectedProduct(
        product_id=existing.product_id or incoming.product_id,
        product_name=_prefer_text(existing.product_name, incoming.product_name),
        brand_name=_prefer_text(existing.brand_name, incoming.brand_name),
        price=existing.price if existing.price is not None else incoming.price,
        review_count=existing.review_count if existing.review_count is not None else incoming.review_count,
        review_score=existing.review_score if existing.review_score is not None else incoming.review_score,
        ranking_position=existing.ranking_position if existing.ranking_position is not None else incoming.ranking_position,
        sales_label_count=existing.sales_label_count if existing.sales_label_count is not None else incoming.sales_label_count,
        product_url=existing.product_url or incoming.product_url,
        image_url=existing.image_url or incoming.image_url,
        source=existing.source if existing.source == incoming.source else f"{existing.source}+{incoming.source}",
    )


def _dedupe_products(found: list[CollectedProduct]) -> list[dict[str, Any]]:
    deduped: dict[str, CollectedProduct] = {}
    for product in found:
        key = _product_key(product)
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = product
        else:
            merged = _merge_product(existing, product)
            deduped[key] = product if _product_quality(product) > _product_quality(merged) else merged
    by_id: dict[str, CollectedProduct] = {}
    for product in deduped.values():
        key = product.product_id or _product_key(product)
        existing = by_id.get(key)
        if existing is None:
            by_id[key] = product
        else:
            by_id[key] = _merge_product(existing, product)
    return [asdict(product) for product in by_id.values()]


def _product_dict_key(product: dict[str, Any]) -> str:
    product_id = str(product.get("product_id") or "").strip()
    if product_id:
        return product_id
    return _name_exclude_key(product.get("brand_name"), product.get("product_name"))


def _product_dict_quality(product: dict[str, Any]) -> int:
    return sum(1 for value in product.values() if value not in (None, ""))


def _dedupe_product_dicts(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for product in products:
        key = _product_dict_key(product)
        existing = deduped.get(key)
        if existing is None or _product_dict_quality(product) > _product_dict_quality(existing):
            deduped[key] = product
    return list(deduped.values())


def _load_public_json(raw_text: str) -> Any | None:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return None


def parse_musinsa_public_products(raw_html: str, source: str = "html") -> list[dict[str, Any]]:
    found: list[CollectedProduct] = []
    for obj in _json_objects_from_html(raw_html):
        _walk_products(obj, source, found)
    return _dedupe_products(found)


def parse_musinsa_public_json(raw_json: str, source: str = "api_json") -> list[dict[str, Any]]:
    obj = _load_public_json(raw_json)
    if obj is None:
        return []
    found: list[CollectedProduct] = []
    _walk_products(obj, source, found)
    return _dedupe_products(found)


def discover_public_ranking_api_urls(raw_html: str) -> list[str]:
    decoded = html.unescape(raw_html).replace("\\u0026", "&")
    urls: list[str] = []
    for match in re.finditer(r"https://(?:api|client)\.musinsa\.com/[^\"'<> ]*ranking[^\"'<> ]*", decoded):
        url = match.group(0)
        if "storeCode=musinsa" not in url:
            continue
        if "subPan=" not in url:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}subPan=product"
        if url not in urls:
            urls.append(url)
    fallback = "https://api.musinsa.com/api2/hm/web/v5/pans/ranking?storeCode=musinsa&subPan=product"
    if fallback not in urls:
        urls.append(fallback)
    return urls[:4]


def _search_url_for_query(query: str) -> str:
    return DEFAULT_SEARCH_URL_TEMPLATE.format(keyword=urllib.parse.quote(query))


def _search_api_url_for_query(query: str, gender: str = "A") -> str:
    params = {
        "keyword": query,
        "gf": gender if gender in {"A", "M", "F"} else "A",
        "page": "1",
        "size": "60",
        "sortCode": "POPULAR",
        "caller": "SEARCH",
    }
    return f"{DEFAULT_SEARCH_API_URL}?{urllib.parse.urlencode(params)}"


def _free_term_variants(term: str) -> list[str]:
    normalized = str(term).casefold().strip()
    if normalized in UMBRELLA_TERMS_CF:
        return UMBRELLA_TERMS_CF[normalized]
    return KEYWORD_ALIASES.get(normalized, [normalized])


def _compact_keyword_text(text: str) -> str:
    return "".join(str(text).casefold().split())


def _expanded_free_term_queries(query_plan: dict[str, Any], limit: int = 6) -> list[str]:
    intent = query_plan.get("parsed_intent") or {}
    terms = [str(term).strip() for term in intent.get("free_terms") or [] if str(term).strip()]
    if not terms:
        return []
    queries = [" ".join(terms)]
    for index, term in enumerate(terms):
        for variant in _free_term_variants(term):
            if variant == term.casefold():
                continue
            expanded = list(terms)
            expanded[index] = variant
            queries.append(" ".join(expanded))
            if len(queries) >= limit:
                return _unique_text(queries)
    return _unique_text(queries)


def _live_search_api_urls(query_plan: dict[str, Any], limit: int = 5) -> list[str]:
    queries: list[str] = []
    intent = query_plan.get("parsed_intent") or {}
    gender = intent.get("gender") or "A"
    for candidate in query_plan.get("candidates", []):
        sources = set(candidate.get("expected_sources") or [])
        if "search_results_page" not in sources:
            continue
        query = str(candidate.get("query") or "").strip()
        if query:
            queries.append(query)
        if len(queries) >= limit:
            break
    queries.extend(_expanded_free_term_queries(query_plan))
    return [_search_api_url_for_query(query, gender) for query in _unique_text(queries)[: limit + 6]]


def _live_search_page_urls(query_plan: dict[str, Any], fallback_url: str, limit: int = 5) -> list[str]:
    queries: list[str] = []
    for candidate in query_plan.get("candidates", []):
        sources = set(candidate.get("expected_sources") or [])
        if "search_results_page" not in sources:
            continue
        query = str(candidate.get("query") or "").strip()
        if query:
            queries.append(query)
        if len(queries) >= limit:
            break
    queries.extend(_expanded_free_term_queries(query_plan))
    urls = [_search_url_for_query(query) for query in _unique_text(queries)[: limit + 6]]
    if fallback_url not in urls:
        urls.append(fallback_url)
    return urls


def fetch_public_html(url: str, timeout: int = 10) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_public_json(url: str, timeout: int = 10) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def _detect_colors(product_name: str, query_colors: list[str]) -> list[str]:
    lowered = product_name.lower()
    colors = list(query_colors)
    for color, terms in COLOR_TERM_MAP.items():
        if any(term.lower() in lowered for term in terms):
            colors.append(color)
    return sorted(set(colors))


def _detect_styles(product_name: str, query_styles: list[str]) -> list[str]:
    styles = list(query_styles)
    if any(term in product_name for term in ["무지", "베이직", "기본", "데일리"]):
        styles.extend(["plain", "basic"])
    if any(term in product_name for term in ["로고", "그래픽", "프린트"]):
        styles.append("graphic")
    return sorted(set(styles))


def _infer_category_label(product_name: str, intent: dict[str, Any]) -> str:
    lowered = product_name.lower()
    product_group = intent.get("product_group")
    if product_group and any(term.lower() in lowered for term in PRODUCT_GROUP_TERMS.get(product_group, [])):
        return intent.get("category_label") or "상품"
    if intent.get("product_group") == "outer" and any(term in lowered for term in ["자켓", "재킷", "점퍼", "가디건"]):
        return intent.get("category_label") or "아우터"
    return "상품"


def _matches_product_group(name: str, product_group: str | None) -> bool:
    if not product_group:
        return True
    terms = PRODUCT_GROUP_TERMS.get(product_group)
    if not terms:
        return True
    lowered = name.lower()
    return any(term.lower() in lowered for term in terms)


def _matches_colors(name: str, colors: list[str]) -> bool:
    if not colors:
        return True
    lowered = name.lower()
    for color in colors:
        terms = COLOR_TERM_MAP.get(color)
        if terms and not any(term.lower() in lowered for term in terms):
            return False
    return True


def _matches_free_terms(product_name: str, free_terms: list[str]) -> bool:
    term_groups = [_free_term_variants(term) for term in free_terms if str(term).strip()]
    if not term_groups:
        return True
    lowered = product_name.casefold()
    compact_lowered = _compact_keyword_text(product_name)
    matched = sum(
        1
        for variants in term_groups
        if any(variant in lowered or _compact_keyword_text(variant) in compact_lowered for variant in variants)
    )
    required = len(term_groups) if len(term_groups) <= 2 else max(2, round(len(term_groups) * 0.6))
    return matched >= required


def _specific_term_variants(term: str) -> list[str]:
    normalized = str(term).casefold().strip()
    return KEYWORD_ALIASES.get(normalized, [normalized])


def _matches_specific_term(product_name: str, term: str) -> bool:
    lowered = product_name.casefold()
    compact_lowered = _compact_keyword_text(product_name)
    return any(
        variant in lowered or _compact_keyword_text(variant) in compact_lowered
        for variant in _specific_term_variants(term)
    )


def _specific_term_match_count(product: dict[str, Any], intent: dict[str, Any]) -> int:
    specific_terms = [str(term).strip() for term in intent.get("specific_terms") or [] if str(term).strip()]
    if not specific_terms:
        return 0
    name = str(product.get("product_name") or "")
    return sum(1 for term in specific_terms if _matches_specific_term(name, term))


def _specific_match_priority(product: dict[str, Any], intent: dict[str, Any]) -> int:
    specific_terms = [str(term).strip() for term in intent.get("specific_terms") or [] if str(term).strip()]
    if not specific_terms:
        return 0
    matched_count = _specific_term_match_count(product, intent)
    if matched_count >= len(specific_terms):
        return 2
    if matched_count:
        return 1
    return 0


def _sort_by_specific_terms(products: list[dict[str, Any]], intent: dict[str, Any]) -> list[dict[str, Any]]:
    if not intent.get("specific_terms"):
        return list(products)
    return sorted(
        products,
        key=lambda product: (
            _specific_match_priority(product, intent),
            _specific_term_match_count(product, intent),
            -(product.get("ranking_position") or 999999),
            product.get("review_count") or 0,
        ),
        reverse=True,
    )


def _matches_intent_gate(product: dict[str, Any], intent: dict[str, Any]) -> bool:
    price = product.get("price")
    if not _matches_core_gate(product, intent):
        return False
    if price is not None and intent.get("price_max") is not None:
        if price > int(intent["price_max"]):
            return False
    if price is not None and intent.get("price_min") is not None:
        if price < int(intent["price_min"]):
            return False
    return True


def _matches_relaxed_similarity_gate(product: dict[str, Any], intent: dict[str, Any]) -> bool:
    """Allow Musinsa search-result products when the exact keyword is a style/brand proxy."""
    source = str(product.get("source") or "")
    if "live_search_api_json" not in source:
        return False
    if not intent.get("free_terms"):
        return False
    if intent.get("product_group") and not _matches_product_group(str(product.get("product_name") or ""), intent.get("product_group")):
        return False
    if not _matches_colors(str(product.get("product_name") or ""), intent.get("colors") or []):
        return False
    if not _price_matches_intent(product, intent):
        return False
    name = str(product.get("product_name") or "").lower()
    if "plain" in (intent.get("styles") or []):
        if any(term in name for term in ["프린트", "그래픽", "로고", "패턴", "아트웍", "artwork", "graphic", "logo"]):
            return False
    return True


def _similar_search_products(products: list[dict[str, Any]], intent: dict[str, Any]) -> list[dict[str, Any]]:
    if not intent.get("free_terms"):
        return []
    return [
        {**product, "source": f"{product.get('source', 'public_json')}+similar_keyword"}
        for product in products
        if _matches_relaxed_similarity_gate(product, intent)
    ]


def _matches_core_gate(product: dict[str, Any], intent: dict[str, Any]) -> bool:
    name = str(product.get("product_name") or "")
    searchable_name = " ".join(part for part in [name, str(product.get("brand_name") or "")] if part)
    lowered = name.lower()
    if not _matches_free_terms(searchable_name, intent.get("free_terms") or []):
        return False
    if not _matches_product_group(name, intent.get("product_group")):
        return False
    if not _matches_colors(name, intent.get("colors") or []):
        return False
    if "plain" in (intent.get("styles") or []):
        if any(term in lowered for term in ["프린트", "그래픽", "로고", "패턴", "아트웍", "artwork", "graphic", "logo"]):
            return False
    return True


def _price_matches_intent(product: dict[str, Any], intent: dict[str, Any]) -> bool:
    price = product.get("price")
    if price is None:
        return True
    if intent.get("price_max") is not None and price > int(intent["price_max"]):
        return False
    if intent.get("price_min") is not None and price < int(intent["price_min"]):
        return False
    return True


def _compact_free_term_match(text: str, free_terms: list[str]) -> bool:
    compact_text = _compact_keyword_text(text)
    if not compact_text:
        return False
    for term in free_terms:
        variants = _free_term_variants(term)
        if any(_compact_keyword_text(variant) in compact_text for variant in variants):
            return True
    return False


def _is_reliable_product(product: dict[str, Any]) -> bool:
    """A usable candidate must have at least a known brand or a known price.

    Name-mention-only matches with unknown brand AND unknown price (e.g. resale/
    reference listings for a non-partner brand) are treated as low quality and
    excluded, so a brand that is not officially on Musinsa yields a clear
    "not found" result instead of a junk candidate.
    """
    brand = str(product.get("brand_name") or "")
    brand_known = bool(brand) and "미확인" not in brand
    price_known = product.get("price") is not None
    return brand_known or price_known


def build_search_diagnostics(
    products: list[dict[str, Any]],
    filtered_products: list[dict[str, Any]],
    intent: dict[str, Any],
    scored_count: int,
    similar_products: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    free_terms = [str(term).strip() for term in intent.get("free_terms") or [] if str(term).strip()]
    similar_products = similar_products or []
    brand_only_matches = 0
    spacing_adjusted_matches = 0
    core_matches = 0
    reliable_core_matches = 0
    price_filtered = 0
    category_filtered = 0
    color_filtered = 0
    sample_rejected: list[dict[str, Any]] = []

    for product in products:
        name = str(product.get("product_name") or "")
        brand = str(product.get("brand_name") or "")
        searchable = " ".join(part for part in [name, brand] if part)
        name_free_match = _matches_free_terms(name, free_terms)
        brand_free_match = _matches_free_terms(brand, free_terms)
        combined_free_match = _matches_free_terms(searchable, free_terms)
        if free_terms and brand_free_match and not name_free_match:
            brand_only_matches += 1
        if free_terms and not any(term.casefold() in searchable.casefold() for term in free_terms) and _compact_free_term_match(searchable, free_terms):
            spacing_adjusted_matches += 1
        if _matches_core_gate(product, intent):
            core_matches += 1
            if _is_reliable_product(product):
                reliable_core_matches += 1
            if not _price_matches_intent(product, intent):
                price_filtered += 1
        elif combined_free_match and not _matches_product_group(name, intent.get("product_group")):
            category_filtered += 1
        elif combined_free_match and not _matches_colors(name, intent.get("colors") or []):
            color_filtered += 1
        if combined_free_match and len(sample_rejected) < 5 and product not in filtered_products:
            sample_rejected.append(
                {
                    "brand": brand or "브랜드 미확인",
                    "product": name,
                    "price": product.get("price"),
                }
            )

    issues: list[dict[str, Any]] = []
    if not products:
        query_terms = [
            str(term).strip()
            for term in ((intent.get("specific_terms") or []) + (intent.get("free_terms") or []))
            if str(term).strip()
        ]
        query_label = " ".join(dict.fromkeys(query_terms)) if query_terms else "입력한 검색어"
        issues.append(
            {
                "type": "no_public_products",
                "title": "무신사 공개 카탈로그 결과 없음",
                "detail": (
                    f"'{query_label}' 검색이 무신사 공개 상품 API에서 0건입니다. "
                    "이 경우 (1) 철자/띄어쓰기 오류, (2) 일시적 네트워크 실패, "
                    "(3) 해당 브랜드가 무신사에 공식 입점하지 않은(미입점) 경우일 수 있습니다. "
                    "미입점 브랜드는 무신사 공개 검색에서 확인되지 않으므로 결과가 나오지 않습니다."
                ),
                "suggestion": "브랜드 철자를 확인하고, 그래도 결과가 없으면 무신사에 실제 판매되는 브랜드/상품군으로 검색해 보세요.",
            }
        )
    elif not filtered_products and similar_products:
        issues.append(
            {
                "type": "similar_keyword_fallback",
                "title": "유사 검색 후보 사용",
                "detail": f"정확 키워드 일치 상품은 없지만 무신사 검색 결과 {len(similar_products)}개를 유사 후보로 사용했습니다.",
                "suggestion": "브랜드 공식 상품 여부는 상품명/브랜드명을 직접 확인하고, 필요하면 상품군/가격/색상을 추가해 좁혀 보세요.",
            }
        )
    elif not filtered_products:
        query_terms = [
            str(term).strip()
            for term in ((intent.get("specific_terms") or []) + (intent.get("free_terms") or []))
            if str(term).strip()
        ]
        query_label = " ".join(dict.fromkeys(query_terms))
        if query_terms and reliable_core_matches == 0:
            issues.append(
                {
                    "type": "keyword_not_found",
                    "title": "검색어와 일치하는 정식 상품 없음",
                    "detail": (
                        f"'{query_label}'에 대해 브랜드·가격 정보가 있는 정식 상품을 찾지 못했습니다. "
                        "(검색어가 상품명에만 들어간 불완전 매칭은 제외했습니다.) "
                        "철자 오류가 아니라면, 해당 브랜드가 무신사에 공식 입점하지 않은(미입점) 경우일 수 있습니다."
                    ),
                    "suggestion": "브랜드 철자를 확인하고, 그래도 없으면 무신사에 실제 판매되는 브랜드/상품군으로 검색해 보세요. 미입점 브랜드는 무신사 공개 검색에서 확인되지 않습니다.",
                }
            )
        else:
            issues.append(
                {
                    "type": "all_filtered_out",
                    "title": "수집 후 필터 전부 탈락",
                    "detail": f"공개 상품 {len(products)}개를 수집했지만 현재 조건을 통과한 상품이 없습니다.",
                    "suggestion": "브랜드명, 상품군, 색상, 가격 조건 중 어떤 조건이 과한지 확인해야 합니다.",
                }
            )
    elif len(filtered_products) < min(5, len(products)):
        issues.append(
            {
                "type": "narrow_filter",
                "title": "필터 통과 후보 적음",
                "detail": f"공개 상품 {len(products)}개 중 {len(filtered_products)}개만 조건을 통과했습니다.",
                "suggestion": "후보가 적으면 가격대나 상품군 조건을 넓히면 비교 폭이 커집니다.",
            }
        )
    if brand_only_matches:
        issues.append(
            {
                "type": "brand_name_match",
                "title": "브랜드명 중심 검색어 감지",
                "detail": f"{brand_only_matches}개 상품은 검색어가 상품명보다 브랜드명에서 확인됐습니다.",
                "suggestion": "브랜드명+상품명 통합 매칭을 적용해 후보 탈락을 줄입니다.",
            }
        )
    if spacing_adjusted_matches:
        issues.append(
            {
                "type": "spacing_difference",
                "title": "띄어쓰기 차이 감지",
                "detail": f"{spacing_adjusted_matches}개 상품은 띄어쓰기 제거 비교에서만 검색어가 확인됐습니다.",
                "suggestion": "붙여쓰기/띄어쓰기 차이는 같은 키워드로 처리합니다.",
            }
        )
    if price_filtered:
        issues.append(
            {
                "type": "price_filtered",
                "title": "가격 조건 탈락",
                "detail": f"{price_filtered}개 상품은 핵심 키워드는 맞지만 가격 조건에서 제외됐습니다.",
                "suggestion": "가격대를 자연어로 조금 넓게 입력하면 후보가 늘어납니다.",
            }
        )
    if category_filtered:
        issues.append(
            {
                "type": "category_filtered",
                "title": "상품군 조건 탈락",
                "detail": f"{category_filtered}개 상품은 키워드는 맞지만 요구한 상품군과 달랐습니다.",
                "suggestion": "브랜드 전체 탐색인지 특정 상품군 탐색인지 검색어에 함께 적어 주세요.",
            }
        )
    if color_filtered:
        issues.append(
            {
                "type": "color_filtered",
                "title": "색상 조건 탈락",
                "detail": f"{color_filtered}개 상품은 키워드는 맞지만 색상 조건과 맞지 않았습니다.",
                "suggestion": "색상 조건을 빼고 먼저 브랜드/상품군을 좁힌 뒤 다시 비교할 수 있습니다.",
            }
        )
    return {
        "status": "pass" if filtered_products else ("no_public_products" if not products else "needs_attention"),
        "counts": {
            "collected": len(products),
            "filtered": len(filtered_products),
            "scored": scored_count,
            "core_matches": core_matches,
            "brand_only_matches": brand_only_matches,
            "spacing_adjusted_matches": spacing_adjusted_matches,
            "price_filtered": price_filtered,
            "category_filtered": category_filtered,
            "color_filtered": color_filtered,
            "similar_candidates": len(similar_products),
        },
        "issues": issues,
        "sample_rejected": sample_rejected,
    }


def _public_issue_ratios(review_count: int | None, review_score: float | None, rank: int | None) -> dict[str, float]:
    count = review_count or 0
    score = float(review_score or 0)
    score_gap = max(0.0, 4.8 - score) if score else 0.7
    sparse_penalty = 0.08 if count < 50 else 0.04 if count < 300 else 0.0
    rank_penalty = 0.04 if rank is None or rank > 100 else 0.02 if rank > 50 else 0.0
    low_rating = min(0.45, max(0.04, 0.08 + (score_gap * 0.14) + sparse_penalty))
    fit = min(0.38, max(0.07, 0.11 + (score_gap * 0.08) + rank_penalty))
    material = min(0.38, max(0.07, 0.1 + (score_gap * 0.09) + sparse_penalty))
    return {
        "low_rating_issue_ratio": round(low_rating, 3),
        "fit_issue_ratio": round(fit, 3),
        "material_issue_ratio": round(material, 3),
    }


def _score_ready_product(product: dict[str, Any], intent: dict[str, Any]) -> dict[str, Any]:
    name = product.get("product_name", "")
    rank = product.get("ranking_position")
    review_count = product.get("review_count")
    review_score = product.get("review_score")
    issue_ratios = _public_issue_ratios(review_count, review_score, rank)
    return {
        "product_id": str(product.get("product_id") or name),
        "product_name": name,
        "brand_name": product.get("brand_name") or "브랜드 미확인",
        "category_label": _infer_category_label(name, intent),
        "colors": _detect_colors(name, intent.get("colors") or []),
        "styles": _detect_styles(name, intent.get("styles") or []),
        "price": product.get("price"),
        "gender": intent.get("gender") or "A",
        "male_ranking_position": rank if intent.get("gender") == "M" else None,
        "age_40s_ranking_position": rank if intent.get("age_band") == "40s" else None,
        "review_count": review_count or 0,
        "review_score": review_score or 0,
        "sales_label_count": product.get("sales_label_count") or 0,
        "ranking_position": rank,
        "plus_delivery": None,
        "is_ad": False,
        "is_sold_out": False,
        "low_rating_issue_ratio": issue_ratios["low_rating_issue_ratio"],
        "fit_issue_ratio": issue_ratios["fit_issue_ratio"],
        "material_issue_ratio": issue_ratios["material_issue_ratio"],
        "repurchase_keyword_count": 0,
        "flashy_design": "graphic" in _detect_styles(name, []),
        "product_url": product.get("product_url"),
        "image_url": product.get("image_url"),
        "source": product.get("source", "public_html"),
        "specific_match_priority": _specific_match_priority(product, intent),
        "specific_term_match_count": _specific_term_match_count(product, intent),
    }


def _with_sample_fillers(
    products: list[dict[str, Any]],
    minimum: int = 5,
    exclude_product_ids: set[str] | None = None,
    intent: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    result = list(products)
    has_public_products = bool(result)
    excluded = exclude_product_ids or set()
    seen = {item.get("product_id") for item in result}
    for sample in SAMPLE_CANDIDATES:
        if len(result) >= minimum:
            break
        if intent and not _matches_intent_gate(sample, intent):
            continue
        if sample.get("product_id") not in seen and not (_exclude_keys_for_product(sample) & excluded):
            filler = {**sample, "source": "sample_fallback"}
            if has_public_products:
                filler["is_sold_out"] = True
                filler["review_count"] = 0
                filler["review_score"] = 0
                filler["sales_label_count"] = 0
                filler["ranking_position"] = None
                filler["male_ranking_position"] = None
                filler["age_40s_ranking_position"] = None
            result.append(filler)
            seen.add(sample.get("product_id"))
    return result


def _requires_strict_candidate_match(intent: dict[str, Any]) -> bool:
    return bool(intent.get("free_terms") or intent.get("product_group") or intent.get("colors"))


def build_buyer_app_model(
    query: str = DEFAULT_QUERY,
    raw_html: str | None = None,
    fetch_live: bool = False,
    url: str = DEFAULT_RANKING_URL,
    exclude_product_ids: list[str] | None = None,
) -> dict[str, Any]:
    intent = parse_to_dict(query)
    query_plan = generate_query_candidates(query)
    collection_errors: list[str] = []
    api_urls_tried: list[str] = []
    html_urls_tried: list[str] = []
    html_source = raw_html
    collection_mode = "sample_fallback"
    public_products: list[dict[str, Any]] = []
    if html_source is None and fetch_live:
        for api_url in _live_search_api_urls(query_plan):
            api_urls_tried.append(api_url)
            try:
                api_json = fetch_public_json(api_url)
                public_products.extend(parse_musinsa_public_json(api_json, "live_search_api_json"))
            except Exception as exc:  # pragma: no cover - network dependent
                collection_errors.append(f"search_api_fetch_failed: {api_url}: {exc}")
        for fetch_url in _live_search_page_urls(query_plan, url):
            html_urls_tried.append(fetch_url)
            try:
                fetched_html = fetch_public_html(fetch_url)
            except Exception as exc:  # pragma: no cover - network dependent
                collection_errors.append(f"live_fetch_failed: {fetch_url}: {exc}")
                continue
            page_products = parse_musinsa_public_products(fetched_html, f"live_html:{fetch_url}")
            public_products.extend(page_products)
            if not page_products and "ranking" in fetch_url:
                for api_url in discover_public_ranking_api_urls(fetched_html):
                    api_urls_tried.append(api_url)
                    try:
                        api_json = fetch_public_json(api_url)
                        public_products.extend(parse_musinsa_public_json(api_json, "live_api_json"))
                    except Exception as exc:  # pragma: no cover - network dependent
                        collection_errors.append(f"api_fetch_failed: {api_url}: {exc}")
        public_products = _dedupe_product_dicts(public_products)
        collection_mode = "live_search_fetch" if public_products else "live_fetch_no_products_fallback"
    elif html_source is not None:
        collection_mode = "html_input"
        public_products = parse_musinsa_public_products(html_source, collection_mode)

    if fetch_live and html_source and not public_products:
        for api_url in discover_public_ranking_api_urls(html_source):
            api_urls_tried.append(api_url)
            try:
                api_json = fetch_public_json(api_url)
                public_products = parse_musinsa_public_json(api_json, "live_api_json")
            except Exception as exc:  # pragma: no cover - network dependent
                collection_errors.append(f"api_fetch_failed: {api_url}: {exc}")
            if public_products:
                collection_mode = "live_api_json"
                break
        if not public_products:
            collection_mode = "live_fetch_no_products_fallback"
    excluded = set(exclude_product_ids or [])
    filtered_products = _sort_by_specific_terms(
        [product for product in public_products if _matches_intent_gate(product, intent) and _is_reliable_product(product)],
        intent,
    )
    similar_products = (
        [product for product in _similar_search_products(public_products, intent) if _is_reliable_product(product)]
        if not filtered_products
        else []
    )
    primary_source = filtered_products if filtered_products else (
        similar_products if similar_products else ([] if _requires_strict_candidate_match(intent) else public_products)
    )
    source_for_scoring = _sort_by_specific_terms(
        [product for product in primary_source if not (_exclude_keys_for_product(product) & excluded)],
        intent,
    )
    if filtered_products and len(source_for_scoring) < 5:
        source_for_scoring.extend(
            product
            for product in public_products
            if product not in source_for_scoring
            and _matches_intent_gate(product, intent)
            and _is_reliable_product(product)
            and not (_exclude_keys_for_product(product) & excluded)
        )
    score_ready = [_score_ready_product(product, intent) for product in source_for_scoring]
    if not (excluded and public_products):
        score_ready = _with_sample_fillers(score_ready, 5, excluded, intent)
    report = build_recommendation_report(query=query, candidates=score_ready, max_candidates=5)
    search_diagnostics = build_search_diagnostics(public_products, filtered_products, intent, len(score_ready[:5]), similar_products)
    return {
        "query": query,
        "collection_mode": collection_mode,
        "source_url": url,
        "html_urls_tried": html_urls_tried,
        "api_urls_tried": api_urls_tried,
        "collection_errors": collection_errors,
        "parsed_intent": intent,
        "query_plan": query_plan,
        "collected_public_product_count": len(public_products),
        "filtered_public_product_count": len(filtered_products),
        "excluded_product_ids": sorted(excluded),
        "scored_candidate_count": len(score_ready[:5]),
        "search_diagnostics": search_diagnostics,
        "recommendation_report": report,
        "workflow": [
            "구매 의도 입력",
            "검색어 후보 생성",
            "무신사 공개 HTML/JSON 신호 수집",
            "상품 후보 정규화",
            "공개/대체/추정 지표 점수화",
            "5개 후보 비교",
            "3개 후보 shortlist 세부 비교",
        ],
        "collection_boundaries": [
            "수집기는 공개 HTML/JSON에 노출된 상품명, 브랜드, 가격, 리뷰 수, 평점, 랭킹 위치만 사용한다.",
            "실제 구매자 수, 실제 판매량, 성별/연령별 전환율, 내부 랭킹 알고리즘은 수집 대상이 아니다.",
            "라이브 수집 실패 시 샘플 데이터로 UI와 점수화 흐름을 확인한다.",
        ],
    }


def validate_buyer_app_model() -> list[str]:
    errors: list[str] = []
    fixture = """
    <html><body><script id="__NEXT_DATA__" type="application/json">
    {"props":{"pageProps":{"products":[
      {"goodsNo":"1001","goodsName":"베이직 무지 반팔 티셔츠 블랙","brandName":"테스트브랜드","salePrice":"29,900","reviewCount":"1200","reviewScore":4.8,"rank":1},
      {"goodsNo":"1002","goodsName":"그래픽 로고 반팔 티셔츠 블랙","brandName":"테스트그래픽","salePrice":"32,900","reviewCount":"300","reviewScore":4.1,"rank":2},
      {"goodsNo":"1003","goodsName":"원턱 트랙 팬츠 블랙","brandName":"테스트팬츠","salePrice":"35,900","reviewCount":"400","reviewScore":4.4,"rank":3}
    ]}}}
    </script></body></html>
    """
    products = parse_musinsa_public_products(fixture)
    api_fixture = '{"data":{"goods":[{"product_id":"2001","product_name":"API 무지 반팔 티셔츠 블랙","brand_name":"API브랜드","price":"25000","reviewCount":"77","reviewScore":"4.6","index":"3"}]}}'
    api_products = parse_musinsa_public_json(api_fixture)
    if len(products) != 3:
        errors.append("fixture must parse three public products")
    if len(api_products) != 1:
        errors.append("api fixture must parse one public product")
    model = build_buyer_app_model(raw_html=fixture)
    if model["collection_mode"] != "html_input":
        errors.append("raw html input must set html_input mode")
    if model["collected_public_product_count"] != 3:
        errors.append("model must expose collected public product count")
    if model["filtered_public_product_count"] != 1:
        errors.append("model must filter non-matching public products before scoring")
    report = model["recommendation_report"]
    if report["recommendation_count"] != 5:
        errors.append("buyer app must compare five candidates")
    if report["shortlist_detail"]["selected_count"] != 3:
        errors.append("buyer app must expose three shortlist detail panels")
    if not any("실제 구매자 수" in boundary for boundary in model["collection_boundaries"]):
        errors.append("buyer app must keep internal data boundary")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Musinsa buyer-facing public-signal app model.")
    parser.add_argument("--query", default=DEFAULT_QUERY, help="Natural-language shopping request")
    parser.add_argument("--url", default=DEFAULT_RANKING_URL, help="Musinsa public page URL")
    parser.add_argument("--html-file", help="Saved Musinsa HTML file to parse")
    parser.add_argument("--fetch-live", action="store_true", help="Fetch the public Musinsa page over the network")
    parser.add_argument("--validate", action="store_true", help="Validate app model")
    args = parser.parse_args()

    if args.validate:
        errors = validate_buyer_app_model()
        print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
        raise SystemExit(1 if errors else 0)

    raw_html = Path(args.html_file).read_text(encoding="utf-8") if args.html_file else None
    model = build_buyer_app_model(args.query, raw_html=raw_html, fetch_live=args.fetch_live, url=args.url)
    print(json.dumps(model, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
