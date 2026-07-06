# 6단계 구현 기록: 상품 상세 데이터 수집 설계

## 목표

5단계에서 만들어진 후보 상품 목록을 기준으로, 상품 상세 페이지에서 어떤 공개 정보를 수집하고 어떤 값은 정제/추정으로 표기할지 정의한다.

이번 단계도 실제 무신사 네트워크 요청은 수행하지 않는다. 상품 목록 후보에 `product_id`와 `product_url`이 붙었다고 가정하고, 상세 페이지 접근 시 필요한 필드 구조와 파싱 규칙을 먼저 고정한다.

## 구현 파일

```text
src/scripts/musinsa_detail_schema.py
src/tests/test_musinsa_detail_schema.py
```

## 상세 수집 입력 조건

상세 수집 작업은 목록 후보에서 다음 키를 받아야 한다.

```text
product_id
product_url
```

둘 중 하나만 있어도 보조 접근은 가능하지만, 중복 제거와 원본 추적을 위해 둘 다 요구하는 구조로 설계했다.

## 상세 필드 구분

상세 데이터 필드는 세 단계로 나눈다.

```text
direct: 페이지에 공개 노출된 값을 그대로 정규화
refined: 공개 문구를 표준 값으로 정제
inferred: 공개 단서를 조합한 추정값
```

`inferred` 필드는 반드시 `confidence_percent`와 `limitation`을 포함한다.

## 주요 direct 필드

```text
product_id
product_url
product_name
brand_name
normal_price
sale_price
discount_rate
image_urls
category_path
delivery_type
estimated_delivery_date
review_count
review_score
description_text
size_options
is_sold_out
ranking_badges
```

## 주요 refined 필드

```text
gender_target
season
material_keywords
fit_keywords
```

## 주요 inferred 필드

```text
plain_style_fit
age_40s_context_fit
```

`age_40s_context_fit`은 실제 40대 구매자 수가 아니다. 베이직함, 과하지 않음, 출근/남편 등 공개 문구와 후속 리뷰 단서를 조합해 계산할 추정 지표다.

## 내부 데이터 경계

다음 값은 상세 페이지 설계에서도 직접 수집한다고 표현하지 않는다.

```text
실제 구매자 수
연령대별 구매 비율
무신사 내부 랭킹 알고리즘
상품별 장바구니 전환율
반품률
재구매율
```

## 5단계 설정 오픈화 반영

5단계 수집 범위 설정은 다음 파일로 분리했다.

```text
src/config/collection_scope.json
```

조정 가능한 값:

```text
소스별 max_items
소스별 max_pages
검색 목적별 multiplier
소스별 priority
1차 수집 제외 소스
목록 소스 최소 수집량
광고/품절/중복 제거 정책 문구
```

즉, 수집 범위가 너무 넓거나 좁으면 코드를 수정하지 않고 JSON 설정부터 조정할 수 있다.

## 자체 검수 항목

```text
정적 검사
단위 테스트
상세 스키마 검증
구현 스킬 실현 시뮬레이션
불필요한 주석 삭제
코드 충돌 여부 확인
전체 코드 라인 정리
HTML/SVG 확인 리포트 생성
```
