# Step 07 Self Review

## 검수 대상

- 설정 파일: `src/config/review_signal_keywords.json`
- 구현 파일: `src/scripts/musinsa_review_signal_schema.py`
- 테스트 파일: `src/tests/test_musinsa_review_signal_schema.py`
- 문서 파일: `src/docs/step_07_review_signal_design.md`
- UI 파일: `src/reports/step_07_review_signal_design_status.html`
- SVG 파일: `src/reports/step_07_review_signal_design_status.svg`

## 정적 검사

- `python -m py_compile src/scripts/musinsa_review_signal_schema.py`
- 결과: 통과

## 구현 스킬 실현 시뮬레이션

입력:

```text
검은색 반팔 무지티를 2~3만원대에서 40대 남성이 입기 좋은 제품으로 찾아줘
```

결과 요약:

- 리뷰 신호 카테고리: 12개
- 리뷰 보조 지표: 4개
- 분석 샘플 리뷰 수: 4개
- 긍정 신호 수: 6개
- 부정 신호 수: 3개
- 타겟 신호 수: 3개
- 신뢰도 상한: 80% 이하

## 자동 테스트

- 실행 명령: `python -m unittest discover -s src/tests -v`
- 결과: 41개 테스트 통과
- 7단계 추가 테스트:
  - 리뷰 신호 청사진 유효성
  - 필수 리뷰 카테고리 포함 여부
  - score/confidence_percent/limitation 포함 여부
  - 부정 리뷰가 원단 리스크 점수를 낮추는지 확인
  - 내부 데이터 경계 문구 확인

## 보조 지표 검수

```text
size_fit_review_score
fabric_risk_review_score
repurchase_mention_score
age_40s_context_review_score
```

모든 지표는 `score`, `confidence_percent`, `evidence`, `limitation`을 포함한다.

## 내부 데이터 경계

- 리뷰 키워드는 실제 반품률이 아니다.
- 재구매 언급은 실제 재구매율이 아니다.
- 40대 타겟 키워드는 실제 40대 구매자 수가 아니다.

## 불필요한 주석 삭제

- 새 Python 구현에는 설명성 모듈 docstring 외 불필요한 주석을 넣지 않았다.
- HTML/SVG에는 확인용 표시 텍스트만 넣었다.

## 코드 충돌 여부

- 6단계 `musinsa_detail_schema.py`의 상세 청사진을 입력 흐름으로 사용한다.
- 기존 1~6단계 데이터 구조를 변경하지 않았다.
- 실제 네트워크 요청은 수행하지 않는다.

## 전체 코드 라인 정리

- 리뷰 키워드는 JSON 설정으로 분리했다.
- 리뷰 분석은 순수 함수로 구성했다.
- 신뢰도는 리뷰 기반 추정 특성을 반영해 최대 80% 이하로 제한했다.

파일별 라인 수:

- `src/config/review_signal_keywords.json`: 126 lines
- `src/scripts/musinsa_review_signal_schema.py`: 193 lines
- `src/tests/test_musinsa_review_signal_schema.py`: 40 lines
- `src/docs/step_07_review_signal_design.md`: 72 lines
- `src/docs/step_07_self_review.md`: 66 lines
- `src/reports/step_07_review_signal_design_status.html`: 266 lines
- `src/reports/step_07_review_signal_design_status.svg`: 70 lines

## 다음 단계 대기 조건

사용자가 다음 단계 진행을 명시하기 전까지 8단계로 넘어가지 않는다.
