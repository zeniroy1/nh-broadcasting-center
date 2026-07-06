import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.musinsa_buyer_server import APP_PATH, build_recommendation_payload, build_search_trends_payload, parse_search_trends


TREND_FIXTURE = """
{"data":{"searchUrl":"https://www.musinsa.com/search/goods?keyword={keyword}","componentList":[
  {"key":"popular","items":[
    {"text":"반팔","rankIncrement":0,"landingUrl":"https://www.musinsa.com/search/goods?keyword=반팔&keywordType=popular"},
    {"text":"반바지","rankIncrement":1,"landingUrl":"https://www.musinsa.com/search/goods?keyword=반바지&keywordType=popular"}
  ],"meta":{"title":"인기 검색어","updateDate":"06.29 16:40, 기준"}},
  {"key":"rising","items":[
    {"text":"하객룩","rankIncrement":20,"landingUrl":"https://www.musinsa.com/search/goods?keyword=하객룩&keywordType=rising"}
  ],"meta":{"title":"급상승 검색어","updateDate":"06.29 16:40, 기준"}}
]}}
"""


class MusinsaBuyerServerTest(unittest.TestCase):
    def test_server_payload_uses_sample_mode_without_live_fetch(self):
        payload = build_recommendation_payload(
            "검은색 반팔 무지티를 2~3만원대에서 40대 남성이 입기 좋은 제품으로 찾아줘",
            fetch_live=False,
        )

        self.assertIn("model", payload)
        self.assertIn("summary", payload)
        self.assertGreaterEqual(payload["summary"]["scored_candidate_count"], 4)
        self.assertLessEqual(payload["summary"]["scored_candidate_count"], 5)
        self.assertEqual(payload["summary"]["keyword_learning"]["updated"], 0)
        self.assertIsNotNone(payload["summary"]["winner"])

    def test_server_payload_is_json_serializable(self):
        payload = build_recommendation_payload(fetch_live=False, query="검은색 반팔 무지티")

        encoded = json.dumps(payload, ensure_ascii=False)

        self.assertIn("recommendation_report", encoded)
        self.assertIn("collection_mode", encoded)

    def test_server_payload_accepts_excluded_product_ids(self):
        payload = build_recommendation_payload(
            fetch_live=False,
            query="검은색 반팔 무지티",
            exclude_product_ids=["sample-black-tee"],
        )

        product_ids = [
            row["product_id"]
            for row in payload["model"]["recommendation_report"]["comparison_table"]["rows"]
        ]

        self.assertNotIn("sample-black-tee", product_ids)
        self.assertEqual(payload["summary"]["excluded_product_count"], 1)

    def test_app_exposes_collapsible_search_diagnostics(self):
        html = APP_PATH.read_text(encoding="utf-8")

        self.assertIn('id="diagnosticsToggle"', html)
        self.assertIn('aria-controls="diagnostics"', html)
        self.assertIn("function syncDiagnosticsCollapse()", html)
        self.assertIn("diagnosticsCollapsed = !diagnosticsCollapsed", html)
        self.assertIn(".diagnostics.isCollapsed #diagnostics", html)

    def test_search_trends_are_parsed(self):
        trends = parse_search_trends(TREND_FIXTURE)

        self.assertEqual(trends["popular"]["title"], "인기 검색어")
        self.assertEqual(trends["popular"]["items"][0]["text"], "반팔")
        self.assertEqual(trends["popular"]["items"][1]["rank_increment"], 1)
        self.assertEqual(trends["rising"]["title"], "급상승 검색어")
        self.assertEqual(trends["rising"]["items"][0]["text"], "하객룩")

    def test_search_trends_payload_accepts_raw_json(self):
        payload = build_search_trends_payload(raw_json=TREND_FIXTURE)

        self.assertEqual(payload["source"], "raw_json")
        self.assertEqual(payload["refresh_seconds"], 60)
        self.assertEqual(payload["keyword_discovery"]["updated"], 0)
        self.assertEqual(payload["trends"]["popular"]["items"][0]["rank"], 1)

    def test_search_trends_payload_can_record_public_keyword_discovery(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            queue_path = Path(temp_dir) / "keyword_learning_queue.json"
            payload = build_search_trends_payload(
                raw_json=TREND_FIXTURE,
                record_discovery=True,
                discovery_path=queue_path,
            )

        self.assertIn("하객룩", payload["keyword_discovery"]["terms"])
        self.assertNotIn("반팔", payload["keyword_discovery"]["terms"])

    def test_search_trends_payload_records_discovery_without_explicit_path(self):
        with patch(
            "scripts.musinsa_buyer_server.update_keyword_discovery_from_terms",
            return_value={"updated": 1, "terms": ["하객룩"], "review_ready": [], "source": "search_trends:raw_json"},
        ) as recorder:
            payload = build_search_trends_payload(raw_json=TREND_FIXTURE, record_discovery=True)

        recorder.assert_called_once()
        self.assertEqual(payload["keyword_discovery"]["updated"], 1)
        self.assertEqual(payload["trends"]["popular"]["items"][0]["text"], "반팔")

    def test_search_trends_payload_keeps_trends_when_discovery_write_fails(self):
        with patch(
            "scripts.musinsa_buyer_server.update_keyword_discovery_from_terms",
            side_effect=TypeError("queue path failed"),
        ):
            payload = build_search_trends_payload(raw_json=TREND_FIXTURE, record_discovery=True)

        self.assertEqual(payload["keyword_discovery"]["updated"], 0)
        self.assertIn("keyword_discovery: queue path failed", payload["errors"])
        self.assertEqual(payload["trends"]["rising"]["items"][0]["text"], "하객룩")

    def test_search_trends_payload_falls_back_to_second_api(self):
        with patch(
            "scripts.musinsa_buyer_server.fetch_search_trend_json",
            side_effect=[RuntimeError("first failed"), TREND_FIXTURE],
        ):
            payload = build_search_trends_payload(fetch_live=True)

        self.assertIn("first failed", payload["errors"][0])
        self.assertEqual(payload["trends"]["rising"]["items"][0]["text"], "하객룩")


if __name__ == "__main__":
    unittest.main()
