import unittest

from scripts.musinsa_review_signal_schema import (
    analyze_review_texts,
    build_review_signal_blueprint,
    build_review_signal_catalog,
    validate_review_signal_blueprint,
)


QUERY = "검은색 반팔 무지티를 2~3만원대에서 40대 남성이 입기 좋은 제품으로 찾아줘"


class MusinsaReviewSignalSchemaTest(unittest.TestCase):
    def test_review_signal_blueprint_is_valid(self):
        self.assertEqual(validate_review_signal_blueprint(QUERY), [])

    def test_catalog_has_expected_review_categories(self):
        catalog = build_review_signal_catalog()
        signal_ids = {category["signal_id"] for category in catalog["categories"]}

        self.assertIn("size_negative", signal_ids)
        self.assertIn("sheerness_negative", signal_ids)
        self.assertIn("neck_durability_negative", signal_ids)
        self.assertIn("repurchase_positive", signal_ids)
        self.assertIn("age_40s_context", signal_ids)

    def test_review_metrics_have_score_confidence_and_limitation(self):
        analysis = analyze_review_texts(["정사이즈라 잘 맞고 재구매하고 싶어요."])

        for metric in analysis["metrics"]:
            self.assertGreaterEqual(metric["score"], 0)
            self.assertLessEqual(metric["score"], 100)
            self.assertLessEqual(metric["confidence_percent"], 80)
            self.assertTrue(metric["limitation"])

    def test_buyer_context_profile_metric_exists(self):
        analysis = analyze_review_texts(["남편 출근용으로 무난해서 재구매했어요."])
        metric_ids = {metric["metric_id"] for metric in analysis["metrics"]}

        self.assertIn("buyer_context_profile_score", metric_ids)

    def test_negative_review_lowers_fabric_score(self):
        positive = analyze_review_texts(["원단 좋아요. 비침 없고 탄탄합니다."])
        negative = analyze_review_texts(["얇아서 비침 있고 세탁 후 목 늘어남이 있어요."])

        positive_score = next(metric for metric in positive["metrics"] if metric["metric_id"] == "fabric_risk_review_score")
        negative_score = next(metric for metric in negative["metrics"] if metric["metric_id"] == "fabric_risk_review_score")

        self.assertGreater(positive_score["score"], negative_score["score"])

    def test_blueprint_keeps_internal_data_boundary(self):
        blueprint = build_review_signal_blueprint(QUERY)
        boundary_text = " ".join(blueprint["catalog"]["boundary"])

        self.assertIn("실제 반품률", boundary_text)
        self.assertIn("실제 재구매율", boundary_text)
        self.assertIn("실제 40대 구매자 수", boundary_text)


if __name__ == "__main__":
    unittest.main()
