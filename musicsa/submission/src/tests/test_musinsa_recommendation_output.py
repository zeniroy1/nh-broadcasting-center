import unittest

from scripts.musinsa_recommendation_output import (
    OUTPUT_BOUNDARIES,
    build_recommendation_report,
    validate_recommendation_report,
)


class MusinsaRecommendationOutputTest(unittest.TestCase):
    def test_recommendation_report_is_valid(self):
        self.assertEqual(validate_recommendation_report(), [])

    def test_report_has_comparison_table_and_cards(self):
        report = build_recommendation_report()

        self.assertEqual(report["recommendation_count"], 5)
        self.assertEqual(len(report["comparison_table"]["rows"]), 5)
        self.assertEqual(len(report["recommendation_cards"]), 5)

    def test_first_candidate_is_ranked_by_score(self):
        report = build_recommendation_report()
        scores = [row["final_score"] for row in report["comparison_table"]["rows"]]

        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(report["winner_product_id"], report["recommendation_cards"][0]["product_id"])

    def test_cards_expose_reasons_evidence_and_cautions(self):
        report = build_recommendation_report()

        for card in report["recommendation_cards"]:
            self.assertTrue(card["reasons"])
            self.assertTrue(card["public_evidence"])
            self.assertTrue(card["cautions"])
            self.assertLessEqual(card["confidence_percent"], 88)

    def test_visualization_data_supports_bar_and_donut_charts(self):
        report = build_recommendation_report()
        bars = report["visualizations"]["score_bar_chart"]

        self.assertEqual(len(bars), 5)
        self.assertIn("세로 막대그래프", report["visualizations"]["chart_policy"])
        self.assertEqual(len({bar["bar_color"] for bar in bars}), 5)
        for bar in bars:
            self.assertLessEqual(len(bar["short_label"]), 4)
        self.assertEqual(report["shortlist_detail"]["selected_count"], 3)
        for panel in report["shortlist_detail"]["detail_panels"]:
            self.assertGreaterEqual(len(panel["component_segments"]), 5)
            self.assertIn("타겟 적합도", {segment["label"] for segment in panel["component_segments"]})
            self.assertTrue(panel["detail_questions"])

    def test_detail_risk_is_displayed_as_higher_means_riskier(self):
        report = build_recommendation_report()
        first_panel = report["shortlist_detail"]["detail_panels"][0]
        risk_segment = next(
            segment for segment in first_panel["component_segments"] if segment["key"] == "review_risk_score"
        )

        self.assertEqual(risk_segment["label"], "리스크")
        self.assertLess(risk_segment["score"], 50)

    def test_detail_segments_expose_low_confidence_unknown_status(self):
        report = build_recommendation_report(
            query="검정 반팔티 2~3만원대 남성",
            candidates=[
                {
                    "product_id": "missing-review",
                    "product_name": "블랙 반팔 티셔츠",
                    "brand_name": "리뷰미확인",
                    "category_label": "반팔 티셔츠",
                    "colors": ["black"],
                    "styles": ["basic"],
                    "price": 29900,
                    "gender": "M",
                    "review_count": 0,
                    "review_score": 0,
                    "ranking_position": None,
                    "plus_delivery": None,
                    "is_sold_out": False,
                }
            ],
        )
        first_panel = report["shortlist_detail"]["detail_panels"][0]
        segments = {segment["key"]: segment for segment in first_panel["component_segments"]}

        self.assertIn("evidence_status", segments["review_purchase_evidence_score"])
        self.assertEqual(segments["review_risk_score"]["evidence_status"], "미확인")

    def test_custom_shortlist_uses_selected_three_products(self):
        report = build_recommendation_report(
            shortlist_product_ids=["sample-premium-tee", "sample-budget-tee", "sample-athletic-tee"]
        )
        selected_ids = [panel["product_id"] for panel in report["shortlist_detail"]["detail_panels"]]

        self.assertEqual(selected_ids, ["sample-premium-tee", "sample-budget-tee", "sample-athletic-tee"])

    def test_boundaries_keep_public_proxy_language(self):
        text = " ".join(OUTPUT_BOUNDARIES)

        self.assertIn("실제 구매자 수", text)
        self.assertIn("confidence_percent", text)

    def test_empty_candidates_do_not_fall_back_to_samples(self):
        report = build_recommendation_report(candidates=[])

        self.assertEqual(report["recommendation_count"], 0)
        self.assertEqual(report["comparison_table"]["rows"], [])
        self.assertEqual(report["winner_product_id"], None)


if __name__ == "__main__":
    unittest.main()
