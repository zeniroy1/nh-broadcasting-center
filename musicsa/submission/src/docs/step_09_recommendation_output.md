# 9단계 구현 기록: 후보 비교 및 추천 출력

## 목표

8단계에서 계산한 `final_score`와 `confidence_percent`를 사용자가 바로 판단할 수 있는 비교표, 추천 카드, 시각화 그래프, shortlist 세부 비교로 바꾼다.

이번 단계도 실제 무신사 네트워크 요청은 수행하지 않는다. 검색/상세/리뷰 수집이 끝난 후보 상품 목록이 들어온다고 가정하고, 점수화 결과를 구매 판단용 출력으로 정리한다.

## 구현 파일

```text
src/scripts/musinsa_recommendation_output.py
src/tests/test_musinsa_recommendation_output.py
src/docs/step_09_recommendation_output.md
src/docs/step_09_self_review.md
src/reports/step_09_recommendation_output_status.html
src/reports/step_09_recommendation_output_status.svg
```

## 출력 구조

```text
query
recommendation_count
winner_product_id
decision_summary
comparison_table
recommendation_cards
visualizations
shortlist_detail
purchase_roadmap
boundaries
next_step_hint
```

## 비교표 항목

```text
rank
brand
product
price
final_score
confidence_percent
decision
fit
```

비교표는 단순 순위표가 아니라 사용자가 후보를 빠르게 줄이기 위한 판단 표다. 초기 화면에서는 후보 5개를 보여주고, `final_score` 세로 막대그래프로 점수 차이를 함께 표시한다.

## 시각화 구조

```text
score_bar_chart
- 초기 5개 후보의 final_score를 세로 막대그래프로 비교한다.
- 막대마다 다른 색상과 축약 상품명을 사용해 눈에 편하게 만든다.
- 점수 차이를 빠르게 확인하는 1차 압축 화면이다.

shortlist_detail.component_segments
- 구매자가 3개 후보를 고른 뒤 세부 지표를 원형/도넛 그래프로 분해한다.
- 목적 적합도, 리뷰 기반 구매 반응, 가격 적합도, 타겟 적합도, 리뷰 리스크를 비교한다.
```

## 5개 후보에서 3개 shortlist로 줄이는 흐름

```text
1. 초기 후보 5개를 표와 세로 막대그래프로 본다.
2. 구매자가 관심 후보 3개를 고른다.
3. 선택된 3개는 세부 지표 도넛 그래프로 다시 비교한다.
4. 최종 후보 1~2개로 줄인 뒤 상세 페이지와 리뷰 원문을 확인한다.
```

## 추천 카드 항목

```text
브랜드
상품명
가격
final_score
confidence_percent
결정 라벨
적합도 라벨
추천 이유
공개 근거
주의점
```

추천 이유에는 목적 적합도, 리뷰 기반 구매 반응 누적 근거, 가격 적합도, 타겟 적합도 추정 점수를 사용한다.

공개 근거에는 가격, 리뷰 수, 평점, 판매 라벨, 랭킹 위치, 배송 상태, 점수 신뢰도를 표시한다.

주의점에는 광고/스폰서 가능성, 품절, 리뷰 리스크, 낮은 신뢰도, 대체 지표의 한계를 표시한다.

## 구매 판단 로드맵

```text
1. 초기 후보 5개를 final_score 세로 막대그래프로 비교한다.
2. 구매자가 관심 후보 3개를 shortlist로 고른다.
3. shortlist 3개는 목적/리뷰/가격/타겟/리스크 도넛 그래프로 세부 비교한다.
4. 최종 후보 1~2개로 줄인 뒤 상세 페이지와 리뷰 원문을 확인한다.
```

## 표현 경계

```text
추천 순위는 실제 판매 순위가 아니다.
리뷰 수는 실제 구매자 수나 판매량이 아니다.
리뷰 키워드 기반 타겟 적합도는 실제 연령/성별별 구매 통계가 아니다.
confidence_percent는 정답 확률이 아니라 공개 근거 충실도다.
```

## 샘플 결과

```text
후보 수: 5개
1순위: sample-black-tee
1순위 final_score: 96점
1순위 confidence_percent: 82%
2순위: sample-premium-tee
2순위 final_score: 87점
2순위 confidence_percent: 82%
3순위: sample-budget-tee
3순위 final_score: 81점
3순위 confidence_percent: 82%
shortlist 세부 비교: 3개
```

## 자체 검수 항목

```text
정적 검사
단위 테스트
추천 출력 검증
구현 스킬 실현 시뮬레이션
불필요한 주석 삭제
코드 충돌 여부 확인
전체 코드 라인 정리
HTML/SVG 확인 리포트 생성
```
