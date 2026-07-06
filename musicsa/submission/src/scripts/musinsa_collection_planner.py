"""Plan Musinsa product-list collection scope from query candidates."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from musinsa_query_generator import generate_query_candidates
from musinsa_runtime_paths import resource_path


DEFAULT_CONFIG_PATH = resource_path("config", "collection_scope.json")

DEFAULT_SOURCE_LIMITS = {
    "search_results_page": {"max_items": 30, "max_pages": 2},
    "ranking_page": {"max_items": 50, "max_pages": 2},
    "category_page": {"max_items": 40, "max_pages": 2},
    "product_detail_page": {"max_items": 0, "max_pages": 0},
    "review_area": {"max_items": 0, "max_pages": 0},
}

DEFAULT_PURPOSE_MULTIPLIER = {
    "exact_match": 1.0,
    "core_search": 0.85,
    "ranking_probe": 1.0,
    "review_probe": 0.5,
    "broad_discovery": 0.6,
    "fallback": 0.4,
}

DEFAULT_SOURCE_PRIORITY = {
    "ranking_page": 100,
    "search_results_page": 90,
    "category_page": 75,
    "product_detail_page": 30,
    "review_area": 20,
}


@dataclass(frozen=True)
class CollectionJob:
    job_id: str
    query: str
    source: str
    purpose: str
    priority: int
    max_items: int
    max_pages: int
    filters: list[str]
    avoid_terms: list[str]
    reason: str


@dataclass(frozen=True)
class DedupPolicy:
    primary_key: str = "product_id"
    fallback_keys: list[str] = field(default_factory=lambda: ["product_url", "normalized_brand_name+normalized_product_name"])
    keep_rule: str = "동일 상품은 더 높은 priority의 수집 작업 결과를 우선 유지한다."


@dataclass(frozen=True)
class CollectionPolicy:
    ad_policy: str = "광고/스폰서 상품은 제외하지 않고 is_ad로 표시한다."
    sold_out_policy: str = "품절 상품은 기본 비교 후보에서 제외하되, 품절 원인 분석용으로 원본 표시는 유지할 수 있다."
    request_policy: str = "실제 수집 단계에서는 요청 간격과 재시도 제한을 둔다."
    dedup_policy: DedupPolicy = field(default_factory=DedupPolicy)


def load_collection_config(config_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if path.exists():
        with path.open("r", encoding="utf-8") as file:
            config = json.load(file)
    else:
        config = {}
    return {
        "version": config.get("version", "inline-default"),
        "source_limits": config.get("source_limits", DEFAULT_SOURCE_LIMITS),
        "purpose_multiplier": config.get("purpose_multiplier", DEFAULT_PURPOSE_MULTIPLIER),
        "source_priority": config.get("source_priority", DEFAULT_SOURCE_PRIORITY),
        "excluded_first_pass_sources": set(config.get("excluded_first_pass_sources", ["product_detail_page", "review_area"])),
        "minimum_items_for_list_source": int(config.get("minimum_items_for_list_source", 5)),
        "policy": config.get("policy", asdict(CollectionPolicy())),
    }


def validate_collection_config(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    source_limits = config["source_limits"]
    for source, limits in source_limits.items():
        if int(limits.get("max_items", -1)) < 0:
            errors.append(f"max_items must be non-negative: {source}")
        if int(limits.get("max_pages", -1)) < 0:
            errors.append(f"max_pages must be non-negative: {source}")
    for purpose, multiplier in config["purpose_multiplier"].items():
        if not 0 <= float(multiplier) <= 1:
            errors.append(f"purpose multiplier must be between 0 and 1: {purpose}")
    policy = config["policy"]
    if policy["dedup_policy"]["primary_key"] != "product_id":
        errors.append("Primary dedup key must be product_id")
    return errors


def _job_limit(source: str, purpose: str, config: dict[str, Any]) -> tuple[int, int]:
    base = config["source_limits"][source]
    multiplier = config["purpose_multiplier"].get(purpose, 0.5)
    max_items = int(round(base["max_items"] * multiplier))
    if source in config["excluded_first_pass_sources"]:
        return 0, 0
    return max(config["minimum_items_for_list_source"], max_items), base["max_pages"]


def _job_priority(candidate_priority: int, source: str, config: dict[str, Any]) -> int:
    return candidate_priority + config["source_priority"].get(source, 0)


def build_collection_plan(text: str, config_path: str | Path | None = None) -> dict[str, Any]:
    config = load_collection_config(config_path)
    query_result = generate_query_candidates(text)
    jobs: list[CollectionJob] = []
    seen: set[tuple[str, str, str]] = set()

    for candidate in query_result["candidates"]:
        for source in candidate["expected_sources"]:
            if source in config["excluded_first_pass_sources"]:
                continue
            dedup_key = (candidate["query"], source, candidate["purpose"])
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            max_items, max_pages = _job_limit(source, candidate["purpose"], config)
            jobs.append(
                CollectionJob(
                    job_id=f"job-{len(jobs) + 1:03d}",
                    query=candidate["query"],
                    source=source,
                    purpose=candidate["purpose"],
                    priority=_job_priority(candidate["priority"], source, config),
                    max_items=max_items,
                    max_pages=max_pages,
                    filters=candidate["must_apply_filters"],
                    avoid_terms=candidate["avoid_terms"],
                    reason=candidate["reason"],
                )
            )

    sorted_jobs = sorted(jobs, key=lambda job: (-job.priority, job.job_id))
    jobs = [
        CollectionJob(
            job_id=f"job-{index:03d}",
            query=job.query,
            source=job.source,
            purpose=job.purpose,
            priority=job.priority,
            max_items=job.max_items,
            max_pages=job.max_pages,
            filters=job.filters,
            avoid_terms=job.avoid_terms,
            reason=job.reason,
        )
        for index, job in enumerate(sorted_jobs, start=1)
    ]
    total_max_items = sum(job.max_items for job in jobs)
    return {
        "raw_text": text,
        "parsed_intent": query_result["parsed_intent"],
        "query_candidate_count": query_result["candidate_count"],
        "collection_job_count": len(jobs),
        "total_max_items_before_dedup": total_max_items,
        "jobs": [asdict(job) for job in jobs],
        "config_version": config["version"],
        "policy": config["policy"],
        "next_step_hint": "다음 단계에서 각 job을 실제 수집기로 연결하고 product_id 기준으로 중복 제거합니다.",
    }


def validate_collection_plan(text: str, config_path: str | Path | None = None) -> list[str]:
    errors: list[str] = []
    config = load_collection_config(config_path)
    errors.extend(validate_collection_config(config))
    plan = build_collection_plan(text, config_path)
    jobs = plan["jobs"]
    if not jobs:
        errors.append("No collection jobs generated")
    job_ids = [job["job_id"] for job in jobs]
    if len(job_ids) != len(set(job_ids)):
        errors.append("Duplicate job ids found")
    priorities = [job["priority"] for job in jobs]
    if priorities != sorted(priorities, reverse=True):
        errors.append("Jobs are not sorted by priority")
    for job in jobs:
        if job["source"] not in config["source_limits"]:
            errors.append(f"Unknown source: {job['source']}")
        if job["source"] in {"search_results_page", "ranking_page", "category_page"} and job["max_items"] <= 0:
            errors.append(f"List source has no item limit: {job['job_id']}")
        if not job["filters"]:
            errors.append(f"Job has no filters: {job['job_id']}")
    policy = plan["policy"]
    if policy["dedup_policy"]["primary_key"] != "product_id":
        errors.append("Primary dedup key must be product_id")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Musinsa product-list collection plan.")
    parser.add_argument("query", nargs="?", help="Natural-language shopping request")
    parser.add_argument("--config", help="Optional collection scope JSON config path")
    parser.add_argument("--validate", action="store_true", help="Validate collection plan")
    args = parser.parse_args()

    query = args.query or "검은색 반팔 무지티를 2~3만원대에서 40대 남성이 입기 좋은 제품으로 찾아줘"
    if args.validate:
        errors = validate_collection_plan(query, args.config)
        print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
        raise SystemExit(1 if errors else 0)
    print(json.dumps(build_collection_plan(query, args.config), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
