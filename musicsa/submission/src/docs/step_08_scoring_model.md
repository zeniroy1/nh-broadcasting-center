# 8단계 구현 기록: 점수화 모델 설계

## 목표

사용자 의도, 공개 지표, 대체 지표, 리뷰 보조 지표를 하나의 설명 가능한 점수 체계로 합친다.

이번 단계도 실제 무신사 네트워크 요청은 수행하지 않는다. 앞 단계에서 만들어진 공개/정제/추정 지표가 들어온다고 가정하고, 상품별 `final_score`와 `confidence_percent`를 계산하는 모델을 구현한다.

## 구현 파일

```text
src/config/scoring_weights.json
src/scripts/musinsa_scoring_model.py
src/tests/test_musinsa_scoring_model.py
src/tests/test_musinsa_proxy_metrics.py
src/tests/test_musinsa_review_signal_schema.py
```

## 기본 가중치

```text
purpose_fit_score: 26
purchase_trust_score: 16
review_purchase_evidence_score: 12
age_male_40s_fit_score: 12
buyer_context_profile_score: 8
price_fit_score: 12
popularity_proxy_score: 7
delivery_stock_score: 3
review_risk_score: 4
```

가중치 총합은 반드시 100이어야 한다. 가중치는 `src/config/scoring_weights.json`에서 조정할 수 있다.

## 산출 지표

```text
final_score
confidence_percent
rank_ready
components
penalties
explanation
cautions
```

## 점수 경계

`final_score`는 실제 구매 전환율이나 판매량이 아니다.

다음 공개/대체 지표를 합친 추천 계산값이다.

```text
목적 조건 일치
리뷰 수/평점/판매 라벨
리뷰 수 기반 구매 후 반응 누적 근거
남성/40대 랭킹 노출 추정
리뷰 키워드 기반 타겟 적합도 추정
가격 적합도
배송/품절 상태
리뷰 키워드 기반 리스크
광고/스폰서 여부
```

## 리뷰 수 반영 원칙

리뷰는 보통 구매 후 작성되는 공개 반응이므로 상품의 구매 경험이 누적되었다는 강한 방향성 근거로 사용할 수 있다.

다만 모든 구매자가 리뷰를 남기지는 않으므로 다음 표현을 금지한다.

```text
리뷰 수 = 실제 구매자 수
리뷰 수 = 실제 판매량
리뷰 수 = 연령/성별별 구매자 수
```

따라서 이번 단계에서는 `review_purchase_evidence_score`를 별도 컴포넌트로 두고, 다음 공개 단서를 합쳐 계산한다.

```text
review_volume_signal: 45
review_score_signal: 20
ranking_signal: 20
sales_label_signal: 15
confidence cap: 86%
```

## 리뷰 키워드 타겟 적합도

리뷰 본문에 포함된 단어는 목표 구매층과 맞을 가능성을 추정하는 보조 단서로 사용한다.

예:

```text
남편
아빠
출근
무난
재구매
선물
40대
```

이 단서는 `buyer_context_profile_score`로 반영한다. 단, 실제 구매자 속성 통계가 아니므로 신뢰도 상한은 72%로 제한한다.

## 신뢰도 원칙

`confidence_percent`는 정답 확률이 아니라 근거 충실도다.

```text
final_score confidence cap: 88%
review component confidence cap: 80%
inferred component confidence cap: 82%
```

## 감점 정책

```text
광고/스폰서 가능성: -3
품절 상품: -100
필수 공개 데이터 부족: -8
```

품절 상품은 `rank_ready=false`로 표시한다.

## 자체 검수 항목

```text
정적 검사
단위 테스트
점수화 모델 검증
구현 스킬 실현 시뮬레이션
불필요한 주석 삭제
코드 충돌 여부 확인
전체 코드 라인 정리
HTML/SVG 확인 리포트 생성
```
