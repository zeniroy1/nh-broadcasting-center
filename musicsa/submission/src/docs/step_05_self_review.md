# Step 05 Self Review

## 검수 대상

- 구현 파일: `src/scripts/musinsa_collection_planner.py`
- 테스트 파일: `src/tests/test_musinsa_collection_planner.py`
- 문서 파일: `src/docs/step_05_collection_scope_planning.md`
- UI 파일: `src/reports/step_05_collection_scope_planning_status.html`
- SVG 파일: `src/reports/step_05_collection_scope_planning_status.svg`

## 정적 검사

- `python -m py_compile src/scripts/musinsa_collection_planner.py`
- 결과: 통과

## 구현 스킬 실현 시뮬레이션

입력:

```text
검은색 반팔 무지티를 2~3만원대에서 40대 남성이 입기 좋은 제품으로 찾아줘
```

결과 요약:

- 검색어 후보 수: 11개
- 수집 작업 수: 14개
- 중복 제거 전 최대 후보 수: 444개
- 목록형 소스: `search_results_page`, `ranking_page`, `category_page`
- 제외된 1차 소스: `product_detail_page`, `review_area`
- 이유: 상세/리뷰 영역은 1차 후보 목록을 만든 뒤 후속 단계에서 상품별로 접근해야 함

## 자동 테스트

- 실행 명령: `python -m unittest discover -s src/tests -v`
- 결과: 35개 테스트 통과
- 5단계 추가 테스트:
  - collection plan validation
  - policy existence
  - priority sorting
  - ranking/search source inclusion
  - filter preservation

## 정책 검수

- 광고/스폰서 상품은 제외하지 않고 `is_ad`로 표시한다.
- 품절 상품은 기본 비교 후보에서 제외하되 원본 표시는 보존할 수 있다.
- 중복 제거 기본 키는 `product_id`로 둔다.
- 보조 중복 제거 키는 `product_url`, `normalized_brand_name+normalized_product_name`이다.
- 실제 수집 단계에서는 요청 간격과 재시도 제한을 둔다.

## 불필요한 주석 삭제

- 새 구현 파일에는 설명성 모듈 docstring 외 불필요한 주석을 추가하지 않았다.
- HTML/SVG에는 표시 목적 텍스트만 포함했다.

## 코드 충돌 여부

- 1단계 `musinsa_intent_parser.py`와 연결된다.
- 4단계 `musinsa_query_generator.py`의 후보 구조를 입력으로 사용한다.
- 기존 공개 지표/추정 지표 구조는 변경하지 않았다.
- 내부 구매자 수, 전환율, 랭킹 알고리즘에 접근한다고 표현하지 않았다.

## 전체 코드 라인 정리

- 수집 계획 모듈은 dataclass와 순수 함수 중심으로 분리했다.
- 정렬 후 `job_id`를 다시 매겨 사람이 검토하기 쉬운 순서를 유지했다.
- 후속 실제 수집기 구현 전까지 네트워크 접근은 하지 않는다.
- 수집 범위 설정은 `src/config/collection_scope.json`으로 분리해 코드 수정 없이 조정할 수 있게 했다.

파일별 라인 수:

- `src/config/collection_scope.json`: 58 lines
- `src/scripts/musinsa_collection_planner.py`: 193 lines
- `src/tests/test_musinsa_collection_planner.py`: 87 lines
- `src/docs/step_05_collection_scope_planning.md`: 76 lines
- `src/reports/step_05_collection_scope_planning_status.html`: 273 lines
- `src/reports/step_05_collection_scope_planning_status.svg`: 77 lines

## 다음 단계 대기 조건

사용자가 다음 단계 진행을 명시하기 전까지 6단계로 넘어가지 않는다.
