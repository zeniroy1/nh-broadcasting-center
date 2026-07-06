import unittest

from scripts.musinsa_proxy_metrics import SAMPLE_PRODUCT
from scripts.musinsa_scoring_model import (
    DEFAULT_QUERY,
    compare_sample_products,
    load_scoring_config,
    score_product,
    validate_scoring_model,
)


class MusinsaScoringModelTest(unittest.TestCase):
    def test_scoring_model_is_valid(self):
        self.assertEqual(validate_scoring_model(), [])

    def test_weights_sum_to_100(self):
        config = load_scoring_config()

        self.assertEqual(sum(config["weights"].values()), 100)

    def test_score_product_has_final_score_and_confidence(self):
        result = score_product(DEFAULT_QUERY, SAMPLE_PRODUCT)
        score = result["product_score"]

        self.assertIn("final_score", score)
        self.assertIn("confidence_percent", score)
        self.assertGreaterEqual(score["final_score"], 0)
        self.assertLessEqual(score["final_score"], 100)
        self.assertLessEqual(score["confidence_percent"], 88)

    def test_components_have_weights_and_limitations(self):
        result = score_product(DEFAULT_QUERY, SAMPLE_PRODUCT)
        components = result["product_score"]["components"]

        self.assertEqual(sum(component["weight"] for component in components), 100)
        for component in components:
            self.assertIn("score", component)
            self.assertIn("confidence_percent", component)
            self.assertTrue(component["limitation"])

    def test_review_purchase_and_buyer_context_are_scored(self):
        result = score_product(DEFAULT_QUERY, SAMPLE_PRODUCT)
        component_keys = {component["key"] for component in result["product_score"]["components"]}

        self.assertIn("review_purchase_evidence_score", component_keys)
        self.assertIn("buyer_context_profile_score", component_keys)

    def test_sample_comparison_is_ranked(self):
        comparison = compare_sample_products()
        scores = [product["final_score"] for product in comparison["ranked_products"]]

        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_sold_out_product_is_not_rank_ready(self):
        product = dict(SAMPLE_PRODUCT)
        product["is_sold_out"] = True
        result = score_product(DEFAULT_QUERY, product)

        self.assertFalse(result["product_score"]["rank_ready"])
        self.assertLessEqual(result["product_score"]["final_score"], 5)

    def test_visible_detail_components_use_public_product_signals_without_review_texts(self):
        strong = dict(SAMPLE_PRODUCT)
        strong.update(
            {
                "review_count": 5200,
                "review_score": 4.9,
                "ranking_position": 8,
                "male_ranking_position": 8,
                "age_40s_ranking_position": 12,
                "low_rating_issue_ratio": 0.05,
                "fit_issue_ratio": 0.08,
                "material_issue_ratio": 0.07,
            }
        )
        weak = dict(SAMPLE_PRODUCT)
        weak.update(
            {
                "review_count": 18,
                "review_score": 3.7,
                "ranking_position": 130,
                "male_ranking_position": 130,
                "age_40s_ranking_position": None,
                "low_rating_issue_ratio": 0.34,
                "fit_issue_ratio": 0.28,
                "material_issue_ratio": 0.3,
            }
        )

        strong_components = {
            component["key"]: component for component in score_product(DEFAULT_QUERY, strong)["product_score"]["components"]
        }
        weak_components = {
            component["key"]: component for component in score_product(DEFAULT_QUERY, weak)["product_score"]["components"]
        }

        self.assertGreater(
            strong_components["review_purchase_evidence_score"]["score"],
            weak_components["review_purchase_evidence_score"]["score"],
        )
        self.assertGreater(
            strong_components["buyer_context_profile_score"]["score"],
            weak_components["buyer_context_profile_score"]["score"],
        )
        self.assertGreater(strong_components["review_risk_score"]["score"], weak_components["review_risk_score"]["score"])
        self.assertEqual(strong_components["review_risk_score"]["label"], "리스크 안정성")

    def test_purpose_and_price_components_follow_requested_conditions(self):
        matched = dict(SAMPLE_PRODUCT)
        mismatched = dict(SAMPLE_PRODUCT)
        mismatched.update(
            {
                "category_label": "데님 팬츠",
                "colors": ["white"],
                "styles": ["graphic"],
                "price": 69000,
            }
        )

        matched_components = {
            component["key"]: component for component in score_product(DEFAULT_QUERY, matched)["product_score"]["components"]
        }
        mismatched_components = {
            component["key"]: component for component in score_product(DEFAULT_QUERY, mismatched)["product_score"]["components"]
        }

        self.assertGreater(matched_components["purpose_fit_score"]["score"], mismatched_components["purpose_fit_score"]["score"])
        self.assertGreater(matched_components["price_fit_score"]["score"], mismatched_components["price_fit_score"]["score"])

    def test_price_component_uses_price_range_not_purpose_score(self):
        query = "검정 반팔티 2~3만원대 남성"
        in_range = dict(SAMPLE_PRODUCT, price=29900)
        too_expensive = dict(SAMPLE_PRODUCT, price=69000)
        too_cheap = dict(SAMPLE_PRODUCT, price=12000)

        in_components = {
            component["key"]: component for component in score_product(query, in_range)["product_score"]["components"]
        }
        expensive_components = {
            component["key"]: component for component in score_product(query, too_expensive)["product_score"]["components"]
        }
        cheap_components = {
            component["key"]: component for component in score_product(query, too_cheap)["product_score"]["components"]
        }

        self.assertEqual(in_components["price_fit_score"]["score"], 100)
        self.assertLess(expensive_components["price_fit_score"]["score"], in_components["price_fit_score"]["score"])
        self.assertLess(cheap_components["price_fit_score"]["score"], in_components["price_fit_score"]["score"])
        self.assertNotEqual(
            expensive_components["price_fit_score"]["score"],
            expensive_components["purpose_fit_score"]["score"],
        )


if __name__ == "__main__":
    unittest.main()
