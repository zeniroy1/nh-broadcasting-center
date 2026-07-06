import unittest

from scripts.musinsa_proxy_metrics import (
    PROXY_METRICS,
    SAMPLE_PRODUCT,
    calculate_proxy_metrics,
    validate_proxy_definitions,
)


QUERY = "검은색 반팔 무지티를 2~3만원대에서 40대 남성이 입기 좋은 제품으로 찾아줘"


class MusinsaProxyMetricsTest(unittest.TestCase):
    def test_proxy_definitions_are_valid(self):
        self.assertEqual(validate_proxy_definitions(), [])

    def test_every_proxy_metric_has_score_and_confidence(self):
        result = calculate_proxy_metrics(QUERY, SAMPLE_PRODUCT)

        self.assertEqual(len(result["metrics"]), len(PROXY_METRICS))
        for metric in result["metrics"]:
            self.assertIn("score", metric)
            self.assertIn("confidence_percent", metric)
            self.assertGreaterEqual(metric["score"], 0)
            self.assertLessEqual(metric["score"], 100)
            self.assertGreaterEqual(metric["confidence_percent"], 0)
            self.assertLessEqual(metric["confidence_percent"], 100)
            self.assertTrue(metric["limitations"])

    def test_purpose_fit_is_high_for_matching_sample(self):
        result = calculate_proxy_metrics(QUERY, SAMPLE_PRODUCT)
        purpose = next(metric for metric in result["metrics"] if metric["key"] == "purpose_fit_score")

        self.assertGreaterEqual(purpose["score"], 90)
        self.assertGreaterEqual(purpose["confidence_percent"], 90)
        self.assertLessEqual(purpose["confidence_percent"], 95)

    def test_musinsa_category_aliases_match_purpose_fit(self):
        product = {**SAMPLE_PRODUCT, "category_label": "반팔 티셔츠"}
        result = calculate_proxy_metrics("검정 무지 반소매 티셔츠 2만원대 남성", product)
        purpose = next(metric for metric in result["metrics"] if metric["key"] == "purpose_fit_score")

        self.assertEqual(result["evidence_map"]["category_match"], 1.0)
        self.assertGreaterEqual(purpose["confidence_percent"], 90)

    def test_internal_proxy_confidence_is_capped(self):
        result = calculate_proxy_metrics(QUERY, SAMPLE_PRODUCT)
        age_metric = next(metric for metric in result["metrics"] if metric["key"] == "age_male_40s_fit_score")
        return_metric = next(metric for metric in result["metrics"] if metric["key"] == "return_risk_score")

        self.assertLessEqual(age_metric["confidence_percent"], 85)
        self.assertLessEqual(return_metric["confidence_percent"], 75)

    def test_missing_evidence_reduces_confidence(self):
        sparse_product = {
            "product_id": "sparse",
            "product_name": "블랙 티셔츠",
            "category_label": "반팔 티셔츠",
            "colors": ["black"],
            "styles": ["plain"],
            "price": 29900,
        }
        result = calculate_proxy_metrics(QUERY, sparse_product)
        age_metric = next(metric for metric in result["metrics"] if metric["key"] == "age_male_40s_fit_score")

        self.assertLess(age_metric["confidence_percent"], 60)
        self.assertIn("male_ranking_exposed", age_metric["missing_evidence"])

    def test_review_count_is_purchase_reaction_evidence(self):
        result = calculate_proxy_metrics(QUERY, SAMPLE_PRODUCT)
        metric = next(metric for metric in result["metrics"] if metric["key"] == "review_purchase_evidence_score")

        self.assertGreaterEqual(metric["score"], 90)
        self.assertLessEqual(metric["confidence_percent"], 86)
        self.assertTrue(any("실제 구매자 수" in limitation for limitation in metric["limitations"]))


if __name__ == "__main__":
    unittest.main()
