import unittest
from unittest.mock import patch

from scripts.musinsa_live_buyer_app import (
    build_buyer_app_model,
    discover_public_ranking_api_urls,
    parse_musinsa_public_json,
    parse_musinsa_public_products,
    validate_buyer_app_model,
    _live_search_api_urls,
    _matches_free_terms,
)
from scripts.musinsa_query_generator import generate_query_candidates


FIXTURE_HTML = """
<html><body><script id="__NEXT_DATA__" type="application/json">
{"props":{"pageProps":{"products":[
  {"goodsNo":"1001","goodsName":"베이직 무지 반팔 티셔츠 블랙","brandName":"테스트브랜드","salePrice":"29,900","reviewCount":"1200","reviewScore":4.8,"rank":1},
  {"goodsNo":"1002","goodsName":"[크롭] 그래픽 로고 반팔 티셔츠 블랙","brandName":"테스트그래픽","salePrice":"32,900","reviewCount":"300","reviewScore":4.1,"rank":2,"url":"https://www.musinsa.com/products/1002","image":"https://image.msscdn.net/images/goods_img/1002.jpg"},
  {"goodsNo":"1003","goodsName":"원턱 트랙 팬츠 블랙","brandName":"테스트팬츠","salePrice":"35,900","reviewCount":"400","reviewScore":4.4,"rank":3}
]}}}
</script></body></html>
"""


class MusinsaLiveBuyerAppTest(unittest.TestCase):
    def test_public_html_products_are_parsed(self):
        products = parse_musinsa_public_products(FIXTURE_HTML)

        self.assertEqual(len(products), 3)
        self.assertEqual(products[0]["product_id"], "1001")
        self.assertEqual(products[0]["price"], 29900)
        self.assertEqual(products[0]["review_count"], 1200)

    def test_buyer_app_model_builds_five_candidate_flow(self):
        model = build_buyer_app_model(raw_html=FIXTURE_HTML)
        report = model["recommendation_report"]

        self.assertEqual(model["collection_mode"], "html_input")
        self.assertEqual(model["collected_public_product_count"], 3)
        self.assertEqual(model["filtered_public_product_count"], 1)
        self.assertEqual(report["recommendation_count"], 5)
        self.assertEqual(report["shortlist_detail"]["selected_count"], 3)
        self.assertIn("product_url", report["comparison_table"]["rows"][0])
        self.assertNotIn("그래픽", {row["product"] for row in report["comparison_table"]["rows"]})

    def test_excluded_products_are_removed_before_scoring(self):
        model = build_buyer_app_model(raw_html=FIXTURE_HTML, exclude_product_ids=["1001"])
        product_ids = [row["product_id"] for row in model["recommendation_report"]["comparison_table"]["rows"]]

        self.assertNotIn("1001", product_ids)
        self.assertEqual(model["excluded_product_ids"], ["1001"])

    def test_excluded_name_keys_remove_duplicate_fragments(self):
        duplicate_fixture = """
        <html><body><script type="application/json">
        {"props":{"pageProps":{"products":[
          {"goodsNo":"1001","goodsName":"베이직 무지 반팔 티셔츠 블랙","brandName":"테스트브랜드","salePrice":"29,900","reviewCount":"1200","reviewScore":4.8,"rank":1},
          {"goodsName":"베이직 무지 반팔 티셔츠 블랙","brandName":"테스트브랜드","salePrice":"29,900","rank":7}
        ]}}}
        </script></body></html>
        """

        model = build_buyer_app_model(
            raw_html=duplicate_fixture,
            exclude_product_ids=["1001", "name:테스트브랜드:베이직 무지 반팔 티셔츠 블랙"],
        )
        rows = model["recommendation_report"]["comparison_table"]["rows"]

        self.assertTrue(all(row["brand"] != "테스트브랜드" for row in rows))

    def test_public_api_json_products_are_parsed(self):
        raw_json = """
        {"data":{"goods":[
          {"product_id":"2001","product_name":"API 무지 반팔 티셔츠 블랙","brand_name":"API브랜드","price":"25000","reviewCount":"77","reviewScore":"4.6","index":"3","goodsLinkUrl":"https://www.musinsa.com/products/2001","thumbnail":"https://image.msscdn.net/images/goods_img/2001.jpg"}
        ]}}
        """
        products = parse_musinsa_public_json(raw_json)

        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]["product_id"], "2001")
        self.assertEqual(products[0]["brand_name"], "API브랜드")
        self.assertEqual(products[0]["ranking_position"], 3)
        self.assertEqual(products[0]["product_url"], "https://www.musinsa.com/products/2001")
        self.assertEqual(products[0]["image_url"], "https://image.msscdn.net/images/goods_img/2001.jpg")

    def test_public_api_nested_review_and_rank_signals_are_parsed(self):
        raw_json = """
        {"data":{"list":[
          {
            "goodsNo":"3001",
            "goodsName":"중첩 리뷰 신호 반팔 티셔츠",
            "brandName":"중첩브랜드",
            "salePrice":"31000",
            "reviewStats":{"totalReviewCount":"1,234","averageRating":"96"},
            "rankInfo":{"rankNo":"7"},
            "salesInfo":{"orderCnt":"8,765"}
          }
        ]}}
        """
        products = parse_musinsa_public_json(raw_json)

        self.assertEqual(products[0]["review_count"], 1234)
        self.assertEqual(products[0]["review_score"], 4.8)
        self.assertEqual(products[0]["ranking_position"], 7)
        self.assertEqual(products[0]["sales_label_count"], 8765)

    def test_nested_generic_score_and_index_are_not_used_as_review_or_rank(self):
        raw_json = """
        {"data":{"list":[
          {
            "goodsNo":"3002",
            "goodsName":"광고 점수 포함 상품",
            "brandName":"안전브랜드",
            "salePrice":"31000",
            "adInfo":{"score":98.7},
            "trackingItems":[{"index":"1"}]
          }
        ]}}
        """
        products = parse_musinsa_public_json(raw_json)

        self.assertEqual(products[0]["review_score"], None)
        self.assertEqual(products[0]["ranking_position"], None)

    def test_public_api_urls_are_discovered_from_html(self):
        raw_html = """
        <script>{"apiUrl":"https://api.musinsa.com/api2/hm/web/v5/pans/ranking?storeCode=musinsa"}</script>
        """
        urls = discover_public_ranking_api_urls(raw_html)

        self.assertTrue(urls)
        self.assertIn("subPan=product", urls[0])

    def test_buyer_app_keeps_public_data_boundaries(self):
        model = build_buyer_app_model(raw_html=FIXTURE_HTML)

        self.assertTrue(any("실제 구매자 수" in item for item in model["collection_boundaries"]))
        self.assertTrue(any("공개 HTML/JSON" in item for item in model["collection_boundaries"]))

    def test_free_keyword_gate_filters_public_products(self):
        raw_html = """
        <html><body><script type="application/json">
        {"props":{"pageProps":{"products":[
          {"goodsNo":"belt1","goodsName":"블랙 소가죽 벨트","brandName":"벨트브랜드","salePrice":"34,000","reviewCount":"500","reviewScore":4.7,"rank":1},
          {"goodsNo":"tee1","goodsName":"블랙 무지 반팔 티셔츠","brandName":"티브랜드","salePrice":"29,000","reviewCount":"1000","reviewScore":4.8,"rank":2}
        ]}}}
        </script></body></html>
        """
        model = build_buyer_app_model(query="검정 가죽 벨트 3만원대 남성", raw_html=raw_html)
        rows = model["recommendation_report"]["comparison_table"]["rows"]

        self.assertEqual(model["filtered_public_product_count"], 1)
        self.assertIn("벨트", rows[0]["product"])
        self.assertNotIn("티브랜드", {row["brand"] for row in rows})

    def test_free_keyword_query_does_not_fallback_to_unrelated_tshirts(self):
        raw_html = """
        <html><body><script type="application/json">
        {"props":{"pageProps":{"products":[
          {"goodsNo":"tee1","goodsName":"블랙 무지 반팔 티셔츠","brandName":"티브랜드","salePrice":"29,000","reviewCount":"1000","reviewScore":4.8,"rank":2}
        ]}}}
        </script></body></html>
        """
        model = build_buyer_app_model(query="검정 가죽 벨트 3만원대 남성", raw_html=raw_html)
        rows = model["recommendation_report"]["comparison_table"]["rows"]

        self.assertEqual(model["filtered_public_product_count"], 0)
        self.assertEqual(rows, [])
        self.assertEqual(model["recommendation_report"]["recommendation_count"], 0)
        self.assertEqual(model["search_diagnostics"]["status"], "needs_attention")
        self.assertTrue(any(issue["type"] == "keyword_not_found" for issue in model["search_diagnostics"]["issues"]))

    def test_price_band_is_strict_for_manwon_band(self):
        raw_html = """
        <html><body><script type="application/json">
        {"props":{"pageProps":{"products":[
          {"goodsNo":"in1","goodsName":"블랙 무지 반팔 티셔츠","brandName":"만원대브랜드","salePrice":"18,900","reviewCount":"500","reviewScore":4.7,"rank":1},
          {"goodsNo":"out1","goodsName":"블랙 무지 반팔 티셔츠","brandName":"이만원대브랜드","salePrice":"20,900","reviewCount":"900","reviewScore":4.8,"rank":2}
        ]}}}
        </script></body></html>
        """
        model = build_buyer_app_model(query="남성 무지반팔티 검정색 만원대", raw_html=raw_html)
        rows = model["recommendation_report"]["comparison_table"]["rows"]

        self.assertEqual(model["filtered_public_product_count"], 1)
        self.assertEqual(rows[0]["brand"], "만원대브랜드")

    def test_plain_intent_excludes_printed_products(self):
        raw_html = """
        <html><body><script type="application/json">
        {"props":{"pageProps":{"products":[
          {"goodsNo":"plain1","goodsName":"블랙 무지 반팔 티셔츠","brandName":"무지브랜드","salePrice":"18,900","reviewCount":"500","reviewScore":4.7,"rank":1},
          {"goodsNo":"print1","goodsName":"블랙 프린트 반팔 티셔츠","brandName":"프린트브랜드","salePrice":"18,900","reviewCount":"900","reviewScore":4.8,"rank":2}
        ]}}}
        </script></body></html>
        """
        model = build_buyer_app_model(query="남성 무지반팔티 검정색 만원대", raw_html=raw_html)
        rows = model["recommendation_report"]["comparison_table"]["rows"]

        self.assertEqual(model["filtered_public_product_count"], 1)
        self.assertEqual(rows[0]["brand"], "무지브랜드")

    def test_charcoal_short_pants_sentence_filters_live_products(self):
        raw_html = """
        <html><body><script type="application/json">
        {"props":{"pageProps":{"products":[
          {"goodsNo":"short1","goodsName":"챠콜 밴딩 반바지","brandName":"반바지브랜드","salePrice":"18,900","reviewCount":"500","reviewScore":4.7,"rank":1},
          {"goodsNo":"pants1","goodsName":"챠콜 와이드 팬츠","brandName":"긴바지브랜드","salePrice":"18,900","reviewCount":"600","reviewScore":4.8,"rank":2},
          {"goodsNo":"black1","goodsName":"블랙 밴딩 반바지","brandName":"블랙브랜드","salePrice":"18,900","reviewCount":"700","reviewScore":4.9,"rank":3}
        ]}}}
        </script></body></html>
        """
        query = "나는 20대 남자이고 지금 여름용 반바지를 찾고있어, 색깔은 챠콜이고 가격은 1만원대의 제품을 찾아줘"
        model = build_buyer_app_model(query=query, raw_html=raw_html)
        rows = model["recommendation_report"]["comparison_table"]["rows"]

        self.assertEqual(model["parsed_intent"]["product_group"], "short_pants")
        self.assertIn("charcoal", model["parsed_intent"]["colors"])
        self.assertEqual(model["filtered_public_product_count"], 1)
        self.assertEqual(rows[0]["brand"], "반바지브랜드")

    def test_swimwear_sentence_filters_live_products(self):
        raw_html = """
        <html><body><script type="application/json">
        {"props":{"pageProps":{"products":[
          {"goodsNo":"swim1","goodsName":"여성 원피스 수영복 블랙","brandName":"수영복브랜드","salePrice":"59,000","reviewCount":"500","reviewScore":4.7,"rank":1},
          {"goodsNo":"rash1","goodsName":"여성 래시가드 세트","brandName":"래시가드브랜드","salePrice":"89,000","reviewCount":"600","reviewScore":4.8,"rank":2},
          {"goodsNo":"tee1","goodsName":"여성 반팔 티셔츠","brandName":"티셔츠브랜드","salePrice":"29,000","reviewCount":"700","reviewScore":4.9,"rank":3}
        ]}}}
        </script></body></html>
        """
        model = build_buyer_app_model(query="23살 여자이고 수영복을 찾고있어, 가격은 10만원이하의 제품을 찾아줘", raw_html=raw_html)
        rows = model["recommendation_report"]["comparison_table"]["rows"]

        self.assertEqual(model["parsed_intent"]["product_group"], "swimwear")
        self.assertEqual(model["filtered_public_product_count"], 2)
        self.assertEqual({row["brand"] for row in rows[:2]}, {"수영복브랜드", "래시가드브랜드"})

    def test_specific_swimwear_term_is_ranked_before_sibling_items(self):
        raw_html = """
        <html><body><script type="application/json">
        {"props":{"pageProps":{"products":[
          {"goodsNo":"bikini1","goodsName":"여성 비키니 세트","brandName":"비키니브랜드","salePrice":"29,000","reviewCount":"9000","reviewScore":4.9,"rank":1},
          {"goodsNo":"rash1","goodsName":"여성 래시가드 긴팔","brandName":"래시가드브랜드A","salePrice":"29,000","reviewCount":"120","reviewScore":4.3,"rank":20},
          {"goodsNo":"rash2","goodsName":"여성 래쉬가드 집업","brandName":"래시가드브랜드B","salePrice":"28,000","reviewCount":"90","reviewScore":4.2,"rank":30}
        ]}}}
        </script></body></html>
        """
        model = build_buyer_app_model(query="20살 여자 래시가드 3만원 이하", raw_html=raw_html)
        rows = model["recommendation_report"]["comparison_table"]["rows"]

        self.assertEqual(model["parsed_intent"]["specific_terms"], ["래시가드"])
        self.assertEqual(model["filtered_public_product_count"], 3)
        self.assertEqual([row["brand"] for row in rows[:2]], ["래시가드브랜드A", "래시가드브랜드B"])
        self.assertIn("비키니브랜드", [row["brand"] for row in rows])
        self.assertGreaterEqual(rows.index(next(row for row in rows if row["brand"] == "비키니브랜드")), 2)

    def test_similar_color_family_and_product_type_filter_live_products(self):
        raw_html = """
        <html><body><script type="application/json">
        {"props":{"pageProps":{"products":[
          {"goodsNo":"dress1","goodsName":"크림 플레어 원피스","brandName":"원피스브랜드","salePrice":"59,000","reviewCount":"500","reviewScore":4.7,"rank":1},
          {"goodsNo":"black1","goodsName":"블랙 플레어 원피스","brandName":"블랙브랜드","salePrice":"59,000","reviewCount":"500","reviewScore":4.7,"rank":2},
          {"goodsNo":"shirt1","goodsName":"크림 오버핏 셔츠","brandName":"셔츠브랜드","salePrice":"49,000","reviewCount":"500","reviewScore":4.7,"rank":3}
        ]}}}
        </script></body></html>
        """
        model = build_buyer_app_model(query="아이보리 드레스 5만원대 여자", raw_html=raw_html)
        rows = model["recommendation_report"]["comparison_table"]["rows"]

        self.assertEqual(model["parsed_intent"]["product_group"], "one_piece_dress")
        self.assertIn("beige", model["parsed_intent"]["colors"])
        self.assertEqual(model["filtered_public_product_count"], 1)
        self.assertEqual(rows[0]["brand"], "원피스브랜드")

    def test_live_fetch_uses_search_urls_for_free_keyword_query(self):
        fetched_urls = []
        fetched_api_urls = []
        search_fixture = """
        {"data":{"list":[
          {"goodsNo":"belt1","goodsName":"블랙 레더 벨트","brandName":"벨트브랜드","salePrice":"34,000","reviewCount":"500","reviewScore":4.7,"rank":1}
        ]}}
        """

        def fake_fetch_html(url):
            fetched_urls.append(url)
            return "<html></html>"

        def fake_fetch_json(url):
            fetched_api_urls.append(url)
            return search_fixture

        with patch("scripts.musinsa_live_buyer_app.fetch_public_html", side_effect=fake_fetch_html), patch(
            "scripts.musinsa_live_buyer_app.fetch_public_json", side_effect=fake_fetch_json
        ):
            model = build_buyer_app_model(query="검정 가죽 벨트 3만원대 남성", fetch_live=True)

        rows = model["recommendation_report"]["comparison_table"]["rows"]
        self.assertTrue(any("search/goods" in url for url in fetched_urls))
        self.assertTrue(any("/plp/goods" in url for url in fetched_api_urls))
        self.assertEqual(model["filtered_public_product_count"], 1)
        self.assertIn("벨트", rows[0]["product"])

    def test_alias_matching_is_not_limited_to_belts(self):
        self.assertTrue(_matches_free_terms("블랙 러닝 스니커즈", ["운동화"]))
        self.assertTrue(_matches_free_terms("방수 데일리 백팩", ["가방"]))
        self.assertTrue(_matches_free_terms("구김방지 와이드 슬랙스", ["링클프리", "슬랙스"]))

    def test_brand_keyword_can_pass_intent_gate(self):
        raw_html = """
        <html><body><script type="application/json">
        {"props":{"pageProps":{"products":[
          {"goodsNo":"tcm1","goodsName":"TCM starfish T (sky blue)","brandName":"더콜디스트모먼트","salePrice":"32,400","reviewCount":"453","reviewScore":4.9,"rank":1},
          {"goodsNo":"other1","goodsName":"베이직 반팔 티셔츠","brandName":"다른브랜드","salePrice":"19,900","reviewCount":"1000","reviewScore":4.8,"rank":2}
        ]}}}
        </script></body></html>
        """
        model = build_buyer_app_model(query="더콜디스트모먼트", raw_html=raw_html)
        rows = model["recommendation_report"]["comparison_table"]["rows"]

        self.assertEqual(model["filtered_public_product_count"], 1)
        self.assertEqual(rows[0]["brand"], "더콜디스트모먼트")
        self.assertEqual(model["search_diagnostics"]["counts"]["brand_only_matches"], 1)
        self.assertTrue(any(issue["type"] == "brand_name_match" for issue in model["search_diagnostics"]["issues"]))

    def test_free_keyword_matching_ignores_spacing(self):
        self.assertTrue(_matches_free_terms("더 콜디스트 모먼트 TCM starfish T", ["더콜디스트모먼트"]))

    def test_search_diagnostics_detect_spacing_difference(self):
        raw_html = """
        <html><body><script type="application/json">
        {"props":{"pageProps":{"products":[
          {"goodsNo":"tcm1","goodsName":"TCM starfish T","brandName":"더 콜디스트 모먼트","salePrice":"32,400","reviewCount":"453","reviewScore":4.9,"rank":1}
        ]}}}
        </script></body></html>
        """
        model = build_buyer_app_model(query="더콜디스트모먼트", raw_html=raw_html)

        self.assertEqual(model["filtered_public_product_count"], 1)
        self.assertEqual(model["search_diagnostics"]["counts"]["spacing_adjusted_matches"], 1)

    def test_similar_keyword_search_uses_musinsa_search_results_when_exact_match_is_empty(self):
        search_fixture = """
        {"data":{"list":[
          {"goodsNo":"similar1","goodsName":"유트 블랙","brandName":"이소","salePrice":"69,600","reviewCount":"300","reviewScore":4.7,"rank":1},
          {"goodsNo":"similar2","goodsName":"하이브 폴딩 뮬 클로그 베이지","brandName":"위더로드","salePrice":"75,600","reviewCount":"220","reviewScore":4.6,"rank":2}
        ]}}
        """

        def fake_fetch_json(url):
            if "/plp/goods" in url:
                return search_fixture
            return '{"data":{"list":[]}}'

        with patch("scripts.musinsa_live_buyer_app.fetch_public_json", side_effect=fake_fetch_json):
            model = build_buyer_app_model(query="버켄스탁", fetch_live=True)

        rows = model["recommendation_report"]["comparison_table"]["rows"]
        issue_types = {issue["type"] for issue in model["search_diagnostics"]["issues"]}

        self.assertEqual(model["filtered_public_product_count"], 0)
        self.assertEqual(model["search_diagnostics"]["counts"]["similar_candidates"], 2)
        self.assertIn("similar_keyword_fallback", issue_types)
        self.assertEqual({row["brand"] for row in rows[:2]}, {"이소", "위더로드"})
        self.assertTrue(all(row["final_score"] <= 74 for row in rows))

    def test_similar_keyword_search_keeps_explicit_product_group_filter(self):
        search_fixture = """
        {"data":{"list":[
          {"goodsNo":"clog1","goodsName":"하이브 폴딩 뮬 클로그 베이지","brandName":"위더로드","salePrice":"75,600","reviewCount":"220","reviewScore":4.6,"rank":1},
          {"goodsNo":"tee1","goodsName":"베이직 반팔 티셔츠","brandName":"티브랜드","salePrice":"29,000","reviewCount":"500","reviewScore":4.8,"rank":2}
        ]}}
        """

        def fake_fetch_json(url):
            if "/plp/goods" in url:
                return search_fixture
            return '{"data":{"list":[]}}'

        with patch("scripts.musinsa_live_buyer_app.fetch_public_json", side_effect=fake_fetch_json):
            model = build_buyer_app_model(query="버켄스탁 샌들", fetch_live=True)

        rows = model["recommendation_report"]["comparison_table"]["rows"]

        self.assertEqual(model["filtered_public_product_count"], 0)
        self.assertEqual(model["search_diagnostics"]["counts"]["similar_candidates"], 1)
        self.assertEqual(rows[0]["brand"], "위더로드")

    def test_search_api_urls_include_alias_expansions_for_any_product(self):
        query_plan = generate_query_candidates("검정 운동화 5만원대 남성")
        urls = _live_search_api_urls(query_plan)

        self.assertTrue(any("keyword=" in url for url in urls))
        self.assertTrue(all("gf=M" in url for url in urls))
        self.assertTrue(any("%EC%8A%A4%EB%8B%88%EC%BB%A4%EC%A6%88" in url for url in urls))

    def test_live_detail_risk_varies_by_public_review_signal(self):
        raw_html = """
        <html><body><script type="application/json">
        {"props":{"pageProps":{"products":[
          {"goodsNo":"stable1","goodsName":"베이직 무지 반팔 티셔츠 블랙","brandName":"안정브랜드","salePrice":"29,000","reviewCount":"5200","reviewScore":4.9,"rank":3},
          {"goodsNo":"risk1","goodsName":"그래픽 반팔 티셔츠 블랙","brandName":"확인필요","salePrice":"29,000","reviewCount":"12","reviewScore":3.7,"rank":140}
        ]}}}
        </script></body></html>
        """
        model = build_buyer_app_model(query="검정 반팔티 3만원대 남성", raw_html=raw_html)
        panels = model["recommendation_report"]["shortlist_detail"]["detail_panels"]
        risk_scores = [
            next(
                segment["score"] for segment in panel["component_segments"] if segment["key"] == "review_risk_score"
            )
            for panel in panels
        ]

        self.assertGreaterEqual(len(risk_scores), 2)
        self.assertGreater(max(risk_scores), min(risk_scores))

    def test_validation_passes(self):
        self.assertEqual(validate_buyer_app_model(), [])


if __name__ == "__main__":
    unittest.main()
