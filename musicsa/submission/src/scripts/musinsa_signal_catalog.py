"""Catalog public Musinsa data sources and usable product signals."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from musinsa_intent_parser import parse_to_dict


ALLOWED_TIERS = {"direct", "refined", "inferred"}


@dataclass(frozen=True)
class SourceDefinition:
    key: str
    label: str
    access_type: str
    purpose: str
    public_fields: list[str]
    limitations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SignalDefinition:
    key: str
    label: str
    tier: str
    sources: list[str]
    source_fields: list[str]
    extraction_method: str
    used_for: list[str]
    confidence_policy: str
    limitations: list[str] = field(default_factory=list)


SOURCES = [
    SourceDefinition(
        key="ranking_page",
        label="랭킹 페이지",
        access_type="public_json",
        purpose="성별/연령대/카테고리/기간 조건별 공개 랭킹 노출을 확인한다.",
        public_fields=[
            "rank",
            "product_id",
            "brand_name",
            "product_name",
            "price",
            "discount_rate",
            "image_url",
            "product_url",
            "sales_label",
            "viewing_now_label",
            "buying_now_label",
        ],
        limitations=["랭킹 알고리즘과 실제 구매자 수는 공개되지 않는다."],
    ),
    SourceDefinition(
        key="search_results_page",
        label="검색 결과 페이지",
        access_type="public_page_or_json",
        purpose="사용자 검색어별 상품 후보와 검색 노출 위치를 확인한다.",
        public_fields=[
            "search_position",
            "product_id",
            "brand_name",
            "product_name",
            "price",
            "discount_rate",
            "image_url",
            "product_url",
            "ad_marker",
        ],
        limitations=["추천순/인기순의 내부 정렬 점수는 공개되지 않는다."],
    ),
    SourceDefinition(
        key="category_page",
        label="카테고리 페이지",
        access_type="public_page_or_json",
        purpose="카테고리 필터와 상품군 범위를 확인한다.",
        public_fields=[
            "category_code",
            "category_name",
            "product_id",
            "brand_name",
            "product_name",
            "price",
            "sold_out",
        ],
        limitations=["카테고리별 노출 순서의 상세 산식은 공개되지 않는다."],
    ),
    SourceDefinition(
        key="product_detail_page",
        label="상품 상세 페이지",
        access_type="public_embedded_json",
        purpose="후보 상품의 가격, 리뷰 요약, 배송, 상세 설명, 랭킹 기록을 확인한다.",
        public_fields=[
            "goods_no",
            "goods_name",
            "brand_info",
            "category",
            "gender",
            "price",
            "normal_price",
            "discount_rate",
            "review_count",
            "review_score",
            "delivery_expected_arrival",
            "plus_delivery",
            "sold_out",
            "goods_images",
            "goods_contents",
            "md_opinion",
            "ranking_record",
        ],
        limitations=["로그인 개인화 가격과 비공개 재고/구매 통계는 제외된다."],
    ),
    SourceDefinition(
        key="review_area",
        label="리뷰 영역",
        access_type="public_page_or_json",
        purpose="착용감, 사이즈, 재구매, 불만 키워드 등 정제 지표를 만든다.",
        public_fields=[
            "review_text",
            "review_score",
            "size_feedback",
            "fit_feedback",
            "review_created_at",
        ],
        limitations=["리뷰는 표본 편향이 있으며 실제 반품률을 직접 의미하지 않는다."],
    ),
    SourceDefinition(
        key="brand_page",
        label="브랜드 페이지",
        access_type="public_page_or_json",
        purpose="브랜드명, 브랜드 소개, 공식 브랜드 여부를 확인한다.",
        public_fields=["brand_name", "brand_english_name", "brand_intro", "official_flag"],
        limitations=["브랜드 신뢰도 자체는 별도 추정 지표로 계산해야 한다."],
    ),
]


SIGNALS = [
    SignalDefinition(
        key="product_id",
        label="상품 ID",
        tier="direct",
        sources=["ranking_page", "search_results_page", "category_page", "product_detail_page"],
        source_fields=["product_id", "goods_no"],
        extraction_method="공개 응답의 상품 식별자를 그대로 저장한다.",
        used_for=["deduplication", "product_url"],
        confidence_policy="direct_public_value_100",
    ),
    SignalDefinition(
        key="product_name",
        label="상품명",
        tier="direct",
        sources=["ranking_page", "search_results_page", "product_detail_page"],
        source_fields=["product_name", "goods_name"],
        extraction_method="공개 상품명을 그대로 저장한다.",
        used_for=["keyword_matching", "style_refinement"],
        confidence_policy="direct_public_value_100",
    ),
    SignalDefinition(
        key="brand_name",
        label="브랜드명",
        tier="direct",
        sources=["ranking_page", "search_results_page", "product_detail_page", "brand_page"],
        source_fields=["brand_name", "brand_info"],
        extraction_method="공개 브랜드명을 그대로 저장한다.",
        used_for=["brand_grouping", "comparison"],
        confidence_policy="direct_public_value_100",
    ),
    SignalDefinition(
        key="price",
        label="판매가",
        tier="direct",
        sources=["ranking_page", "search_results_page", "product_detail_page"],
        source_fields=["price", "sale_price", "final_price"],
        extraction_method="공개 판매가를 숫자로 정규화한다.",
        used_for=["price_fit_score", "filtering"],
        confidence_policy="direct_public_value_100",
    ),
    SignalDefinition(
        key="discount_rate",
        label="할인율",
        tier="direct",
        sources=["ranking_page", "search_results_page", "product_detail_page"],
        source_fields=["discount_rate"],
        extraction_method="공개 할인율을 숫자로 정규화한다.",
        used_for=["comparison", "value_score"],
        confidence_policy="direct_public_value_100",
    ),
    SignalDefinition(
        key="review_count",
        label="리뷰 수",
        tier="direct",
        sources=["product_detail_page", "review_area"],
        source_fields=["review_count", "total_count"],
        extraction_method="공개 리뷰 총수를 그대로 저장한다.",
        used_for=["trust_score", "popularity_proxy_score"],
        confidence_policy="direct_public_value_100",
    ),
    SignalDefinition(
        key="review_score",
        label="평점/만족도",
        tier="direct",
        sources=["product_detail_page", "review_area"],
        source_fields=["review_score", "satisfaction_score"],
        extraction_method="공개 평점 또는 만족도 점수를 정규화한다.",
        used_for=["trust_score", "review_risk_score"],
        confidence_policy="direct_public_value_100",
    ),
    SignalDefinition(
        key="ranking_position",
        label="랭킹 순위",
        tier="direct",
        sources=["ranking_page", "product_detail_page"],
        source_fields=["rank", "ranking_record"],
        extraction_method="공개 랭킹 순위와 조건을 함께 저장한다.",
        used_for=["popularity_proxy_score", "age_gender_proxy"],
        confidence_policy="direct_public_value_100_for_position_only",
        limitations=["랭킹 순위는 판매량 자체가 아니다."],
    ),
    SignalDefinition(
        key="sales_label",
        label="판매 라벨",
        tier="direct",
        sources=["ranking_page"],
        source_fields=["sales_label"],
        extraction_method="판매 3.3천개 같은 공개 라벨을 원문과 숫자 후보로 저장한다.",
        used_for=["popularity_proxy_score"],
        confidence_policy="direct_public_label_90_to_100",
        limitations=["라벨 노출 기준과 갱신 시점은 공개되지 않을 수 있다."],
    ),
    SignalDefinition(
        key="viewing_buying_labels",
        label="현재 보는 중/구매 중 라벨",
        tier="direct",
        sources=["ranking_page"],
        source_fields=["viewing_now_label", "buying_now_label"],
        extraction_method="현재 보는 중, 구매 중 표시를 원문과 숫자 후보로 저장한다.",
        used_for=["real_time_interest_proxy"],
        confidence_policy="direct_public_label_80_to_100",
        limitations=["순간 표시이며 장기 구매 성과를 의미하지 않는다."],
    ),
    SignalDefinition(
        key="delivery_signal",
        label="배송 정보",
        tier="direct",
        sources=["product_detail_page"],
        source_fields=["delivery_expected_arrival", "plus_delivery"],
        extraction_method="도착 예정일과 플러스배송 여부를 그대로 저장한다.",
        used_for=["delivery_score"],
        confidence_policy="direct_public_value_100_at_collection_time",
    ),
    SignalDefinition(
        key="sold_out",
        label="품절 여부",
        tier="direct",
        sources=["category_page", "product_detail_page"],
        source_fields=["sold_out", "is_out_of_stock"],
        extraction_method="공개 품절 여부를 불리언으로 저장한다.",
        used_for=["availability_filter", "delivery_score"],
        confidence_policy="direct_public_value_100_at_collection_time",
    ),
    SignalDefinition(
        key="color_signal",
        label="색상 분류",
        tier="refined",
        sources=["search_results_page", "product_detail_page", "review_area"],
        source_fields=["product_name", "goods_contents", "option_text", "review_text"],
        extraction_method="상품명, 옵션, 설명, 리뷰에서 색상 키워드를 추출해 표준 색상으로 매핑한다.",
        used_for=["purpose_fit_score", "filtering"],
        confidence_policy="refined_keyword_match_50_to_95",
    ),
    SignalDefinition(
        key="style_signal",
        label="스타일 분류",
        tier="refined",
        sources=["search_results_page", "product_detail_page", "review_area"],
        source_fields=["product_name", "goods_contents", "md_opinion", "review_text"],
        extraction_method="무지, 베이직, 미니멀, 오버핏 같은 키워드를 표준 스타일 태그로 매핑한다.",
        used_for=["purpose_fit_score", "age_fit_proxy_score"],
        confidence_policy="refined_keyword_match_40_to_95",
    ),
    SignalDefinition(
        key="fit_signal",
        label="핏 분류",
        tier="refined",
        sources=["product_detail_page", "review_area"],
        source_fields=["product_name", "md_opinion", "review_text", "fit_feedback"],
        extraction_method="오버핏, 루즈핏, 정핏, 슬림핏 등 착용감 키워드를 추출한다.",
        used_for=["purpose_fit_score", "review_risk_score"],
        confidence_policy="refined_keyword_match_40_to_90",
    ),
    SignalDefinition(
        key="material_wearability_signal",
        label="소재/착용감 분류",
        tier="refined",
        sources=["product_detail_page", "review_area"],
        source_fields=["goods_contents", "md_opinion", "review_text"],
        extraction_method="두께, 비침, 통기성, 부드러움, 세탁 변형 키워드를 추출한다.",
        used_for=["review_risk_score", "purpose_fit_score"],
        confidence_policy="refined_keyword_match_30_to_85",
    ),
    SignalDefinition(
        key="repurchase_keyword_signal",
        label="재구매 언급",
        tier="refined",
        sources=["review_area"],
        source_fields=["review_text"],
        extraction_method="재구매, 또 샀다, 색깔별 구매 같은 리뷰 키워드를 집계한다.",
        used_for=["repurchase_likelihood_score"],
        confidence_policy="refined_review_keyword_30_to_80",
        limitations=["재구매율 자체가 아니라 리뷰 내 언급 빈도다."],
    ),
    SignalDefinition(
        key="low_rating_issue_signal",
        label="낮은 평점 이슈",
        tier="refined",
        sources=["review_area"],
        source_fields=["review_score", "review_text"],
        extraction_method="낮은 평점 리뷰에서 사이즈, 품질, 배송, 색상 불만 키워드를 집계한다.",
        used_for=["return_risk_score", "review_risk_score"],
        confidence_policy="refined_review_keyword_30_to_80",
        limitations=["반품률 자체가 아니라 불만 가능성의 단서다."],
    ),
    SignalDefinition(
        key="purpose_fit_score",
        label="목적 적합도",
        tier="inferred",
        sources=["search_results_page", "product_detail_page", "review_area"],
        source_fields=["product_name", "category", "price", "color_signal", "style_signal"],
        extraction_method="사용자 조건과 직접/정제 지표의 일치도를 가중 합산한다.",
        used_for=["final_score"],
        confidence_policy="required_confidence_percent_from_evidence_coverage",
        limitations=["사용자 취향을 완전히 알 수 없으므로 가능성으로 표현한다."],
    ),
    SignalDefinition(
        key="age_male_40s_fit_score",
        label="40대 남성 적합도 추정",
        tier="inferred",
        sources=["ranking_page", "product_detail_page", "review_area"],
        source_fields=["ranking_position", "gender", "age_filter_context", "style_signal", "review_count", "review_score"],
        extraction_method="남성/40대 랭킹 노출과 무난한 스타일, 리뷰 지표를 조합한다.",
        used_for=["final_score", "explanation"],
        confidence_policy="required_confidence_percent_from_public_proxy_strength",
        limitations=["실제 40대 남성 구매자 수는 공개되지 않는다."],
    ),
    SignalDefinition(
        key="purchase_trust_score",
        label="구매 신뢰도 추정",
        tier="inferred",
        sources=["ranking_page", "product_detail_page", "review_area"],
        source_fields=["review_count", "review_score", "sales_label", "ranking_position"],
        extraction_method="리뷰 수, 평점, 판매 라벨, 랭킹 노출을 조합한다.",
        used_for=["final_score", "comparison"],
        confidence_policy="required_confidence_percent_from_evidence_coverage",
        limitations=["구매 전환율이나 실제 누적 구매자 원본 데이터는 공개되지 않는다."],
    ),
    SignalDefinition(
        key="return_risk_score",
        label="반품 리스크 추정",
        tier="inferred",
        sources=["review_area", "product_detail_page"],
        source_fields=["low_rating_issue_signal", "fit_signal", "material_wearability_signal"],
        extraction_method="낮은 평점 이슈와 사이즈/품질 불만 키워드를 조합한다.",
        used_for=["caution_reason", "final_score"],
        confidence_policy="required_confidence_percent_from_review_sample_size",
        limitations=["실제 반품률은 공개되지 않는다."],
    ),
    SignalDefinition(
        key="repurchase_likelihood_score",
        label="재구매 가능성 추정",
        tier="inferred",
        sources=["review_area", "product_detail_page"],
        source_fields=["repurchase_keyword_signal", "review_count", "review_score"],
        extraction_method="재구매 언급과 리뷰 지표를 조합한다.",
        used_for=["comparison", "explanation"],
        confidence_policy="required_confidence_percent_from_review_sample_size",
        limitations=["실제 재구매율은 공개되지 않는다."],
    ),
]


def get_sources() -> list[dict]:
    return [asdict(source) for source in SOURCES]


def get_signals(tier: str | None = None) -> list[dict]:
    if tier is not None and tier not in ALLOWED_TIERS:
        raise ValueError(f"Unknown signal tier: {tier}")
    signals = SIGNALS if tier is None else [signal for signal in SIGNALS if signal.tier == tier]
    return [asdict(signal) for signal in signals]


def summarize_catalog() -> dict:
    summary = {tier: 0 for tier in sorted(ALLOWED_TIERS)}
    for signal in SIGNALS:
        summary[signal.tier] += 1
    return {
        "source_count": len(SOURCES),
        "signal_count": len(SIGNALS),
        "signals_by_tier": summary,
        "confidence_required_for_inferred": all(
            "required_confidence_percent" in signal.confidence_policy
            for signal in SIGNALS
            if signal.tier == "inferred"
        ),
    }


def validate_catalog() -> list[str]:
    errors: list[str] = []
    source_keys = {source.key for source in SOURCES}
    signal_keys: set[str] = set()

    for source in SOURCES:
        if not source.key or not source.label:
            errors.append(f"Invalid source identity: {source}")
        if not source.public_fields:
            errors.append(f"Source has no public fields: {source.key}")

    for signal in SIGNALS:
        if signal.key in signal_keys:
            errors.append(f"Duplicate signal key: {signal.key}")
        signal_keys.add(signal.key)
        if signal.tier not in ALLOWED_TIERS:
            errors.append(f"Invalid tier for {signal.key}: {signal.tier}")
        unknown_sources = [source for source in signal.sources if source not in source_keys]
        if unknown_sources:
            errors.append(f"{signal.key} references unknown sources: {unknown_sources}")
        if not signal.source_fields:
            errors.append(f"Signal has no source fields: {signal.key}")
        if signal.tier == "inferred" and "required_confidence_percent" not in signal.confidence_policy:
            errors.append(f"Inferred signal lacks confidence percent policy: {signal.key}")
        if signal.tier == "direct" and "추정" in signal.label:
            errors.append(f"Direct signal label should not imply inference: {signal.key}")

    return errors


def build_collection_plan(query: str) -> dict:
    intent = parse_to_dict(query)
    target_sources = ["search_results_page", "ranking_page", "product_detail_page"]
    if intent.get("age_band") or intent.get("gender"):
        target_sources.append("review_area")
    target_signals = [
        "product_id",
        "product_name",
        "brand_name",
        "price",
        "discount_rate",
        "ranking_position",
        "review_count",
        "review_score",
        "color_signal",
        "style_signal",
        "purpose_fit_score",
        "purchase_trust_score",
    ]
    if intent.get("age_band") == "40s" and intent.get("gender") == "M":
        target_signals.append("age_male_40s_fit_score")
    return {
        "query": query,
        "parsed_intent": intent,
        "target_sources": target_sources,
        "target_signals": target_signals,
        "summary": summarize_catalog(),
        "inference_rule": "추정 지표는 score와 confidence_percent를 함께 출력해야 합니다.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Musinsa public signal catalog.")
    parser.add_argument("--tier", choices=sorted(ALLOWED_TIERS), help="Filter signals by tier")
    parser.add_argument("--summary", action="store_true", help="Print catalog summary")
    parser.add_argument("--validate", action="store_true", help="Validate catalog consistency")
    parser.add_argument("--plan", help="Build a collection plan for a shopping query")
    args = parser.parse_args()

    if args.validate:
        errors = validate_catalog()
        print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
        raise SystemExit(1 if errors else 0)
    if args.plan:
        print(json.dumps(build_collection_plan(args.plan), ensure_ascii=False, indent=2))
        return
    if args.summary:
        print(json.dumps(summarize_catalog(), ensure_ascii=False, indent=2))
        return
    print(json.dumps({"sources": get_sources(), "signals": get_signals(args.tier)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
