"""Combine public, proxy, and review signals into explainable product scores."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from musinsa_proxy_metrics import SAMPLE_PRODUCT, calculate_proxy_metrics
from musinsa_intent_parser import parse_to_dict
from musinsa_review_signal_schema import DEFAULT_SAMPLE_REVIEWS, analyze_review_texts
from musinsa_runtime_paths import resource_path


DEFAULT_CONFIG_PATH = resource_path("config", "scoring_weights.json")
DEFAULT_QUERY = "검은색 반팔 무지티를 2~3만원대에서 40대 남성이 입기 좋은 제품으로 찾아줘"
SECOND_SAMPLE_PRODUCT = {
    "product_id": "sample-logo-tee",
    "product_name": "그래픽 로고 반팔 티셔츠 블랙",
    "brand_name": "샘플 그래픽",
    "category_label": "반팔 티셔츠",
    "colors": ["black"],
    "styles": ["graphic", "logo"],
    "price": 32900,
    "gender": "M",
    "male_ranking_position": 82,
    "age_40s_ranking_position": None,
    "review_count": 340,
    "review_score": 4.2,
    "sales_label_count": 900,
    "ranking_position": 94,
    "plus_delivery": False,
    "is_ad": True,
    "is_sold_out": False,
    "low_rating_issue_ratio": 0.22,
    "fit_issue_ratio": 0.25,
    "material_issue_ratio": 0.19,
    "repurchase_keyword_count": 1,
    "flashy_design": True,
}


@dataclass(frozen=True)
class ScoreComponent:
    key: str
    label: str
    score: int
    weight: float
    weighted_score: float
    confidence_percent: int
    source: str
    limitation: str


@dataclass(frozen=True)
class ProductScore:
    product_id: str
    product_name: str
    brand_name: str
    final_score: int
    confidence_percent: int
    rank_ready: bool
    components: list[ScoreComponent]
    penalties: list[str]
    explanation: str
    cautions: list[str]


def load_scoring_config(config_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def clamp_score(value: float) -> int:
    return int(round(max(0, min(100, value))))


def _safe_float(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _metric_by_key(metrics: list[dict[str, Any]], key: str) -> dict[str, Any]:
    return next(metric for metric in metrics if metric["key"] == key)


def _review_metric_by_id(metrics: list[dict[str, Any]], metric_id: str) -> dict[str, Any]:
    return next(metric for metric in metrics if metric["metric_id"] == metric_id)


def _price_fit_score(product: dict[str, Any], query: str) -> dict[str, Any]:
    intent = parse_to_dict(query)
    price = _safe_float(product.get("price"), None)
    price_min = intent.get("price_min")
    price_max = intent.get("price_max")
    if price is None:
        return {
            "score": 55,
            "confidence_percent": 30,
            "limitation": "상품 공개 판매가가 없어 가격 적합도는 중립값으로 둔다.",
        }
    if price_min is None and price_max is None:
        return {
            "score": 70,
            "confidence_percent": 35,
            "limitation": "사용자 가격 범위가 없어 공개 판매가를 비교 기준으로만 보조 반영한다.",
        }

    if price_min is not None and price < float(price_min):
        gap_ratio = (float(price_min) - price) / max(float(price_min), 1.0)
        score = clamp_score(100 - (gap_ratio * 70))
    elif price_max is not None and price > float(price_max):
        gap_ratio = (price - float(price_max)) / max(float(price_max), 1.0)
        score = clamp_score(100 - (gap_ratio * 120))
    else:
        score = 100

    if score == 100:
        confidence = 88
    elif score >= 70:
        confidence = 82
    else:
        confidence = 76
    return {
        "score": score,
        "confidence_percent": confidence,
        "limitation": "가격 적합도는 사용자가 입력한 가격 범위와 공개 판매가 비교 결과다.",
    }


def _popularity_score(proxy_metrics: list[dict[str, Any]]) -> dict[str, Any]:
    trust = _metric_by_key(proxy_metrics, "purchase_trust_score")
    review_purchase = _metric_by_key(proxy_metrics, "review_purchase_evidence_score")
    age = _metric_by_key(proxy_metrics, "age_male_40s_fit_score")
    score = clamp_score((review_purchase["score"] * 0.55) + (trust["score"] * 0.3) + (age["score"] * 0.15))
    confidence = min(
        82,
        int(round((review_purchase["confidence_percent"] + trust["confidence_percent"] + age["confidence_percent"]) / 3)),
    )
    return {
        "score": score,
        "confidence_percent": confidence,
        "limitation": "인기 근거는 리뷰 수를 구매 후 반응 누적량으로 반영한 공개 대체 지표이며 실제 판매량이 아니다.",
    }


def _delivery_stock_score(product: dict[str, Any]) -> dict[str, Any]:
    if product.get("is_sold_out"):
        score = 0
    elif product.get("plus_delivery"):
        score = 100
    elif product.get("plus_delivery") is False:
        score = 55
    else:
        score = 60
    return {
        "score": score,
        "confidence_percent": 90 if product.get("is_sold_out") is not None or product.get("plus_delivery") is not None else 45,
        "limitation": "배송/품절 점수는 공개 노출 상태 기준이며 실제 배송 확정일이 아니다.",
    }


def _public_review_count_confidence(review_count: int | float | None) -> int:
    count = int(review_count or 0)
    if count >= 1000:
        return 64
    if count >= 300:
        return 56
    if count >= 50:
        return 46
    if count > 0:
        return 36
    return 24


def _buyer_context_score(
    product: dict[str, Any],
    review_metrics: list[dict[str, Any]],
    proxy_metrics: list[dict[str, Any]],
    has_review_texts: bool,
) -> dict[str, Any]:
    context = _review_metric_by_id(review_metrics, "buyer_context_profile_score")
    age_context = _metric_by_key(proxy_metrics, "age_male_40s_fit_score")
    purchase_trust = _metric_by_key(proxy_metrics, "purchase_trust_score")
    purpose = _metric_by_key(proxy_metrics, "purpose_fit_score")
    public_score = clamp_score(
        (age_context["score"] * 0.45) + (purchase_trust["score"] * 0.3) + (purpose["score"] * 0.25)
    )
    public_confidence = min(
        64,
        int(
            round(
                (
                    age_context["confidence_percent"]
                    + purchase_trust["confidence_percent"]
                    + purpose["confidence_percent"]
                )
                / 3
            )
        ),
    )
    if has_review_texts:
        score = clamp_score((context["score"] * 0.55) + (public_score * 0.45))
        confidence = min(72, int(round((context["confidence_percent"] + public_confidence) / 2)))
        limitation = "타겟 적합도는 리뷰 키워드와 공개 상품 반응을 함께 반영한 추정이며 실제 구매자 속성 통계가 아니다."
    else:
        score = public_score
        confidence = max(24, public_confidence)
        limitation = "타겟 적합도는 실제 연령/성별 구매 통계가 아니라 공개 랭킹, 리뷰 수, 평점, 목적 일치도 기반 대체 지표다."
    if not product.get("review_count"):
        confidence = min(confidence, 38)
    return {
        "score": score,
        "confidence_percent": confidence,
        "limitation": limitation,
    }


def _public_review_risk_proxy(product: dict[str, Any]) -> dict[str, Any]:
    review_score = _safe_float(product.get("review_score"), 0.0) or 0.0
    review_count = int(_safe_float(product.get("review_count"), 0.0) or 0)
    low_rating_issue = _safe_float(product.get("low_rating_issue_ratio"), None)
    fit_issue = _safe_float(product.get("fit_issue_ratio"), None)
    material_issue = _safe_float(product.get("material_issue_ratio"), None)
    if low_rating_issue is None:
        low_rating_issue = 0.3 if not review_score else max(0.04, min(0.45, 0.1 + ((4.8 - review_score) * 0.14)))
    if fit_issue is None:
        fit_issue = 0.22 if review_count < 50 else 0.16
    if material_issue is None:
        material_issue = 0.22 if review_count < 50 else 0.15
    issue_stability = clamp_score(100 - ((low_rating_issue * 40) + (fit_issue * 30) + (material_issue * 30)))
    if review_score:
        rating_stability = clamp_score(55 + ((review_score - 3.5) / 1.5 * 45))
    else:
        rating_stability = 55
    if review_count >= 1000:
        volume_stability = 92
    elif review_count >= 300:
        volume_stability = 78
    elif review_count >= 50:
        volume_stability = 62
    elif review_count > 0:
        volume_stability = 48
    else:
        volume_stability = 35
    score = clamp_score((issue_stability * 0.55) + (rating_stability * 0.3) + (volume_stability * 0.15))
    return {
        "score": score,
        "confidence_percent": _public_review_count_confidence(review_count),
        "limitation": "리스크 안정성은 공개 리뷰 수, 평점, 이슈 비율 기반 대체 지표이며 실제 반품률이나 불만 리뷰 원문 분석값이 아니다.",
    }


def _review_risk_score(
    product: dict[str, Any],
    review_metrics: list[dict[str, Any]],
    has_review_texts: bool,
) -> dict[str, Any]:
    size = _review_metric_by_id(review_metrics, "size_fit_review_score")
    fabric = _review_metric_by_id(review_metrics, "fabric_risk_review_score")
    text_score = clamp_score((size["score"] * 0.45) + (fabric["score"] * 0.55))
    text_confidence = min(80, int(round((size["confidence_percent"] + fabric["confidence_percent"]) / 2)))
    public_proxy = _public_review_risk_proxy(product)
    if has_review_texts:
        score = clamp_score((text_score * 0.65) + (public_proxy["score"] * 0.35))
        confidence = min(78, int(round((text_confidence + public_proxy["confidence_percent"]) / 2)))
        limitation = "리스크 안정성은 리뷰 키워드와 공개 리뷰 반응을 함께 반영한 보조 지표이며 실제 반품률이 아니다."
    else:
        score = public_proxy["score"]
        confidence = public_proxy["confidence_percent"]
        limitation = public_proxy["limitation"]
    return {
        "score": score,
        "confidence_percent": confidence,
        "limitation": limitation,
    }


def _component(key: str, label: str, raw: dict[str, Any], weight: float, source: str) -> ScoreComponent:
    score = int(raw["score"])
    return ScoreComponent(
        key=key,
        label=label,
        score=score,
        weight=weight,
        weighted_score=round(score * (weight / 100), 2),
        confidence_percent=int(raw["confidence_percent"]),
        source=source,
        limitation=raw["limitation"] if "limitation" in raw else "; ".join(raw.get("limitations", [])),
    )


def score_product(
    query: str,
    product: dict[str, Any],
    review_texts: list[str] | None = None,
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    config = load_scoring_config(config_path)
    weights = config["weights"]
    proxy_result = calculate_proxy_metrics(query, product)
    proxy_metrics = proxy_result["metrics"]
    has_review_texts = bool(review_texts)
    review_analysis = analyze_review_texts(review_texts or DEFAULT_SAMPLE_REVIEWS)
    review_metrics = review_analysis["metrics"]

    purpose = _metric_by_key(proxy_metrics, "purpose_fit_score")
    trust = _metric_by_key(proxy_metrics, "purchase_trust_score")
    review_purchase = _metric_by_key(proxy_metrics, "review_purchase_evidence_score")
    age = _metric_by_key(proxy_metrics, "age_male_40s_fit_score")
    buyer_context = _buyer_context_score(product, review_metrics, proxy_metrics, has_review_texts)
    price = _price_fit_score(product, query)
    popularity = _popularity_score(proxy_metrics)
    delivery_stock = _delivery_stock_score(product)
    review_risk = _review_risk_score(product, review_metrics, has_review_texts)

    components = [
        _component("purpose_fit_score", "목적 적합도", purpose, weights["purpose_fit_score"], "proxy"),
        _component("purchase_trust_score", "구매 신뢰도", trust, weights["purchase_trust_score"], "proxy"),
        _component(
            "review_purchase_evidence_score",
            "리뷰 기반 구매 반응 누적 근거",
            review_purchase,
            weights["review_purchase_evidence_score"],
            "proxy",
        ),
        _component("age_male_40s_fit_score", "40대 남성 적합 추정", age, weights["age_male_40s_fit_score"], "proxy"),
        _component("buyer_context_profile_score", "타겟 적합도 추정", buyer_context, weights["buyer_context_profile_score"], "review"),
        _component("price_fit_score", "가격 적합도", price, weights["price_fit_score"], "derived"),
        _component("popularity_proxy_score", "인기 근거", popularity, weights["popularity_proxy_score"], "derived"),
        _component("delivery_stock_score", "배송/품절", delivery_stock, weights["delivery_stock_score"], "public"),
        _component("review_risk_score", "리스크 안정성", review_risk, weights["review_risk_score"], "review"),
    ]

    base_score = sum(component.weighted_score for component in components)
    penalties: list[str] = []
    if product.get("is_ad"):
        base_score -= config["penalties"]["is_ad"]
        penalties.append("광고/스폰서 가능성이 있어 소폭 감점")
    if product.get("is_sold_out"):
        base_score -= config["penalties"]["is_sold_out"]
        penalties.append("품절 상품이라 추천 후보에서 제외 수준 감점")

    final_score = clamp_score(base_score)
    confidence_values = [component.confidence_percent for component in components]
    confidence = min(config["confidence_caps"]["final_score"], int(round(sum(confidence_values) / len(confidence_values))))
    rank_ready = not product.get("is_sold_out", False)
    explanation = (
        f"{product.get('brand_name', '')} {product.get('product_name', '')}은 목적 적합도, 리뷰 기반 구매 반응 누적 근거, 구매 신뢰도를 "
        f"종합해 final_score {final_score}점으로 계산되었습니다."
    )
    cautions = [component.limitation for component in components if component.source in {"proxy", "review", "derived"}]
    cautions.extend(penalties)

    result = ProductScore(
        product_id=product.get("product_id", ""),
        product_name=product.get("product_name", ""),
        brand_name=product.get("brand_name", ""),
        final_score=final_score,
        confidence_percent=confidence,
        rank_ready=rank_ready,
        components=components,
        penalties=penalties,
        explanation=explanation,
        cautions=cautions,
    )
    return {
        "query": query,
        "config_version": config["version"],
        "score_boundary": config["explanation"]["score_boundary"],
        "confidence_boundary": config["explanation"]["confidence_boundary"],
        "product_score": {
            **asdict(result),
            "components": [asdict(component) for component in components],
        },
    }


def compare_sample_products(query: str = DEFAULT_QUERY) -> dict[str, Any]:
    products = [SAMPLE_PRODUCT, SECOND_SAMPLE_PRODUCT]
    scored = [score_product(query, product)["product_score"] for product in products]
    ranked = sorted(scored, key=lambda item: item["final_score"], reverse=True)
    return {
        "query": query,
        "scored_product_count": len(scored),
        "ranked_products": ranked,
        "next_step_hint": "다음 단계에서 최종 후보 비교표와 추천 출력 템플릿으로 연결합니다.",
    }


def validate_scoring_model() -> list[str]:
    errors: list[str] = []
    config = load_scoring_config()
    if round(sum(config["weights"].values()), 5) != 100:
        errors.append("Scoring weights must sum to 100")
    if config["confidence_caps"]["final_score"] > 90:
        errors.append("final_score confidence cap is too high for proxy-based scoring")
    sample = compare_sample_products()
    if sample["scored_product_count"] < 2:
        errors.append("Sample comparison must include at least two products")
    for product in sample["ranked_products"]:
        if not 0 <= product["final_score"] <= 100:
            errors.append(f"final_score out of range: {product['product_id']}")
        if not 0 <= product["confidence_percent"] <= config["confidence_caps"]["final_score"]:
            errors.append(f"confidence out of range: {product['product_id']}")
        if not product["components"]:
            errors.append(f"missing score components: {product['product_id']}")
        component_weight = round(sum(component["weight"] for component in product["components"]), 5)
        if component_weight != 100:
            errors.append(f"component weights must sum to 100: {product['product_id']}")
        if not product["cautions"]:
            errors.append(f"missing cautions: {product['product_id']}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate Musinsa product scoring model.")
    parser.add_argument("--validate", action="store_true", help="Validate scoring model")
    parser.add_argument("--sample", action="store_true", help="Run sample product comparison")
    parser.add_argument("--query", default=DEFAULT_QUERY, help="Natural-language shopping request")
    args = parser.parse_args()

    if args.validate:
        errors = validate_scoring_model()
        print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
        raise SystemExit(1 if errors else 0)
    print(json.dumps(compare_sample_products(args.query), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
