"""Design review-based support signals without scraping live reviews."""

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

from musinsa_detail_schema import build_detail_collection_blueprint
from musinsa_runtime_paths import resource_path


DEFAULT_CONFIG_PATH = resource_path("config", "review_signal_keywords.json")
DEFAULT_SAMPLE_REVIEWS = [
    "정사이즈로 잘 맞고 원단이 탄탄해서 출근할 때도 무난합니다.",
    "검은색이라 비침 없고 기본핏이라 남편이 편하게 입어요.",
    "세탁 후 목 늘어남은 아직 없고 재구매 생각 있습니다.",
    "생각보다 얇아 한여름에는 좋지만 속이 비치는 느낌이 조금 있습니다.",
]


@dataclass(frozen=True)
class ReviewSignalCategory:
    signal_id: str
    label: str
    polarity: str
    risk_area: str
    keywords: list[str]
    weight: float
    confidence_cap: int
    interpretation: str


@dataclass(frozen=True)
class ReviewMetric:
    metric_id: str
    label: str
    score: int
    confidence_percent: int
    evidence: list[str]
    limitation: str


def load_review_signal_config(config_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    with path.open("r", encoding="utf-8") as file:
        config = json.load(file)
    return config


def build_review_signal_catalog(config_path: str | Path | None = None) -> dict[str, Any]:
    config = load_review_signal_config(config_path)
    categories = [ReviewSignalCategory(**category) for category in config["categories"]]
    return {
        "catalog_version": config["version"],
        "review_sample_limit": config["review_sample_limit"],
        "category_count": len(categories),
        "categories": [asdict(category) for category in categories],
        "boundary": [
            "리뷰 키워드는 실제 반품률이 아니다.",
            "재구매 언급은 실제 재구매율이 아니다.",
            "40대 타겟 키워드는 실제 40대 구매자 수가 아니다.",
        ],
    }


def _find_keyword_hits(text: str, keywords: list[str]) -> list[str]:
    normalized = text.casefold()
    return [keyword for keyword in keywords if keyword.casefold() in normalized]


def _confidence(base_cap: int, sample_count: int, hit_count: int) -> int:
    if hit_count == 0:
        return min(35, base_cap)
    sample_factor = min(1.0, sample_count / 20)
    hit_factor = min(1.0, hit_count / 5)
    return int(round(min(base_cap, 45 + 35 * sample_factor + 20 * hit_factor)))


def _score_from_balance(positive: float, negative: float, base: int = 70) -> int:
    score = base + int(round(positive * 8)) - int(round(negative * 12))
    return max(0, min(100, score))


def analyze_review_texts(review_texts: list[str], config_path: str | Path | None = None) -> dict[str, Any]:
    catalog = build_review_signal_catalog(config_path)
    categories = catalog["categories"]
    signal_hits: list[dict[str, Any]] = []

    for category in categories:
        evidence: list[str] = []
        hit_count = 0
        for review in review_texts:
            hits = _find_keyword_hits(review, category["keywords"])
            if hits:
                hit_count += len(hits)
                evidence.append(f"{', '.join(hits)}")
        signal_hits.append(
            {
                "signal_id": category["signal_id"],
                "label": category["label"],
                "polarity": category["polarity"],
                "risk_area": category["risk_area"],
                "hit_count": hit_count,
                "weighted_count": round(hit_count * float(category["weight"]), 2),
                "confidence_percent": _confidence(int(category["confidence_cap"]), len(review_texts), hit_count),
                "evidence": evidence[:5],
                "interpretation": category["interpretation"],
            }
        )

    by_id = {signal["signal_id"]: signal for signal in signal_hits}
    size_positive = by_id["size_positive"]["weighted_count"] + by_id["fit_positive"]["weighted_count"]
    size_negative = by_id["size_negative"]["weighted_count"] + by_id["fit_negative"]["weighted_count"]
    fabric_positive = by_id["fabric_positive"]["weighted_count"] + by_id["sheerness_positive"]["weighted_count"]
    fabric_negative = (
        by_id["fabric_negative"]["weighted_count"]
        + by_id["sheerness_negative"]["weighted_count"]
        + by_id["neck_durability_negative"]["weighted_count"]
        + by_id["laundry_deformation_negative"]["weighted_count"]
    )
    repurchase = by_id["repurchase_positive"]["weighted_count"]
    age_context = by_id["age_40s_context"]["weighted_count"]

    metrics = [
        ReviewMetric(
            "size_fit_review_score",
            "리뷰 기반 사이즈/핏 안정성",
            _score_from_balance(size_positive, size_negative, 72),
            min(78, max(by_id["size_positive"]["confidence_percent"], by_id["size_negative"]["confidence_percent"])),
            by_id["size_positive"]["evidence"] + by_id["fit_positive"]["evidence"],
            "리뷰 키워드 기반 단서이며 실제 교환/반품률이 아니다.",
        ),
        ReviewMetric(
            "fabric_risk_review_score",
            "리뷰 기반 원단/비침 리스크",
            _score_from_balance(fabric_positive, fabric_negative, 74),
            min(76, max(by_id["fabric_positive"]["confidence_percent"], by_id["fabric_negative"]["confidence_percent"])),
            by_id["fabric_positive"]["evidence"] + by_id["sheerness_positive"]["evidence"],
            "원단 만족/불만 표현을 기반으로 한 보조 지표다.",
        ),
        ReviewMetric(
            "repurchase_mention_score",
            "재구매 언급 점수",
            max(0, min(100, 45 + int(round(repurchase * 12)))),
            by_id["repurchase_positive"]["confidence_percent"],
            by_id["repurchase_positive"]["evidence"],
            "재구매 언급 수는 실제 재구매율이 아니다.",
        ),
        ReviewMetric(
            "age_40s_context_review_score",
            "리뷰 기반 40대 타겟 적합 추정",
            max(0, min(100, 50 + int(round(age_context * 9)))),
            by_id["age_40s_context"]["confidence_percent"],
            by_id["age_40s_context"]["evidence"],
            "40대 타겟 키워드는 실제 40대 구매자 수가 아니다.",
        ),
        ReviewMetric(
            "buyer_context_profile_score",
            "리뷰 기반 타겟 적합도 추정",
            max(0, min(100, 48 + int(round((age_context + repurchase) * 7)))),
            min(72, max(by_id["age_40s_context"]["confidence_percent"], by_id["repurchase_positive"]["confidence_percent"])),
            by_id["age_40s_context"]["evidence"] + by_id["repurchase_positive"]["evidence"],
            "리뷰 키워드로 타겟 적합도를 추정하지만 실제 구매자 속성 통계가 아니다.",
        ),
    ]

    return {
        "review_count_analyzed": len(review_texts),
        "signal_hits": signal_hits,
        "metrics": [asdict(metric) for metric in metrics],
        "summary": {
            "positive_signal_count": sum(signal["hit_count"] for signal in signal_hits if signal["polarity"] == "positive"),
            "negative_signal_count": sum(signal["hit_count"] for signal in signal_hits if signal["polarity"] == "negative"),
            "context_signal_count": sum(signal["hit_count"] for signal in signal_hits if signal["polarity"] == "context"),
        },
    }


def build_review_signal_blueprint(text: str, review_texts: list[str] | None = None) -> dict[str, Any]:
    detail_blueprint = build_detail_collection_blueprint(text)
    reviews = review_texts if review_texts is not None else DEFAULT_SAMPLE_REVIEWS
    return {
        "raw_text": text,
        "detail_task_count": detail_blueprint["detail_task_count"],
        "review_source": "review_area",
        "required_input_keys": ["product_id", "product_url"],
        "catalog": build_review_signal_catalog(),
        "analysis_simulation": analyze_review_texts(reviews),
        "next_step_hint": "다음 단계에서 상세 지표와 리뷰 보조 지표를 점수화 모델로 합칩니다.",
    }


def validate_review_signal_blueprint(text: str) -> list[str]:
    errors: list[str] = []
    blueprint = build_review_signal_blueprint(text)
    catalog = blueprint["catalog"]
    if catalog["category_count"] < 10:
        errors.append("Review signal catalog is too small")
    for category in catalog["categories"]:
        if not category["keywords"]:
            errors.append(f"Review signal has no keywords: {category['signal_id']}")
        if category["confidence_cap"] > 80:
            errors.append(f"Review signal confidence cap is too high: {category['signal_id']}")
    for metric in blueprint["analysis_simulation"]["metrics"]:
        if not 0 <= metric["score"] <= 100:
            errors.append(f"Metric score out of range: {metric['metric_id']}")
        if metric["confidence_percent"] > 80:
            errors.append(f"Review metric confidence is too high: {metric['metric_id']}")
        if not metric["limitation"]:
            errors.append(f"Metric lacks limitation: {metric['metric_id']}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Musinsa review signal blueprint.")
    parser.add_argument("query", nargs="?", help="Natural-language shopping request")
    parser.add_argument("--validate", action="store_true", help="Validate review signal blueprint")
    args = parser.parse_args()

    query = args.query or "검은색 반팔 무지티를 2~3만원대에서 40대 남성이 입기 좋은 제품으로 찾아줘"
    if args.validate:
        errors = validate_review_signal_blueprint(query)
        print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
        raise SystemExit(1 if errors else 0)
    print(json.dumps(build_review_signal_blueprint(query), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
