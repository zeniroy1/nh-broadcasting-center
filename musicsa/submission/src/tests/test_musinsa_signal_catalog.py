import unittest

from scripts.musinsa_signal_catalog import (
    build_collection_plan,
    get_signals,
    summarize_catalog,
    validate_catalog,
)


class MusinsaSignalCatalogTest(unittest.TestCase):
    def test_catalog_is_valid(self):
        self.assertEqual(validate_catalog(), [])

    def test_has_three_signal_tiers(self):
        summary = summarize_catalog()

        self.assertGreater(summary["signals_by_tier"]["direct"], 0)
        self.assertGreater(summary["signals_by_tier"]["refined"], 0)
        self.assertGreater(summary["signals_by_tier"]["inferred"], 0)
        self.assertTrue(summary["confidence_required_for_inferred"])

    def test_inferred_signals_require_confidence_percent(self):
        inferred = get_signals("inferred")

        self.assertTrue(inferred)
        for signal in inferred:
            self.assertIn("required_confidence_percent", signal["confidence_policy"])

    def test_collection_plan_for_male_40s_query(self):
        plan = build_collection_plan("검은색 반팔 무지티를 2~3만원대에서 40대 남성이 입기 좋은 제품으로 찾아줘")

        self.assertIn("ranking_page", plan["target_sources"])
        self.assertIn("product_detail_page", plan["target_sources"])
        self.assertIn("review_area", plan["target_sources"])
        self.assertIn("age_male_40s_fit_score", plan["target_signals"])
        self.assertEqual(plan["parsed_intent"]["age_band"], "40s")
        self.assertEqual(plan["parsed_intent"]["gender"], "M")


if __name__ == "__main__":
    unittest.main()
