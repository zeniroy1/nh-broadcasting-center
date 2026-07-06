"""Map public Musinsa signals into proxy metric scores with confidence."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from musinsa_intent_parser import CATEGORY_KEYWORDS, parse_to_dict
from musinsa_signal_catalog import get_signals, validate_catalog


@dataclass(frozen=True)
class ProxyMetricDefinition:
    key: str
    label: str
    inputs: list[str]
    weights: dict[str, float]
    confidence_inputs: list[str]
    confidence_ceiling: int
    limitations: list[str]


@dataclass
class MetricResult:
    key: str
    label: str
    score: int
    confidence_percent: int
    confidence_level: str
    evidence: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


PROXY_METRICS = [
    ProxyMetricDefinition(
        key="purpose_fit_score",
        label="목적 적합도",
        inputs=["category_match", "color_match", "style_match", "price_match", "gender_match"],
        weights={"category_match": 25, "color_match": 20, "style_match": 20, "price_match": 25, "gender_match": 10},
        confidence_inputs=["category_match", "color_match", "style_match", "price_match"],
        confidence_ceiling=95,
        limitations=["사용자 취향 전체를 알 수 없으므로 조건 일치 기반 추정이다."],
    ),
    ProxyMetricDefinition(
        key="age_male_40s_fit_score",
        label="40대 남성 적합도 추정",
        inputs=[
            "male_ranking_exposed",
            "age_40s_ranking_exposed",
            "basic_style_signal",
            "review_volume_signal",
            "review_score_signal",
            "not_flashy_signal",
        ],
        weights={
            "male_ranking_exposed": 20,
            "age_40s_ranking_exposed": 25,
            "basic_style_signal": 20,
            "review_volume_signal": 15,
            "review_score_signal": 10,
            "not_flashy_signal": 10,
        },
        confidence_inputs=["male_ranking_exposed", "age_40s_ranking_exposed", "review_volume_signal", "review_score_signal"],
        confidence_ceiling=85,
        limitations=["실제 40대 남성 구매자 수는 공개되지 않는다."],
    ),
    ProxyMetricDefinition(
        key="purchase_trust_score",
        label="구매 신뢰도 추정",
        inputs=["review_volume_signal", "review_score_signal", "sales_label_signal", "ranking_signal", "delivery_signal"],
        weights={
            "review_volume_signal": 30,
            "review_score_signal": 25,
            "sales_label_signal": 20,
            "ranking_signal": 15,
            "delivery_signal": 10,
        },
        confidence_inputs=["review_volume_signal", "review_score_signal", "sales_label_signal", "ranking_signal"],
        confidence_ceiling=88,
        limitations=["실제 구매 전환율과 누적 구매자 원본 데이터는 공개되지 않는다."],
    ),
    ProxyMetricDefinition(
        key="review_purchase_evidence_score",
        label="리뷰 기반 구매 반응 누적 근거",
        inputs=["review_volume_signal", "review_score_signal", "ranking_signal", "sales_label_signal"],
        weights={
            "review_volume_signal": 45,
            "review_score_signal": 20,
            "ranking_signal": 20,
            "sales_label_signal": 15,
        },
        confidence_inputs=["review_volume_signal", "review_score_signal", "ranking_signal"],
        confidence_ceiling=86,
        limitations=[
            "리뷰 수는 구매 후 반응 누적량의 강한 공개 단서지만 실제 구매자 수나 판매량은 아니다.",
            "리뷰 작성률을 알 수 없으므로 구매 규모의 방향성을 보는 대체 지표로만 사용한다.",
        ],
    ),
    ProxyMetricDefinition(
        key="return_risk_score",
        label="반품 리스크 낮음 추정",
        inputs=["low_issue_signal", "fit_issue_signal", "material_issue_signal", "review_volume_signal"],
        weights={"low_issue_signal": 35, "fit_issue_signal": 25, "material_issue_signal": 25, "review_volume_signal": 15},
        confidence_inputs=["low_issue_signal", "fit_issue_signal", "material_issue_signal", "review_volume_signal"],
        confidence_ceiling=75,
        limitations=["실제 반품률은 공개되지 않으며 리뷰 기반 리스크 추정이다."],
    ),
    ProxyMetricDefinition(
        key="repurchase_likelihood_score",
        label="재구매 가능성 추정",
        inputs=["repurchase_keyword_signal", "review_volume_signal", "review_score_signal", "basic_style_signal"],
        weights={
            "repurchase_keyword_signal": 35,
            "review_volume_signal": 20,
            "review_score_signal": 25,
            "basic_style_signal": 20,
        },
        confidence_inputs=["repurchase_keyword_signal", "review_volume_signal", "review_score_signal"],
        confidence_ceiling=72,
        limitations=["실제 재구매율이 아니라 리뷰 키워드와 만족도 기반 추정이다."],
    ),
]


SAMPLE_PRODUCT = {
    "product_id": "sample-black-tee",
    "product_name": "베이직 무지 반팔 티셔츠 블랙",
    "brand_name": "샘플 브랜드",
    "category_label": "반팔 티셔츠",
    "colors": ["black"],
    "styles": ["plain", "basic"],
    "price": 29900,
    "gender": "M",
    "male_ranking_position": 18,
    "age_40s_ranking_position": 24,
    "review_count": 8200,
    "review_score": 4.8,
    "sales_label_count": 50000,
    "ranking_position": 18,
    "plus_delivery": True,
    "low_rating_issue_ratio": 0.08,
    "fit_issue_ratio": 0.12,
    "material_issue_ratio": 0.1,
    "repurchase_keyword_count": 37,
    "flashy_design": False,
}


def _canonical_category_label(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    compact_text = re.sub(r"\s+", "", text).lower()
    for category in CATEGORY_KEYWORDS.values():
        label = str(category.get("label") or "").strip()
        aliases = [label]
        aliases.extend(str(keyword).strip() for keyword in category.get("keywords", []) if str(keyword).strip())
        aliases.extend(str(term).strip() for term in category.get("search_terms", []) if str(term).strip())
        for alias in aliases:
            if text == alias or compact_text == re.sub(r"\s+", "", alias).lower():
                return label
    return text


def confidence_level(confidence_percent: int) -> str:
    if confidence_percent >= 90:
        return "very_high"
    if confidence_percent >= 70:
        return "high"
    if confidence_percent >= 50:
        return "medium"
    if confidence_percent >= 30:
        return "low"
    return "very_low"


def clamp_score(value: float) -> int:
    return int(round(max(0, min(100, value))))


def _price_match(intent: dict[str, Any], product: dict[str, Any]) -> float | None:
    price = product.get("price")
    if price is None:
        return None
    price_min = intent.get("price_min")
    price_max = intent.get("price_max")
    if price_min is not None and price < price_min:
        return max(0.0, 1 - ((price_min - price) / max(price_min, 1)))
    if price_max is not None and price > price_max:
        return max(0.0, 1 - ((price - price_max) / max(price_max, 1)))
    return 1.0


def _ranking_signal(position: int | None, excellent: int = 20, acceptable: int = 100) -> float | None:
    if position is None:
        return None
    if position <= excellent:
        return 1.0
    if position > acceptable:
        return 0.25
    return max(0.25, 1 - ((position - excellent) / (acceptable - excellent)) * 0.75)


def _review_volume_signal(review_count: int | None) -> float | None:
    if review_count is None:
        return None
    if review_count >= 5000:
        return 1.0
    if review_count >= 1000:
        return 0.85
    if review_count >= 300:
        return 0.65
    if review_count >= 50:
        return 0.4
    return 0.2


def _review_score_signal(review_score: float | None) -> float | None:
    if review_score is None:
        return None
    if review_score >= 4.8:
        return 1.0
    if review_score >= 4.5:
        return 0.85
    if review_score >= 4.0:
        return 0.65
    if review_score >= 3.5:
        return 0.4
    return 0.2


def _sales_label_signal(sales_count: int | None) -> float | None:
    if sales_count is None:
        return None
    if sales_count >= 100000:
        return 1.0
    if sales_count >= 10000:
        return 0.85
    if sales_count >= 1000:
        return 0.65
    if sales_count >= 100:
        return 0.45
    return 0.2


def _inverse_issue_signal(issue_ratio: float | None) -> float | None:
    if issue_ratio is None:
        return None
    return max(0.0, min(1.0, 1 - issue_ratio))


def _repurchase_signal(count: int | None, review_count: int | None) -> float | None:
    if count is None:
        return None
    if review_count is None or review_count <= 0:
        return min(1.0, count / 20)
    ratio = count / review_count
    if ratio >= 0.01:
        return 1.0
    if ratio >= 0.005:
        return 0.8
    if ratio >= 0.002:
        return 0.6
    if count > 0:
        return 0.4
    return 0.0


def derive_evidence(intent: dict[str, Any], product: dict[str, Any]) -> dict[str, float | None]:
    product_styles = set(product.get("styles", []))
    intent_styles = set(intent.get("styles", []))
    product_colors = set(product.get("colors", []))
    intent_colors = set(intent.get("colors", []))
    review_count = product.get("review_count")
    review_score = product.get("review_score")

    product_category = _canonical_category_label(product.get("category_label"))
    intent_category = _canonical_category_label(intent.get("category_label"))

    return {
        "category_match": 1.0 if product_category and product_category == intent_category else None,
        "color_match": 1.0 if intent_colors and intent_colors.issubset(product_colors) else None,
        "style_match": 1.0 if intent_styles and intent_styles.intersection(product_styles) else None,
        "price_match": _price_match(intent, product),
        "gender_match": 1.0 if intent.get("gender") and product.get("gender") == intent.get("gender") else None,
        "male_ranking_exposed": _ranking_signal(product.get("male_ranking_position")),
        "age_40s_ranking_exposed": _ranking_signal(product.get("age_40s_ranking_position")),
        "basic_style_signal": 1.0 if {"plain", "basic", "minimal"}.intersection(product_styles) else None,
        "not_flashy_signal": 1.0 if product.get("flashy_design") is False else 0.0 if product.get("flashy_design") else None,
        "review_volume_signal": _review_volume_signal(review_count),
        "review_score_signal": _review_score_signal(review_score),
        "sales_label_signal": _sales_label_signal(product.get("sales_label_count")),
        "ranking_signal": _ranking_signal(product.get("ranking_position")),
        "delivery_signal": 1.0 if product.get("plus_delivery") else 0.4 if product.get("plus_delivery") is False else None,
        "low_issue_signal": _inverse_issue_signal(product.get("low_rating_issue_ratio")),
        "fit_issue_signal": _inverse_issue_signal(product.get("fit_issue_ratio")),
        "material_issue_signal": _inverse_issue_signal(product.get("material_issue_ratio")),
        "repurchase_keyword_signal": _repurchase_signal(product.get("repurchase_keyword_count"), review_count),
    }


def _score_metric(definition: ProxyMetricDefinition, evidence_map: dict[str, float | None]) -> MetricResult:
    score_total = 0.0
    weight_total = 0.0
    evidence: list[str] = []
    missing: list[str] = []

    for key in definition.inputs:
        weight = definition.weights[key]
        value = evidence_map.get(key)
        if value is None:
            missing.append(key)
            continue
        score_total += value * weight
        weight_total += weight
        evidence.append(key)

    score = clamp_score((score_total / weight_total) * 100) if weight_total else 0
    available_confidence = sum(1 for key in definition.confidence_inputs if evidence_map.get(key) is not None)
    coverage = available_confidence / max(len(definition.confidence_inputs), 1)
    raw_confidence = clamp_score((coverage * 70) + (min(weight_total / max(sum(definition.weights.values()), 1), 1) * 30))
    confidence = min(raw_confidence, definition.confidence_ceiling)

    return MetricResult(
        key=definition.key,
        label=definition.label,
        score=score,
        confidence_percent=confidence,
        confidence_level=confidence_level(confidence),
        evidence=evidence,
        missing_evidence=missing,
        limitations=definition.limitations,
    )


def calculate_proxy_metrics(query: str, product: dict[str, Any]) -> dict[str, Any]:
    intent = parse_to_dict(query)
    evidence_map = derive_evidence(intent, product)
    metric_results = [_score_metric(definition, evidence_map) for definition in PROXY_METRICS]
    return {
        "query": query,
        "parsed_intent": intent,
        "product": product,
        "evidence_map": evidence_map,
        "metrics": [asdict(result) for result in metric_results],
        "rule": "모든 추정 지표는 score와 confidence_percent를 함께 표시합니다.",
    }


def validate_proxy_definitions() -> list[str]:
    errors: list[str] = []
    catalog_errors = validate_catalog()
    if catalog_errors:
        errors.extend(f"catalog:{error}" for error in catalog_errors)
    inferred_keys = {signal["key"] for signal in get_signals("inferred")}
    definition_keys = {definition.key for definition in PROXY_METRICS}
    missing_definitions = sorted(inferred_keys - definition_keys)
    if missing_definitions:
        errors.append(f"Missing proxy definitions for inferred signals: {missing_definitions}")
    for definition in PROXY_METRICS:
        if not definition.weights:
            errors.append(f"No weights for {definition.key}")
        if set(definition.inputs) != set(definition.weights):
            errors.append(f"Input/weight mismatch for {definition.key}")
        if not definition.confidence_inputs:
            errors.append(f"No confidence inputs for {definition.key}")
        if not 0 < definition.confidence_ceiling <= 100:
            errors.append(f"Invalid confidence ceiling for {definition.key}")
    sample_result = calculate_proxy_metrics(
        "검은색 반팔 무지티를 2~3만원대에서 40대 남성이 입기 좋은 제품으로 찾아줘",
        SAMPLE_PRODUCT,
    )
    for metric in sample_result["metrics"]:
        if "score" not in metric or "confidence_percent" not in metric:
            errors.append(f"Metric lacks score or confidence: {metric['key']}")
        if not 0 <= metric["score"] <= 100:
            errors.append(f"Score out of range: {metric['key']}")
        if not 0 <= metric["confidence_percent"] <= 100:
            errors.append(f"Confidence out of range: {metric['key']}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate Musinsa public-signal proxy metrics.")
    parser.add_argument("--validate", action="store_true", help="Validate proxy metric definitions")
    parser.add_argument("--sample", action="store_true", help="Run sample proxy metric simulation")
    parser.add_argument("--query", help="Natural-language shopping request")
    parser.add_argument("--product-json", help="Product public/refined signal JSON")
    args = parser.parse_args()

    if args.validate:
        errors = validate_proxy_definitions()
        print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
        raise SystemExit(1 if errors else 0)

    if args.sample:
        query = args.query or "검은색 반팔 무지티를 2~3만원대에서 40대 남성이 입기 좋은 제품으로 찾아줘"
        print(json.dumps(calculate_proxy_metrics(query, SAMPLE_PRODUCT), ensure_ascii=False, indent=2))
        return

    if args.query and args.product_json:
        product = json.loads(args.product_json)
        print(json.dumps(calculate_proxy_metrics(args.query, product), ensure_ascii=False, indent=2))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
