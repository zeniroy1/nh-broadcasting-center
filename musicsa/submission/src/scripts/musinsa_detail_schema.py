"""Design product-detail collection schema without performing live requests."""

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

from musinsa_collection_planner import build_collection_plan


@dataclass(frozen=True)
class DetailField:
    field_name: str
    label: str
    value_type: str
    metric_tier: str
    source_area: str
    required: bool
    confidence_percent: int
    parser_rule: str
    limitation: str


@dataclass(frozen=True)
class DetailCollectionTask:
    task_id: str
    from_collection_job_id: str
    source_query: str
    detail_source: str
    required_input_keys: list[str]
    fields_to_collect: list[str]
    priority: int
    reason: str


DETAIL_FIELDS = [
    DetailField("product_id", "상품 ID", "string", "direct", "detail_url_or_payload", True, 100, "상품 URL 또는 페이지 초기 데이터의 식별자를 보존한다.", "공개 페이지에 식별자가 없으면 URL을 보조 키로 사용한다."),
    DetailField("product_url", "상품 URL", "url", "direct", "detail_url", True, 100, "목록에서 전달된 URL을 정규화한다.", "URL 구조 변경 시 파서 수정이 필요하다."),
    DetailField("product_name", "상품명", "string", "direct", "product_header", True, 100, "상세 헤더의 상품명을 공백 정규화한다.", "브랜드명과 결합된 제목이면 분리 규칙이 필요하다."),
    DetailField("brand_name", "브랜드", "string", "direct", "product_header", True, 100, "브랜드 텍스트 또는 브랜드 링크명을 수집한다.", "영문/국문 표기가 함께 있으면 대표 표기를 선택한다."),
    DetailField("normal_price", "정상가", "integer", "direct", "price_area", False, 100, "숫자와 통화 기호를 분리해 원 단위 정수로 저장한다.", "정상가가 숨겨진 상품은 비어 있을 수 있다."),
    DetailField("sale_price", "판매가", "integer", "direct", "price_area", True, 100, "현재 노출 판매가를 원 단위 정수로 저장한다.", "쿠폰/회원가가 별도이면 별도 필드가 필요하다."),
    DetailField("discount_rate", "할인율", "float", "direct", "price_area", False, 100, "노출 할인율을 숫자로 저장한다.", "할인율 미노출 시 가격 차이로 계산할 수 있다."),
    DetailField("image_urls", "상품 이미지", "list[url]", "direct", "image_area", False, 100, "대표 이미지와 보조 이미지 URL을 순서대로 보존한다.", "지연 로딩 이미지 속성이 바뀌면 보완이 필요하다."),
    DetailField("category_path", "카테고리", "list[string]", "direct", "breadcrumb", False, 100, "breadcrumb 또는 상세 메타 카테고리를 배열로 저장한다.", "카테고리 노출이 없으면 목록 카테고리를 승계한다."),
    DetailField("gender_target", "성별 대상", "string", "refined", "category_or_tags", False, 90, "카테고리, 태그, 목록 필터를 조합해 남성/여성/공용으로 정제한다.", "명시 필드가 아니면 추정이 섞일 수 있다."),
    DetailField("season", "시즌", "string", "refined", "product_meta", False, 90, "노출 시즌 또는 상품 태그를 표준 시즌 값으로 매핑한다.", "시즌 정보가 없는 기본 상품은 unknown으로 둔다."),
    DetailField("delivery_type", "배송 유형", "string", "direct", "delivery_area", False, 100, "플러스배송, 일반배송 등 노출 배송 문구를 표준화한다.", "지역/회원 조건별 배송 차이는 반영하지 않는다."),
    DetailField("estimated_delivery_date", "배송 예정일", "string", "direct", "delivery_area", False, 100, "상세 페이지의 배송 예정 문구를 원문과 정규화 값으로 저장한다.", "실제 배송 확정일이 아니다."),
    DetailField("review_count", "리뷰 수", "integer", "direct", "review_summary", False, 100, "리뷰 요약 영역의 숫자를 정수로 변환한다.", "리뷰 영역 로딩 실패 시 비어 있을 수 있다."),
    DetailField("review_score", "평점", "float", "direct", "review_summary", False, 100, "평점 숫자를 소수로 저장한다.", "평점 기준이 플랫폼에서 바뀌면 해석 기준도 바뀐다."),
    DetailField("description_text", "상품 설명", "string", "direct", "description_area", False, 100, "상품 설명의 텍스트를 줄바꿈 기준으로 정리한다.", "이미지 안에만 있는 설명은 OCR 없이는 제한된다."),
    DetailField("material_keywords", "소재 키워드", "list[string]", "refined", "description_area", False, 88, "면, 폴리, 스판 등 소재 단어를 사전 기반으로 추출한다.", "이미지 설명에만 있는 소재는 누락될 수 있다."),
    DetailField("fit_keywords", "핏 키워드", "list[string]", "refined", "description_area", False, 88, "오버핏, 레귤러핏, 슬림핏 등 핏 단어를 사전 기반으로 추출한다.", "마케팅 문구와 실제 착용감은 다를 수 있다."),
    DetailField("size_options", "사이즈 옵션", "list[string]", "direct", "option_area", False, 100, "선택 가능한 사이즈 옵션과 품절 표시를 함께 저장한다.", "옵션이 스크립트로 늦게 로딩되면 별도 처리한다."),
    DetailField("is_sold_out", "품절 여부", "boolean", "direct", "option_area", False, 100, "전체 품절 또는 선택 가능 옵션 없음 여부를 boolean으로 저장한다.", "일부 사이즈 품절은 size_options에서 따로 본다."),
    DetailField("ranking_badges", "랭킹 기록", "list[string]", "direct", "badge_area", False, 100, "상세 페이지에 노출된 랭킹/베스트 배지를 원문 보존한다.", "노출되지 않는 내부 랭킹 기록은 알 수 없다."),
    DetailField("plain_style_fit", "무지/베이직 적합 추정", "integer", "inferred", "name_description_image_alt", False, 82, "상품명, 설명, 이미지 대체 텍스트의 무지/로고/프린트 단서를 점수화한다.", "이미지 자체의 로고 크기를 정밀 판단하지 않는다."),
    DetailField("age_40s_context_fit", "40대 타겟 적합 추정", "integer", "inferred", "category_description_review_summary", False, 72, "베이직, 과하지 않음, 출근, 남편 등 공개 문구 단서를 조합한다.", "실제 40대 구매자 수나 전환율이 아니다."),
]


def build_detail_schema() -> dict[str, Any]:
    fields = [asdict(field) for field in DETAIL_FIELDS]
    return {
        "schema_version": "0.1.0",
        "field_count": len(fields),
        "fields": fields,
        "confidence_rule": "direct는 공개 노출값, refined는 정제값, inferred는 추정값이며 inferred는 confidence_percent를 반드시 표시한다.",
        "internal_data_boundary": [
            "실제 구매자 수를 수집하지 않는다.",
            "연령대별 구매 비율을 수집하지 않는다.",
            "무신사 내부 랭킹 알고리즘을 추정값처럼 단정하지 않는다.",
        ],
    }


def build_detail_collection_blueprint(text: str, max_tasks: int = 5) -> dict[str, Any]:
    collection_plan = build_collection_plan(text)
    tasks: list[DetailCollectionTask] = []
    fields_to_collect = [field.field_name for field in DETAIL_FIELDS]

    for job in collection_plan["jobs"][:max_tasks]:
        tasks.append(
            DetailCollectionTask(
                task_id=f"detail-{len(tasks) + 1:03d}",
                from_collection_job_id=job["job_id"],
                source_query=job["query"],
                detail_source="product_detail_page",
                required_input_keys=["product_id", "product_url"],
                fields_to_collect=fields_to_collect,
                priority=job["priority"],
                reason="목록 후보의 product_id/product_url을 이용해 상세 공개 지표를 보강한다.",
            )
        )

    return {
        "raw_text": text,
        "collection_config_version": collection_plan["config_version"],
        "source_collection_job_count": collection_plan["collection_job_count"],
        "detail_task_count": len(tasks),
        "tasks": [asdict(task) for task in tasks],
        "detail_schema": build_detail_schema(),
        "next_step_hint": "다음 단계에서 리뷰 키워드 사전과 리뷰 기반 리스크 요약 규칙을 연결합니다.",
    }


def validate_detail_blueprint(text: str) -> list[str]:
    errors: list[str] = []
    blueprint = build_detail_collection_blueprint(text)
    schema = blueprint["detail_schema"]
    fields = schema["fields"]
    field_names = {field["field_name"] for field in fields}
    required = {"product_id", "product_url", "product_name", "brand_name", "sale_price"}
    missing_required = required - field_names
    if missing_required:
        errors.append(f"Missing required detail fields: {sorted(missing_required)}")
    for field in fields:
        if field["metric_tier"] == "inferred" and field["confidence_percent"] > 85:
            errors.append(f"Inferred field confidence is too high: {field['field_name']}")
        if field["metric_tier"] == "inferred" and not field["limitation"]:
            errors.append(f"Inferred field has no limitation: {field['field_name']}")
    if not blueprint["tasks"]:
        errors.append("No detail collection tasks generated")
    for task in blueprint["tasks"]:
        if "product_id" not in task["required_input_keys"] or "product_url" not in task["required_input_keys"]:
            errors.append(f"Detail task lacks required input keys: {task['task_id']}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Musinsa product-detail collection blueprint.")
    parser.add_argument("query", nargs="?", help="Natural-language shopping request")
    parser.add_argument("--validate", action="store_true", help="Validate detail blueprint")
    parser.add_argument("--max-tasks", type=int, default=5, help="Maximum detail tasks to generate")
    args = parser.parse_args()

    query = args.query or "검은색 반팔 무지티를 2~3만원대에서 40대 남성이 입기 좋은 제품으로 찾아줘"
    if args.validate:
        errors = validate_detail_blueprint(query)
        print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
        raise SystemExit(1 if errors else 0)
    print(json.dumps(build_detail_collection_blueprint(query, args.max_tasks), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
