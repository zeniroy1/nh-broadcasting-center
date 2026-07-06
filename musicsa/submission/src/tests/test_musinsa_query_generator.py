import unittest

from scripts.musinsa_query_generator import generate_query_candidates, validate_query_candidates


QUERY = "검은색 반팔 무지티를 2~3만원대에서 40대 남성이 입기 좋은 제품으로 찾아줘"


class MusinsaQueryGeneratorTest(unittest.TestCase):
    def test_query_candidates_are_valid(self):
        self.assertEqual(validate_query_candidates(QUERY), [])

    def test_exact_match_candidate_is_first(self):
        result = generate_query_candidates(QUERY)
        first = result["candidates"][0]

        self.assertEqual(first["purpose"], "exact_match")
        self.assertIn("남성", first["query"])
        self.assertIn("블랙", first["query"])
        self.assertIn("무지", first["query"])
        self.assertIn("반소매", first["query"])

    def test_candidates_include_expected_purposes(self):
        result = generate_query_candidates(QUERY)
        purposes = {candidate["purpose"] for candidate in result["candidates"]}

        self.assertIn("exact_match", purposes)
        self.assertIn("core_search", purposes)
        self.assertIn("ranking_probe", purposes)
        self.assertIn("review_probe", purposes)
        self.assertIn("broad_discovery", purposes)

    def test_filters_are_attached(self):
        result = generate_query_candidates(QUERY)

        for candidate in result["candidates"]:
            self.assertIn("price:20000-39999", candidate["must_apply_filters"])
            self.assertIn("gender:M", candidate["must_apply_filters"])

    def test_logo_exclusion_creates_avoid_terms(self):
        result = generate_query_candidates("로고 없는 블랙 반팔티 3만원 이하")
        avoid_terms = set(result["candidates"][0]["avoid_terms"])

        self.assertIn("로고", avoid_terms)
        self.assertIn("그래픽", avoid_terms)

    def test_musinsa_category_terms_are_kept_in_query_candidates(self):
        result = generate_query_candidates("검정 가죽 벨트 3만원대 남성")
        queries = [candidate["query"] for candidate in result["candidates"]]

        self.assertIn("가죽", result["parsed_intent"]["free_terms"])
        self.assertEqual(result["parsed_intent"]["product_group"], "belt")
        self.assertEqual(result["parsed_intent"]["category_label"], "벨트")
        self.assertTrue(any("가죽 벨트" in query for query in queries))
        self.assertTrue(any(query == "블랙 가죽" for query in queries))
        self.assertIn("price:30000-39999", result["candidates"][0]["must_apply_filters"])

    def test_new_musinsa_category_terms_create_search_candidates(self):
        result = generate_query_candidates("검정 메신저백 5만원대 남성")
        queries = [candidate["query"] for candidate in result["candidates"]]

        self.assertEqual(result["parsed_intent"]["product_group"], "messenger_cross_bag")
        self.assertFalse(any("/" in query for query in queries))
        self.assertTrue(any("메신저백" in query for query in queries))
        self.assertTrue(any("크로스백" in query for query in queries))

    def test_charcoal_short_pants_query_candidates(self):
        result = generate_query_candidates("나는 20대 남자이고 지금 여름용 반바지를 찾고있어, 색깔은 챠콜이고 가격은 1만원대의 제품을 찾아줘")
        queries = [candidate["query"] for candidate in result["candidates"]]

        self.assertEqual(result["parsed_intent"]["product_group"], "short_pants")
        self.assertIn("charcoal", result["parsed_intent"]["colors"])
        self.assertTrue(any("차콜" in query and "숏 팬츠" in query for query in queries))
        self.assertTrue(any("반바지" in query for query in queries))
        self.assertIn("price:10000-19999", result["candidates"][0]["must_apply_filters"])

    def test_swimwear_query_candidates_from_natural_sentence(self):
        result = generate_query_candidates("23살 여자이고 수영복을 찾고있어, 가격은 10만원이하의 제품을 찾아줘")
        queries = [candidate["query"] for candidate in result["candidates"]]

        self.assertEqual(result["parsed_intent"]["product_group"], "swimwear")
        self.assertEqual(result["parsed_intent"]["age_band"], "20s")
        self.assertFalse(any("/" in query for query in queries))
        self.assertTrue(any("수영복" in query for query in queries))
        self.assertTrue(any("비치웨어" in query for query in queries))
        self.assertIn("price:-100000", result["candidates"][0]["must_apply_filters"])
        self.assertIn("gender:F", result["candidates"][0]["must_apply_filters"])

    def test_specific_swimwear_term_is_first_query_without_slash(self):
        result = generate_query_candidates("20살 여자 래시가드 3만원 이하")
        first = result["candidates"][0]
        queries = [candidate["query"] for candidate in result["candidates"]]

        self.assertEqual(result["parsed_intent"]["product_group"], "swimwear")
        self.assertEqual(result["parsed_intent"]["specific_terms"], ["래시가드"])
        self.assertEqual(first["purpose"], "exact_match")
        self.assertIn("여성", first["query"])
        self.assertIn("래시가드", first["query"])
        self.assertNotIn("수영복", first["query"])
        self.assertFalse(any("/" in query for query in queries))

    def test_similar_color_and_product_type_query_candidates(self):
        result = generate_query_candidates("아이보리 드레스 5만원대 여자")
        queries = [candidate["query"] for candidate in result["candidates"]]

        self.assertEqual(result["parsed_intent"]["product_group"], "one_piece_dress")
        self.assertIn("beige", result["parsed_intent"]["colors"])
        self.assertTrue(any("베이지" in query and "원피스" in query for query in queries))
        self.assertTrue(any("아이보리" in query for query in queries))
        self.assertTrue(any("드레스" in query for query in queries))
        self.assertIn("gender:F", result["candidates"][0]["must_apply_filters"])


if __name__ == "__main__":
    unittest.main()
