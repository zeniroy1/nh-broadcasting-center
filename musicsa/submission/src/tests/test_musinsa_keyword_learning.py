import tempfile
import unittest
from pathlib import Path

from scripts.musinsa_keyword_learning import (
    is_unknown_dictionary_term,
    load_keyword_learning_queue,
    summarize_keyword_learning_queue,
    update_keyword_discovery_from_terms,
    update_keyword_learning_queue,
)


class TestMusinsaKeywordLearning(unittest.TestCase):
    def test_unknown_free_terms_are_recorded_without_auto_promotion(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            queue_path = Path(temp_dir) / "keyword_learning_queue.json"
            result = update_keyword_learning_queue(
                "버켄스탁",
                {"free_terms": ["버켄스탁"]},
                {"counts": {"filtered": 0, "similar_candidates": 14}},
                queue_path,
                now="2026-06-30T00:00:00+00:00",
            )
            payload = load_keyword_learning_queue(queue_path)
            item = payload["terms"][0]

            self.assertEqual(result["updated"], 1)
            self.assertEqual(item["term"], "버켄스탁")
            self.assertEqual(item["status"], "pending_review")
            self.assertEqual(item["count"], 1)
            self.assertFalse(item["promotion_ready"])
            self.assertEqual(item["max_public_match_count"], 14)

    def test_repeated_unknown_keyword_becomes_review_ready(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            queue_path = Path(temp_dir) / "keyword_learning_queue.json"
            for index in range(3):
                update_keyword_learning_queue(
                    f"버켄스탁 검색 {index}",
                    {"free_terms": ["버켄스탁"]},
                    {"counts": {"filtered": 0, "similar_candidates": 14}},
                    queue_path,
                    now=f"2026-06-30T00:00:0{index}+00:00",
                )

            summary = summarize_keyword_learning_queue(queue_path)
            payload = load_keyword_learning_queue(queue_path)

            self.assertEqual(summary["total_terms"], 1)
            self.assertEqual(summary["promotion_ready"], ["버켄스탁"])
            self.assertTrue(payload["terms"][0]["promotion_ready"])

    def test_known_empty_terms_do_not_write_queue(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            queue_path = Path(temp_dir) / "keyword_learning_queue.json"
            result = update_keyword_learning_queue(
                "검정 반팔티",
                {"free_terms": []},
                {"counts": {"filtered": 5, "similar_candidates": 0}},
                queue_path,
            )

            self.assertEqual(result["updated"], 0)
            self.assertFalse(queue_path.exists())

    def test_public_trend_discovery_records_only_unknown_dictionary_terms_once_per_day(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            queue_path = Path(temp_dir) / "keyword_learning_queue.json"
            first = update_keyword_discovery_from_terms(
                ["반팔", "하객룩", "하객룩"],
                "search_trends:test",
                queue_path,
                now="2026-06-30T00:00:00+00:00",
            )
            second = update_keyword_discovery_from_terms(
                ["하객룩"],
                "search_trends:test",
                queue_path,
                now="2026-06-30T01:00:00+00:00",
            )
            next_day = update_keyword_discovery_from_terms(
                ["하객룩"],
                "search_trends:test",
                queue_path,
                now="2026-07-01T00:00:00+00:00",
            )
            payload = load_keyword_learning_queue(queue_path)
            item = payload["terms"][0]

            self.assertEqual(first["terms"], ["하객룩"])
            self.assertEqual(second["updated"], 0)
            self.assertEqual(next_day["updated"], 1)
            self.assertEqual(item["term"], "하객룩")
            self.assertEqual(item["count"], 2)
            self.assertIn("search_trends:test", item["sources"])

    def test_dictionary_known_terms_are_not_discovery_candidates(self):
        self.assertFalse(is_unknown_dictionary_term("반팔"))
        self.assertFalse(is_unknown_dictionary_term("차콜"))
        self.assertTrue(is_unknown_dictionary_term("하객룩"))


if __name__ == "__main__":
    unittest.main()
