import unittest

from scripts.musinsa_intent_parser import parse_to_dict


class MusinsaIntentParserTest(unittest.TestCase):
    def test_black_plain_tshirt_for_male_40s(self):
        result = parse_to_dict("검은색 반팔 무지티를 2~3만원대에서 40대 남성이 입기 좋은 제품으로 찾아줘")

        self.assertEqual(result["product_group"], "short_sleeve_tshirt")
        self.assertEqual(result["category_label"], "반소매 티셔츠")
        self.assertIn("black", result["colors"])
        self.assertIn("plain", result["styles"])
        self.assertEqual(result["price_min"], 20000)
        self.assertEqual(result["price_max"], 39999)
        self.assertEqual(result["gender"], "M")
        self.assertEqual(result["age_band"], "40s")
        self.assertGreaterEqual(result["confidence"], 0.9)

    def test_logo_exclusion(self):
        result = parse_to_dict("로고 없는 블랙 반팔티 3만원 이하")

        self.assertIn("visible_logo", result["excluded_conditions"])
        self.assertEqual(result["price_max"], 30000)
        self.assertIn("블랙 무지 반소매 티셔츠", result["generated_keywords"])

    def test_price_band_natural_language(self):
        exact_range = parse_to_dict("검은색 반팔티 2~3만원")
        manwon_band = parse_to_dict("검은색 반팔티 3만원대")
        won_band = parse_to_dict("검은색 반팔티 30000원대")

        self.assertEqual(exact_range["price_min"], 20000)
        self.assertEqual(exact_range["price_max"], 30000)
        self.assertEqual(manwon_band["price_min"], 30000)
        self.assertEqual(manwon_band["price_max"], 39999)
        self.assertEqual(won_band["price_min"], 30000)
        self.assertEqual(won_band["price_max"], 39999)

    def test_price_amount_variants_are_normalized(self):
        under_queries = [
            "반팔티 70,000원 이하",
            "반팔티 70000원 이하",
            "반팔티 7만 이하",
            "반팔티 7만원 이하",
            "반팔티 칠만원 이하",
            "반팔티 70,000",
            "반팔티 70000",
            "반팔티 7만",
            "반팔티 7만원",
            "반팔티 칠만원",
        ]
        for query in under_queries:
            with self.subTest(query=query):
                result = parse_to_dict(query)
                self.assertIsNone(result["price_min"])
                self.assertEqual(result["price_max"], 70000)

        band_queries = [
            "반팔티 70,000원대",
            "반팔티 70000원대",
            "반팔티 7만원대",
            "반팔티 칠만원대",
        ]
        for query in band_queries:
            with self.subTest(query=query):
                result = parse_to_dict(query)
                self.assertEqual(result["price_min"], 70000)
                self.assertEqual(result["price_max"], 79999)

    def test_unknown_category_keeps_note(self):
        result = parse_to_dict("무난한 검정 제품")

        self.assertIsNone(result["product_group"])
        self.assertTrue(any("상품군" in note for note in result["notes"]))

    def test_free_terms_preserve_unknown_product_words(self):
        result = parse_to_dict("검정 가죽 벨트 3만원대 남성")

        self.assertEqual(result["product_group"], "belt")
        self.assertEqual(result["category_label"], "벨트")
        self.assertEqual(result["free_terms"], ["가죽"])
        self.assertIn("keyword:가죽", result["required_conditions"])
        self.assertIn("category:벨트", result["required_conditions"])
        self.assertTrue(any("가죽 벨트" in keyword for keyword in result["generated_keywords"]))

    def test_free_terms_strip_korean_particles(self):
        result = parse_to_dict("검정 벨트를 3만원대에서 찾아줘")

        self.assertEqual(result["product_group"], "belt")
        self.assertEqual(result["free_terms"], [])
        self.assertNotIn("벨트를", result["free_terms"])

    def test_musinsa_category_words_are_used_for_bag_and_sweatshirt(self):
        bag = parse_to_dict("검정 메신저백 5만원대 남성")
        sweatshirt = parse_to_dict("검정 맨투맨 3만원대 남성")

        self.assertEqual(bag["product_group"], "messenger_cross_bag")
        self.assertEqual(bag["category_label"], "메신저/크로스 백")
        self.assertEqual(sweatshirt["product_group"], "sweatshirt")
        self.assertEqual(sweatshirt["category_label"], "맨투맨/스웨트셔츠")

    def test_attribute_words_do_not_become_free_terms(self):
        result = parse_to_dict("40대 남성의 무지반팔티 색깔은검정색으로 가격대는 만원대")

        self.assertEqual(result["product_group"], "short_sleeve_tshirt")
        self.assertIn("black", result["colors"])
        self.assertIn("plain", result["styles"])
        self.assertEqual(result["price_min"], 10000)
        self.assertEqual(result["price_max"], 19999)
        self.assertEqual(result["gender"], "M")
        self.assertEqual(result["age_band"], "40s")
        self.assertEqual(result["free_terms"], [])

    def test_exact_age_value_becomes_age_band_not_keyword(self):
        result = parse_to_dict("검은색, 무지, 49세 남자, 반팔티, 만원대")

        self.assertEqual(result["age_band"], "40s")
        self.assertEqual(result["gender"], "M")
        self.assertEqual(result["price_min"], 10000)
        self.assertEqual(result["price_max"], 19999)
        self.assertEqual(result["free_terms"], [])
        self.assertTrue(all("49세" not in keyword for keyword in result["generated_keywords"]))

    def test_seasonal_short_pants_charcoal_sentence_is_normalized(self):
        result = parse_to_dict("나는 20대 남자이고 지금 여름용 반바지를 찾고있어, 색깔은 챠콜이고 가격은 1만원대의 제품을 찾아줘")

        self.assertEqual(result["product_group"], "short_pants")
        self.assertEqual(result["category_label"], "숏 팬츠")
        self.assertIn("charcoal", result["colors"])
        self.assertEqual(result["age_band"], "20s")
        self.assertEqual(result["gender"], "M")
        self.assertEqual(result["price_min"], 10000)
        self.assertEqual(result["price_max"], 19999)
        self.assertEqual(result["free_terms"], [])
        self.assertTrue(any("숏 팬츠" in keyword or "반바지" in keyword for keyword in result["generated_keywords"]))

    def test_swimwear_sentence_with_sal_age_is_normalized(self):
        result = parse_to_dict("23살 여자이고 수영복을 찾고있어, 가격은 10만원이하의 제품을 찾아줘")

        self.assertEqual(result["product_group"], "swimwear")
        self.assertEqual(result["category_label"], "수영복/비치웨어")
        self.assertEqual(result["age_band"], "20s")
        self.assertEqual(result["gender"], "F")
        self.assertEqual(result["price_max"], 100000)
        self.assertEqual(result["free_terms"], [])
        self.assertTrue(all("23살" not in keyword for keyword in result["generated_keywords"]))
        self.assertTrue(any("여성" in keyword for keyword in result["generated_keywords"]))
        self.assertTrue(all("남성" not in keyword for keyword in result["generated_keywords"]))

    def test_exact_age_values_are_broadened_to_decade_bands(self):
        cases = [
            ("23살 여자 수영복", "20s", "23살"),
            ("33살 남자 반팔티", "30s", "33살"),
            ("49세 남자 반팔티", "40s", "49세"),
            ("57세 남자 반팔티", "50s", "57세"),
            ("67세 남자 운동화", "60s", "67세"),
        ]

        for query, expected_age_band, age_token in cases:
            with self.subTest(query=query):
                result = parse_to_dict(query)

                self.assertEqual(result["age_band"], expected_age_band)
                self.assertIn(f"age_proxy:{expected_age_band}", result["preferred_conditions"])
                self.assertNotIn(age_token, result["free_terms"])
                self.assertTrue(all(age_token not in keyword for keyword in result["generated_keywords"]))

    def test_teen_context_is_not_active_age_proxy(self):
        for query, age_token in [("13살 여자 수영복", "13살"), ("10대 여자 백팩", "10대"), ("청소년 남자 후드티", "청소년")]:
            with self.subTest(query=query):
                result = parse_to_dict(query)

                self.assertIsNone(result["age_band"])
                self.assertTrue(result["teen_context"])
                self.assertNotIn("age_proxy:10s", result["preferred_conditions"])
                self.assertNotIn(age_token, result["free_terms"])
                self.assertTrue(all(age_token not in keyword for keyword in result["generated_keywords"]))

    def test_natural_color_words_map_to_standard_color_families(self):
        cases = [
            ("소라색 셔츠", "skyblue"),
            ("아이보리 원피스", "beige"),
            ("올리브 바람막이", "khaki"),
            ("와인색 스커트", "burgundy"),
            ("민트 운동화", "green"),
        ]

        for query, expected_color in cases:
            with self.subTest(query=query):
                result = parse_to_dict(query)

                self.assertIn(expected_color, result["colors"])
                self.assertEqual(result["free_terms"], [])

    def test_natural_product_type_words_map_to_musinsa_categories(self):
        cases = [
            ("아이보리 드레스", "one_piece_dress", "원피스"),
            ("와인색 치마", "skirt", "스커트"),
            ("민트 러닝화", "sneakers", "스니커즈"),
            ("블랙 요가팬츠", "leggings", "레깅스"),
            ("올리브 바람막이", "outer", "아우터"),
        ]

        for query, product_group, category_label in cases:
            with self.subTest(query=query):
                result = parse_to_dict(query)

                self.assertEqual(result["product_group"], product_group)
                self.assertEqual(result["category_label"], category_label)
                self.assertEqual(result["free_terms"], [])


if __name__ == "__main__":
    unittest.main()
