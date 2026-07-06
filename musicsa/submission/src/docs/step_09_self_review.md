# Step 09 Self Review

## 검수 대상

- 구현 파일: `src/scripts/musinsa_recommendation_output.py`
- 테스트 파일: `src/tests/test_musinsa_recommendation_output.py`
- 문서 파일: `src/docs/step_09_recommendation_output.md`
- UI 파일: `src/reports/step_09_recommendation_output_status.html`
- SVG 파일: `src/reports/step_09_recommendation_output_status.svg`

## 정적 검사

- `python -m py_compile src/scripts/musinsa_recommendation_output.py`
- 결과: 통과

## 구현 스킬 실현 시뮬레이션

입력:

```text
검은색 반팔 무지티를 2~3만원대에서 40대 남성이 입기 좋은 제품으로 찾아줘
```

결과 요약:

- 후보 수: 5개
- 비교표 행 수: 5개
- 추천 카드 수: 5개
- 1순위 상품: sample-black-tee
- 1순위 final_score: 96점
- 1순위 confidence_percent: 82%
- 세로 막대그래프 데이터: 5개
- shortlist 세부 비교: 3개
- 출력 경계 문구: 4개

## 자동 테스트

- 실행 명령: `python -m unittest discover -s src/tests -v`
- 결과: 51개 테스트 통과
- 9단계 추가 테스트:
  - 추천 출력 검증
  - 비교표와 추천 카드 존재 확인
  - 점수 기준 정렬 확인
  - 추천 이유/공개 근거/주의점 포함 확인
  - 실제 구매자 수 경계 문구 유지 확인
  - 초기 5개 후보 세로 막대그래프 데이터 확인
  - 세로 막대그래프 축약 상품명과 개별 색상 확인
  - 선택 3개 후보 세부 지표 분해 데이터 확인
  - 기존 모호한 표현을 타겟 적합도 표현으로 변경했는지 확인

## 내부 데이터 경계

- 추천 순위는 실제 판매 순위가 아니다.
- 리뷰 수는 실제 구매자 수나 실제 판매량이 아니다.
- 리뷰 키워드 기반 타겟 적합도는 실제 구매자 속성 통계가 아니다.
- `confidence_percent`는 정답 확률이 아니라 공개 근거 충실도다.

## 불필요한 주석 삭제

- 새 Python 구현에는 설명성 모듈 docstring 외 불필요한 주석을 넣지 않았다.
- HTML/SVG에는 확인용 표시 텍스트만 넣었다.

## 코드 충돌 여부

- 8단계 `musinsa_scoring_model.py` 결과를 입력으로 사용한다.
- 기존 점수 계산식을 변경하지 않고 출력 계층만 추가했다.
- 실제 네트워크 요청은 수행하지 않는다.

## 전체 코드 라인 정리

- 추천 출력은 점수 계산과 분리했다.
- 비교표, 추천 카드, 세로 막대그래프, shortlist 세부 비교, 구매 판단 로드맵, 경계 문구를 별도 필드로 분리했다.
- `final_score`와 `confidence_percent`가 사용자에게 함께 노출되도록 유지했다.

파일별 라인 수:

- `src/scripts/musinsa_recommendation_output.py`: 454 lines
- `src/scripts/musinsa_scoring_model.py`: 306 lines
- `src/scripts/musinsa_review_signal_schema.py`: 237 lines
- `src/tests/test_musinsa_recommendation_output.py`: 75 lines
- `src/docs/step_09_recommendation_output.md`: 139 lines
- `src/docs/step_09_self_review.md`: 88 lines
- `src/reports/step_09_recommendation_output_status.html`: 370 lines
- `src/reports/step_09_recommendation_output_status.svg`: 82 lines

## 다음 단계 대기 조건

사용자가 다음 단계 진행을 명시하기 전까지 10단계로 넘어가지 않는다.
