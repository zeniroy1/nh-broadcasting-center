"""Build a buyer-facing comparison report from scored Musinsa candidates."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from musinsa_proxy_metrics import SAMPLE_PRODUCT
from musinsa_scoring_model import DEFAULT_QUERY, SECOND_SAMPLE_PRODUCT, score_product


THIRD_SAMPLE_PRODUCT = {
    "product_id": "sample-premium-tee",
    "product_name": "프리미엄 코튼 무지 반팔 티셔츠 블랙",
    "brand_name": "샘플 코튼",
    "category_label": "반팔 티셔츠",
    "colors": ["black"],
    "styles": ["plain", "basic", "minimal"],
    "price": 38900,
    "gender": "M",
    "male_ranking_position": 36,
    "age_40s_ranking_position": 41,
    "review_count": 2100,
    "review_score": 4.7,
    "sales_label_count": 12000,
    "ranking_position": 42,
    "plus_delivery": True,
    "is_ad": False,
    "is_sold_out": False,
    "low_rating_issue_ratio": 0.12,
    "fit_issue_ratio": 0.15,
    "material_issue_ratio": 0.09,
    "repurchase_keyword_count": 18,
    "flashy_design": False,
}
FOURTH_SAMPLE_PRODUCT = {
    "product_id": "sample-budget-tee",
    "product_name": "데일리 무지 반팔 티셔츠 블랙",
    "brand_name": "샘플 데일리",
    "category_label": "반팔 티셔츠",
    "colors": ["black"],
    "styles": ["plain", "basic"],
    "price": 20900,
    "gender": "M",
    "male_ranking_position": 54,
    "age_40s_ranking_position": 67,
    "review_count": 980,
    "review_score": 4.5,
    "sales_label_count": 8200,
    "ranking_position": 58,
    "plus_delivery": False,
    "is_ad": False,
    "is_sold_out": False,
    "low_rating_issue_ratio": 0.16,
    "fit_issue_ratio": 0.18,
    "material_issue_ratio": 0.16,
    "repurchase_keyword_count": 7,
    "flashy_design": False,
}
FIFTH_SAMPLE_PRODUCT = {
    "product_id": "sample-athletic-tee",
    "product_name": "쿨링 기능성 반팔 티셔츠 블랙",
    "brand_name": "샘플 액티브",
    "category_label": "반팔 티셔츠",
    "colors": ["black"],
    "styles": ["plain", "sport"],
    "price": 27900,
    "gender": "M",
    "male_ranking_position": 73,
    "age_40s_ranking_position": None,
    "review_count": 620,
    "review_score": 4.3,
    "sales_label_count": 2600,
    "ranking_position": 76,
    "plus_delivery": True,
    "is_ad": False,
    "is_sold_out": False,
    "low_rating_issue_ratio": 0.2,
    "fit_issue_ratio": 0.2,
    "material_issue_ratio": 0.18,
    "repurchase_keyword_count": 3,
    "flashy_design": False,
}
SAMPLE_CANDIDATES = [
    SAMPLE_PRODUCT,
    SECOND_SAMPLE_PRODUCT,
    THIRD_SAMPLE_PRODUCT,
    FOURTH_SAMPLE_PRODUCT,
    FIFTH_SAMPLE_PRODUCT,
]
OUTPUT_BOUNDARIES = [
    "추천 순위는 공개 지표와 대체 지표 기반의 비교 결과이며 실제 판매 순위가 아니다.",
    "리뷰 수는 구매 후 반응 누적 근거지만 실제 구매자 수나 판매량으로 환산하지 않는다.",
    "타겟 적합도는 리뷰 키워드 기반 추정이며 실제 연령/성별별 구매 통계가 아니다.",
    "confidence_percent는 정답 확률이 아니라 공개 근거 충실도다.",
]
BAR_COLORS = ["#167647", "#175cd3", "#b54708", "#7a5af8", "#c11574"]


@dataclass(frozen=True)
class RecommendationCard:
    rank: int
    product_id: str
    brand_name: str
    product_name: str
    price: int | None
    product_url: str | None
    image_url: str | None
    final_score: int
    confidence_percent: int
    decision_label: str
    fit_label: str
    reasons: list[str]
    public_evidence: list[str]
    cautions: list[str]


def _price_label(price: int | None) -> str:
    if price is None:
        return "가격 미확인"
    return f"{price:,}원"


def _clean_display_name(product_name: str) -> str:
    cleaned = re.sub(r"\[[^\]]+\]\s*", "", product_name)
    return " ".join(cleaned.split()).strip() or product_name


def _component_by_key(product_score: dict[str, Any], key: str) -> dict[str, Any]:
    return next(component for component in product_score["components"] if component["key"] == key)


def _fit_label(final_score: int) -> str:
    if final_score >= 85:
        return "강한 추천 후보"
    if final_score >= 70:
        return "비교 검토 후보"
    if final_score >= 55:
        return "조건 일부 충족 후보"
    return "후순위 후보"


def _decision_label(rank: int, product_score: dict[str, Any]) -> str:
    if not product_score["rank_ready"]:
        return "제외 후보"
    if rank == 1:
        return "1순위 확인"
    if rank == 2:
        return "대안 비교"
    return "보조 후보"


def _reason_lines(product_score: dict[str, Any]) -> list[str]:
    purpose = _component_by_key(product_score, "purpose_fit_score")
    review_purchase = _component_by_key(product_score, "review_purchase_evidence_score")
    price = _component_by_key(product_score, "price_fit_score")
    buyer_context = _component_by_key(product_score, "buyer_context_profile_score")
    review_purchase_text = (
        f"리뷰 기반 구매 반응 근거 {review_purchase['score']}점으로 공개 반응이 충분히 누적되어 있습니다."
        if review_purchase["score"] >= 80
        else f"리뷰 기반 구매 반응 근거 {review_purchase['score']}점으로 1순위 후보 대비 공개 반응이 약합니다."
    )
    reasons = [
        f"목적 적합도 {purpose['score']}점으로 요청 조건과 잘 맞습니다.",
        review_purchase_text,
        f"가격 적합도 {price['score']}점으로 요청 가격대와 비교 가능합니다.",
    ]
    if buyer_context["score"] >= 70:
        reasons.append(f"리뷰 키워드 기반 타겟 적합도 {buyer_context['score']}점이 보조 근거로 반영됐습니다.")
    return reasons


def _public_evidence(product: dict[str, Any], product_score: dict[str, Any]) -> list[str]:
    evidence = [
        f"가격: {_price_label(product.get('price'))}",
        f"리뷰 수: {product.get('review_count', '미확인')}",
        f"리뷰 평점: {product.get('review_score', '미확인')}",
        f"판매 라벨: {product.get('sales_label_count', '미확인')}",
        f"랭킹 위치: {product.get('ranking_position', '미확인')}",
        f"배송: {'플러스배송' if product.get('plus_delivery') else '일반/미확인'}",
    ]
    evidence.append(f"점수 신뢰도: {product_score['confidence_percent']}%")
    return evidence


def _caution_lines(product: dict[str, Any], product_score: dict[str, Any]) -> list[str]:
    review_risk = _component_by_key(product_score, "review_risk_score")
    cautions: list[str] = []
    if product.get("is_ad"):
        cautions.append("광고/스폰서 가능성이 있어 순수 인기 근거와 분리해 봐야 합니다.")
    if product.get("is_sold_out"):
        cautions.append("품절 상품이므로 구매 후보에서 제외해야 합니다.")
    if review_risk["score"] < 70:
        cautions.append(f"리뷰 리스크 점수 {review_risk['score']}점으로 사이즈/원단 후기를 추가 확인해야 합니다.")
    if product_score["confidence_percent"] < 75:
        cautions.append("공개 근거 충실도가 낮아 상세 페이지와 리뷰 원문 확인이 필요합니다.")
    cautions.extend(product_score["cautions"][:2])
    return cautions[:5]


def _bar_chart_rows(cards: list[RecommendationCard]) -> list[dict[str, Any]]:
    return [
        {
            "rank": card.rank,
            "product_id": card.product_id,
            "short_label": _short_product_label(card.product_name),
            "label": f"{card.brand_name} / {_clean_display_name(card.product_name)}",
            "final_score": card.final_score,
            "confidence_percent": card.confidence_percent,
            "bar_percent": card.final_score,
            "bar_color": BAR_COLORS[(card.rank - 1) % len(BAR_COLORS)],
        }
        for card in cards
    ]


def _short_product_label(product_name: str) -> str:
    product_name = _clean_display_name(product_name)
    if "베이직" in product_name:
        return "베이직"
    if "프리미엄" in product_name:
        return "코튼"
    if "데일리" in product_name:
        return "데일리"
    if "쿨링" in product_name:
        return "쿨링"
    if "그래픽" in product_name:
        return "그래픽"
    return product_name[:4]


def _detail_segments(product_score: dict[str, Any]) -> list[dict[str, Any]]:
    keys = [
        "purpose_fit_score",
        "review_purchase_evidence_score",
        "price_fit_score",
        "buyer_context_profile_score",
        "review_risk_score",
    ]
    colors = ["#167647", "#175cd3", "#b54708", "#7a5af8", "#b42318"]
    segments = []
    for index, key in enumerate(keys):
        component = _component_by_key(product_score, key)
        if key == "buyer_context_profile_score":
            label = "타겟 적합도"
            score = component["score"]
        elif key == "review_risk_score":
            label = "리스크"
            score = max(0, min(100, 100 - int(component["score"])))
        else:
            label = component["label"]
            score = component["score"]
        segments.append(
            {
                "key": component["key"],
                "label": label,
                "score": score,
                "weight": component["weight"],
                "weighted_score": component["weighted_score"],
                "confidence_percent": component["confidence_percent"],
                "evidence_status": "미확인" if component["confidence_percent"] <= 38 else "확인",
                "color": colors[index],
            }
        )
    return segments


def _shortlist_detail(
    ranked_items: list[dict[str, Any]],
    selected_product_ids: list[str] | None = None,
    target_count: int = 3,
) -> dict[str, Any]:
    if selected_product_ids:
        selected = [item for item in ranked_items if item["product_score"]["product_id"] in selected_product_ids]
    else:
        selected = ranked_items[:target_count]
    selected = selected[:target_count]
    panels = []
    for index, item in enumerate(selected, start=1):
        product = item["source_product"]
        product_score = item["product_score"]
        panels.append(
            {
                "detail_rank": index,
                "product_id": product_score["product_id"],
                "brand_name": product_score["brand_name"],
                "product_name": _clean_display_name(product_score["product_name"]),
                "price": _price_label(product.get("price")),
                "product_url": product.get("product_url"),
                "image_url": product.get("image_url"),
                "final_score": product_score["final_score"],
                "confidence_percent": product_score["confidence_percent"],
                "fit_label": _fit_label(product_score["final_score"]),
                "component_segments": _detail_segments(product_score),
                "detail_questions": [
                    "목적 조건과 가격대가 실제 구매 의도에 맞는가?",
                    "리뷰 원문에서 사이즈/원단 리스크가 허용 가능한가?",
                    "광고/배송/품절 조건을 분리해 봐도 여전히 우선 후보인가?",
                ],
            }
        )
    return {
        "selected_count": len(panels),
        "target_count": target_count,
        "selection_rule": "초기 5개 후보에서 구매자가 3개를 고르면 세부 지표와 적합성을 다시 비교한다.",
        "detail_panels": panels,
    }


def _score_candidates(query: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored = []
    for product in candidates:
        product_score = score_product(query, product)["product_score"]
        if "similar_keyword" in str(product.get("source") or ""):
            product_score["final_score"] = min(product_score["final_score"], 74)
            product_score["confidence_percent"] = min(product_score["confidence_percent"], 58)
            product_score["cautions"].insert(0, "정확 키워드 일치가 아니라 무신사 검색 결과 기반 유사 후보입니다.")
        scored.append({"source_product": product, "product_score": product_score})
    return sorted(
        scored,
        key=lambda item: (
            item["product_score"]["rank_ready"],
            item["source_product"].get("specific_match_priority", 0),
            item["source_product"].get("specific_term_match_count", 0),
            item["product_score"]["final_score"],
        ),
        reverse=True,
    )


def build_recommendation_report(
    query: str = DEFAULT_QUERY,
    candidates: list[dict[str, Any]] | None = None,
    max_candidates: int = 5,
    shortlist_product_ids: list[str] | None = None,
) -> dict[str, Any]:
    source_candidates = SAMPLE_CANDIDATES if candidates is None else candidates
    scored_ranked = _score_candidates(query, source_candidates)
    ranked = scored_ranked[:max_candidates]
    cards: list[RecommendationCard] = []

    for index, item in enumerate(ranked, start=1):
        product = item["source_product"]
        product_score = item["product_score"]
        cards.append(
            RecommendationCard(
                rank=index,
                product_id=product_score["product_id"],
                brand_name=product_score["brand_name"],
                product_name=product_score["product_name"],
                price=product.get("price"),
                product_url=product.get("product_url"),
                image_url=product.get("image_url"),
                final_score=product_score["final_score"],
                confidence_percent=product_score["confidence_percent"],
                decision_label=_decision_label(index, product_score),
                fit_label=_fit_label(product_score["final_score"]),
                reasons=_reason_lines(product_score),
                public_evidence=_public_evidence(product, product_score),
                cautions=_caution_lines(product, product_score),
            )
        )

    comparison_rows = [
        {
            "rank": card.rank,
            "brand": card.brand_name,
            "product": _clean_display_name(card.product_name),
            "price": _price_label(card.price),
            "product_id": card.product_id,
            "product_url": card.product_url,
            "image_url": card.image_url,
            "final_score": card.final_score,
            "confidence_percent": card.confidence_percent,
            "decision": card.decision_label,
            "fit": card.fit_label,
        }
        for card in cards
    ]
    winner = cards[0] if cards else None
    return {
        "query": query,
        "recommendation_count": len(cards),
        "winner_product_id": winner.product_id if winner else None,
        "decision_summary": (
            f"{winner.brand_name} {winner.product_name}을 1순위로 확인하고, "
            "리뷰 원문과 사이즈/원단 리스크를 마지막으로 검토합니다."
            if winner
            else "추천 후보가 없습니다."
        ),
        "comparison_table": {
            "columns": ["rank", "brand", "product", "price", "final_score", "confidence_percent", "decision", "fit"],
            "rows": comparison_rows,
        },
        "recommendation_cards": [asdict(card) for card in cards],
        "visualizations": {
            "score_bar_chart": _bar_chart_rows(cards),
            "chart_policy": "세로 막대그래프는 final_score 비교용, 원형/도넛 그래프는 shortlist 3개 후보의 세부 지표 분해용으로 사용한다.",
        },
        "shortlist_detail": _shortlist_detail(ranked, shortlist_product_ids, 3),
        "purchase_roadmap": [
            "초기 후보 5개를 final_score 세로 막대그래프로 비교한다.",
            "구매자가 관심 후보 3개를 shortlist로 고른다.",
            "shortlist 3개는 목적/리뷰/가격/타겟/리스크 도넛 그래프로 세부 비교한다.",
            "최종 후보 1~2개로 줄인 뒤 상세 페이지와 리뷰 원문을 확인한다.",
        ],
        "boundaries": OUTPUT_BOUNDARIES,
        "next_step_hint": "다음 단계에서 사용자 피드백을 반영해 조건 강화/완화 후 재정렬하는 구조로 연결합니다.",
    }


def validate_recommendation_report() -> list[str]:
    errors: list[str] = []
    report = build_recommendation_report()
    if report["recommendation_count"] != 5:
        errors.append("Sample report must include five initial candidates")
    if not report["winner_product_id"]:
        errors.append("Report must expose a winner product id")
    if not report["comparison_table"]["rows"]:
        errors.append("Comparison table must include rows")
    if len(report["visualizations"]["score_bar_chart"]) != 5:
        errors.append("Score bar chart must include five rows")
    if report["shortlist_detail"]["selected_count"] != 3:
        errors.append("Shortlist detail must include three candidates")
    for row in report["comparison_table"]["rows"]:
        if not 0 <= row["final_score"] <= 100:
            errors.append(f"final_score out of range: {row['product']}")
        if not 0 <= row["confidence_percent"] <= 88:
            errors.append(f"confidence out of range: {row['product']}")
    for card in report["recommendation_cards"]:
        if not card["reasons"]:
            errors.append(f"missing reasons: {card['product_id']}")
        if not card["public_evidence"]:
            errors.append(f"missing public evidence: {card['product_id']}")
        if not card["cautions"]:
            errors.append(f"missing cautions: {card['product_id']}")
    for panel in report["shortlist_detail"]["detail_panels"]:
        if len(panel["component_segments"]) < 5:
            errors.append(f"missing component segments: {panel['product_id']}")
        if not panel["detail_questions"]:
            errors.append(f"missing detail questions: {panel['product_id']}")
    if not any("실제 구매자 수" in boundary for boundary in report["boundaries"]):
        errors.append("Report must keep the actual buyer count boundary")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Musinsa recommendation comparison report.")
    parser.add_argument("--validate", action="store_true", help="Validate recommendation report")
    parser.add_argument("--sample", action="store_true", help="Run sample recommendation report")
    parser.add_argument("--query", default=DEFAULT_QUERY, help="Natural-language shopping request")
    args = parser.parse_args()

    if args.validate:
        errors = validate_recommendation_report()
        print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
        raise SystemExit(1 if errors else 0)
    print(json.dumps(build_recommendation_report(args.query), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
