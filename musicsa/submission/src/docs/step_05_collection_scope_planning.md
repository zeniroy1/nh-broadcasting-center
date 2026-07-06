# 5단계 구현 기록: 상품 목록 수집 범위 설계

## 목표

4단계에서 만든 검색어 후보를 바탕으로 상품 목록 수집 작업 계획을 만든다.

이번 단계는 실제 무신사 요청을 수행하지 않는다. 대신 다음 단계에서 수집기를 구현할 수 있도록 다음 내용을 구조화한다.

```text
어떤 검색어를 사용할지
어떤 공개 데이터 소스를 볼지
각 소스에서 몇 개까지 수집할지
어떤 필터를 반드시 적용할지
중복 상품을 어떻게 제거할지
광고/품절 상품을 어떻게 처리할지
```

## 구현 파일

```text
src/scripts/musinsa_collection_planner.py
src/tests/test_musinsa_collection_planner.py
```

## 수집 대상 소스

```text
search_results_page
ranking_page
category_page
```

`product_detail_page`와 `review_area`는 상품 목록을 만든 뒤 다음 단계에서 상세/리뷰 수집에 사용한다.

## 수집 정책

기본값은 다음 JSON 설정 파일에서 관리한다.

```text
src/config/collection_scope.json
```

따라서 수집 범위가 너무 넓거나 좁으면 코드 수정 없이 설정값을 먼저 조정한다.

```text
검색 결과: 후보 검색어별 최대 30개, 최대 2페이지
랭킹 페이지: 후보 검색어별 최대 50개, 최대 2페이지
카테고리 페이지: 후보 검색어별 최대 40개, 최대 2페이지
```

후보 목적에 따라 수집량을 조정한다.

```text
exact_match: 100%
core_search: 85%
ranking_probe: 100%
review_probe: 50%
broad_discovery: 60%
fallback: 40%
```

## 중복 제거 정책

```text
1차 키: product_id
보조 키: product_url
보조 키: normalized_brand_name + normalized_product_name
```

동일 상품은 더 높은 priority의 수집 작업 결과를 우선 유지한다.

## 광고/품절 처리

```text
광고/스폰서 상품은 제외하지 않고 is_ad로 표시한다.
품절 상품은 기본 비교 후보에서 제외하되, 원본 표시는 유지할 수 있다.
```

## 자체 검수 항목

```text
정적 검사
단위 테스트
수집 계획 검증
구현 스킬 실현 시뮬레이션
불필요한 주석 삭제
코드 충돌 여부 확인
전체 코드 라인 정리
HTML/SVG 확인 리포트 생성
```

## 오픈형 설정 항목

```text
source_limits: 소스별 max_items, max_pages
purpose_multiplier: 검색 목적별 수집량 배율
source_priority: 소스별 수집 우선순위
excluded_first_pass_sources: 1차 후보 수집 제외 소스
minimum_items_for_list_source: 목록형 소스 최소 수집량
policy: 광고/품절/중복 제거 정책
```
