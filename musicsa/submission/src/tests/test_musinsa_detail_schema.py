import unittest

from scripts.musinsa_detail_schema import (
    build_detail_collection_blueprint,
    build_detail_schema,
    validate_detail_blueprint,
)


QUERY = "검은색 반팔 무지티를 2~3만원대에서 40대 남성이 입기 좋은 제품으로 찾아줘"


class MusinsaDetailSchemaTest(unittest.TestCase):
    def test_detail_blueprint_is_valid(self):
        self.assertEqual(validate_detail_blueprint(QUERY), [])

    def test_schema_has_required_public_fields(self):
        schema = build_detail_schema()
        field_names = {field["field_name"] for field in schema["fields"]}

        self.assertIn("product_id", field_names)
        self.assertIn("product_url", field_names)
        self.assertIn("product_name", field_names)
        self.assertIn("brand_name", field_names)
        self.assertIn("sale_price", field_names)

    def test_inferred_fields_have_capped_confidence(self):
        schema = build_detail_schema()
        inferred_fields = [field for field in schema["fields"] if field["metric_tier"] == "inferred"]

        self.assertGreater(len(inferred_fields), 0)
        for field in inferred_fields:
            self.assertLessEqual(field["confidence_percent"], 85)
            self.assertTrue(field["limitation"])

    def test_blueprint_creates_detail_tasks_from_collection_jobs(self):
        blueprint = build_detail_collection_blueprint(QUERY, max_tasks=3)

        self.assertEqual(blueprint["detail_task_count"], 3)
        for task in blueprint["tasks"]:
            self.assertEqual(task["detail_source"], "product_detail_page")
            self.assertIn("product_id", task["required_input_keys"])
            self.assertIn("product_url", task["required_input_keys"])

    def test_internal_data_boundary_is_explicit(self):
        schema = build_detail_schema()
        boundary_text = " ".join(schema["internal_data_boundary"])

        self.assertIn("실제 구매자 수", boundary_text)
        self.assertIn("연령대별 구매 비율", boundary_text)


if __name__ == "__main__":
    unittest.main()
