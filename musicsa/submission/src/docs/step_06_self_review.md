# Step 06 Self Review

## 검수 대상

- 설정 파일: `src/config/collection_scope.json`
- 5단계 갱신 파일: `src/scripts/musinsa_collection_planner.py`
- 6단계 구현 파일: `src/scripts/musinsa_detail_schema.py`
- 테스트 파일: `src/tests/test_musinsa_collection_planner.py`
- 테스트 파일: `src/tests/test_musinsa_detail_schema.py`
- 문서 파일: `src/docs/step_06_detail_data_schema.md`
- UI 파일: `src/reports/step_06_detail_data_schema_status.html`
- SVG 파일: `src/reports/step_06_detail_data_schema_status.svg`

## 정적 검사

- `python -m py_compile src/scripts/musinsa_collection_planner.py src/scripts/musinsa_detail_schema.py`
- 결과: 통과

## 구현 스킬 실현 시뮬레이션

입력:

```text
검은색 반팔 무지티를 2~3만원대에서 40대 남성이 입기 좋은 제품으로 찾아줘
```

결과 요약:

- 5단계 수집 설정 버전: `0.1.0`
- 5단계 목록 수집 작업 수: 14개
- 6단계 기본 상세 작업 수: 5개
- 상세 필드 수: 23개
- 추정 필드 수: 2개
- 추정 필드 최대 신뢰도: 82%

## 자동 테스트

- 실행 명령: `python -m unittest discover -s src/tests -v`
- 결과: 35개 테스트 통과
- 6단계 추가 테스트:
  - 상세 청사진 유효성
  - 필수 공개 필드 포함 여부
  - 추정 필드 신뢰도 상한 확인
  - 목록 작업에서 상세 작업 생성 여부
  - 내부 데이터 경계 문구 확인

## 오픈형 설정 검수

- `src/config/collection_scope.json`으로 수집 범위 설정을 분리했다.
- 사용자 지정 설정 파일을 전달하면 `config_version`과 총 수집량이 바뀌는 테스트를 추가했다.
- 코드 수정 없이 다음 항목을 바꿀 수 있다.

```text
소스별 max_items
소스별 max_pages
검색 목적별 multiplier
소스별 priority
1차 수집 제외 소스
목록형 소스 최소 수집량
광고/품절/중복 제거 정책 문구
```

## 불필요한 주석 삭제

- 새 Python 구현에는 설명성 모듈 docstring 외 불필요한 주석을 넣지 않았다.
- HTML/SVG에는 확인용 표시 텍스트만 넣었다.

## 코드 충돌 여부

- 1단계 Intent Parser와 직접 충돌 없음.
- 4단계 Query Generator 출력 구조와 호환됨.
- 5단계 Collection Planner는 기존 기본값을 유지하면서 JSON 설정을 읽도록 확장됨.
- 6단계 Detail Schema는 실제 네트워크 요청 없이 청사진만 생성하므로 외부 접근 부작용 없음.

## 내부 데이터 경계

- 실제 구매자 수를 수집하지 않는다.
- 연령대별 구매 비율을 수집하지 않는다.
- 무신사 내부 랭킹 알고리즘을 추정값처럼 단정하지 않는다.
- 40대 적합 관련 필드는 `age_40s_context_fit` 추정 필드로 두고 `confidence_percent`와 `limitation`을 포함한다.

## 전체 코드 라인 정리

- 상세 필드는 dataclass 목록으로 고정했다.
- 상세 작업 생성은 목록 수집 계획의 상위 작업을 받아 순수 함수로 만든다.
- 설정 로더는 기본 JSON 파일을 우선 읽고, 없으면 내부 기본값으로 fallback한다.

파일별 라인 수:

- `src/config/collection_scope.json`: 58 lines
- `src/scripts/musinsa_collection_planner.py`: 193 lines
- `src/scripts/musinsa_detail_schema.py`: 132 lines
- `src/tests/test_musinsa_collection_planner.py`: 87 lines
- `src/tests/test_musinsa_detail_schema.py`: 39 lines
- `src/docs/step_06_detail_data_schema.md`: 94 lines
- `src/reports/step_06_detail_data_schema_status.html`: 265 lines
- `src/reports/step_06_detail_data_schema_status.svg`: 77 lines

## 다음 단계 대기 조건

사용자가 다음 단계 진행을 명시하기 전까지 7단계로 넘어가지 않는다.
