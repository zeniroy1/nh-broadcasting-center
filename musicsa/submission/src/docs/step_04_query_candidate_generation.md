# 4단계 구현 기록: 검색 후보 생성 로직

## 목표

사용자의 자연어 구매 요청에서 여러 검색어 후보를 생성한다.

핵심은 검색어를 하나만 만드는 것이 아니라, 목적별 검색어를 만들어 이후 수집 단계에서 더 넓고 안정적인 후보군을 확보하는 것이다.

## 구현 파일

```text
src/scripts/musinsa_query_generator.py
src/tests/test_musinsa_query_generator.py
```

## 생성하는 검색어 목적

```text
exact_match: 사용자 조건을 가장 많이 포함한 1차 검색어
core_search: 색상, 스타일, 상품군을 조합한 핵심 검색어
ranking_probe: 랭킹/카테고리 후보 수집용 검색어
review_probe: 리뷰 기반 정제 지표 확인용 검색어
broad_discovery: 너무 좁은 결과를 보완하는 넓은 검색어
fallback: 1단계 Intent Parser가 만든 보조 검색어
```

## 예시 입력

```text
검은색 반팔 무지티를 2~3만원대에서 40대 남성이 입기 좋은 제품으로 찾아줘
```

## 예시 검색어 후보

```text
남성 블랙 무지 반팔 티셔츠
블랙 무지 반팔 티셔츠
남성 블랙 반팔 티셔츠
무지 반팔 티셔츠 리뷰
반팔 티셔츠
```

## 검색어 후보에 붙는 보조 정보

```text
purpose
priority
reason
expected_sources
must_apply_filters
avoid_terms
```

## 필터와 제외 조건

검색어만으로 모든 조건을 표현하지 않는다.

예:

```text
price:20000-30000
gender:M
```

로고 없는 제품처럼 제외 조건이 있는 경우:

```text
avoid_terms:
- 로고
- 그래픽
- 프린트
```

## 자체 검수 항목

```text
정적 검사
단위 테스트
검색어 후보 검증
구현 스킬 실현 시뮬레이션
불필요한 주석 삭제
코드 충돌 여부 확인
전체 코드 라인 정리
HTML/SVG 확인 리포트 생성
```
