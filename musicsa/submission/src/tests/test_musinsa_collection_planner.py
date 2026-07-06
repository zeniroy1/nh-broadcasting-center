import json
import tempfile
import unittest
from pathlib import Path

from scripts.musinsa_collection_planner import (
    build_collection_plan,
    load_collection_config,
    validate_collection_config,
    validate_collection_plan,
)


QUERY = "검은색 반팔 무지티를 2~3만원대에서 40대 남성이 입기 좋은 제품으로 찾아줘"


class MusinsaCollectionPlannerTest(unittest.TestCase):
    def test_collection_plan_is_valid(self):
        self.assertEqual(validate_collection_plan(QUERY), [])

    def test_plan_has_jobs_and_policy(self):
        plan = build_collection_plan(QUERY)

        self.assertGreater(plan["collection_job_count"], 0)
        self.assertGreater(plan["total_max_items_before_dedup"], 0)
        self.assertEqual(plan["policy"]["dedup_policy"]["primary_key"], "product_id")

    def test_jobs_are_sorted_by_priority(self):
        plan = build_collection_plan(QUERY)
        priorities = [job["priority"] for job in plan["jobs"]]

        self.assertEqual(priorities, sorted(priorities, reverse=True))

    def test_ranking_and_search_jobs_exist(self):
        plan = build_collection_plan(QUERY)
        sources = {job["source"] for job in plan["jobs"]}

        self.assertIn("ranking_page", sources)
        self.assertIn("search_results_page", sources)

    def test_filters_are_preserved(self):
        plan = build_collection_plan(QUERY)

        for job in plan["jobs"]:
            self.assertIn("price:20000-39999", job["filters"])
            self.assertIn("gender:M", job["filters"])

    def test_default_config_is_externalized(self):
        config = load_collection_config()

        self.assertEqual(config["version"], "0.1.0")
        self.assertEqual(config["source_limits"]["ranking_page"]["max_items"], 50)
        self.assertEqual(validate_collection_config(config), [])

    def test_plan_exposes_config_version(self):
        plan = build_collection_plan(QUERY)

        self.assertEqual(plan["config_version"], "0.1.0")

    def test_custom_config_changes_collection_scope(self):
        custom_config = {
            "version": "custom-test",
            "source_limits": {
                "search_results_page": {"max_items": 10, "max_pages": 1},
                "ranking_page": {"max_items": 12, "max_pages": 1},
                "category_page": {"max_items": 8, "max_pages": 1},
                "product_detail_page": {"max_items": 0, "max_pages": 0},
                "review_area": {"max_items": 0, "max_pages": 0},
            },
            "purpose_multiplier": {
                "exact_match": 1.0,
                "core_search": 0.5,
                "ranking_probe": 1.0,
                "review_probe": 0.5,
                "broad_discovery": 0.5,
                "fallback": 0.5,
            },
            "source_priority": {
                "ranking_page": 100,
                "search_results_page": 90,
                "category_page": 75,
                "product_detail_page": 30,
                "review_area": 20,
            },
            "excluded_first_pass_sources": ["product_detail_page", "review_area"],
            "minimum_items_for_list_source": 3,
            "policy": {
                "ad_policy": "광고 상품은 is_ad로 표시한다.",
                "sold_out_policy": "품절 상품은 기본 비교 후보에서 제외한다.",
                "request_policy": "요청 간격과 재시도 제한을 둔다.",
                "dedup_policy": {
                    "primary_key": "product_id",
                    "fallback_keys": ["product_url", "normalized_brand_name+normalized_product_name"],
                    "keep_rule": "높은 priority 결과를 우선 유지한다.",
                },
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "collection_scope.json"
            config_path.write_text(json.dumps(custom_config, ensure_ascii=False), encoding="utf-8")
            plan = build_collection_plan(QUERY, config_path)

        self.assertEqual(plan["config_version"], "custom-test")
        self.assertLess(plan["total_max_items_before_dedup"], 444)


if __name__ == "__main__":
    unittest.main()
