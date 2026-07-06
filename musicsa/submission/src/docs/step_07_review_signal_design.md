# 7단계 구현 기록: 리뷰 기반 보조 지표 설계

## 목표

리뷰 원문에서 구매 판단에 도움이 되는 착용 경험 단서를 추출해 보조 지표로 만든다.

이번 단계도 실제 무신사 리뷰 요청은 수행하지 않는다. 상품 상세 후보에 `product_id`와 `product_url`이 붙은 뒤, 리뷰 영역에서 어떤 키워드를 어떤 신호로 해석할지 먼저 정의한다.

## 구현 파일

```text
src/config/review_signal_keywords.json
src/scripts/musinsa_review_signal_schema.py
src/tests/test_musinsa_review_signal_schema.py
```

## 리뷰 신호 카테고리

```text
size_positive
size_negative
sheerness_positive
sheerness_negative
neck_durability_negative
laundry_deformation_negative
fabric_positive
fabric_negative
fit_positive
fit_negative
repurchase_positive
age_40s_context
```

## 보조 지표

```text
size_fit_review_score
fabric_risk_review_score
repurchase_mention_score
age_40s_context_review_score
```

모든 보조 지표는 다음 값을 포함한다.

```text
score
confidence_percent
evidence
limitation
```

## 신뢰도 원칙

리뷰 기반 지표는 사용자 경험의 단서일 뿐, 플랫폼 내부 통계가 아니다.

따라서 다음 상한을 둔다.

```text
리뷰 신호 confidence_cap: 최대 80% 이하
보조 지표 confidence_percent: 최대 80% 이하
40대 타겟 리뷰 지표: 최대 68% 이하
재구매 언급 지표: 최대 70% 이하
```

## 내부 데이터 경계

다음처럼 표현하지 않는다.

```text
반품률이 낮다
재구매율이 높다
40대 남성이 많이 샀다
```

다음처럼 표현한다.

```text
낮은 평점 리뷰에서 사이즈/품질 불만 키워드가 적어 리스크가 낮을 가능성이 있습니다.
재구매 언급이 있어 만족도가 높을 가능성이 있습니다.
40대/남편/출근/무난함 타겟 키워드가 있어 40대 남성에게 적합할 가능성을 보조합니다.
```

## 자체 검수 항목

```text
정적 검사
단위 테스트
리뷰 신호 청사진 검증
구현 스킬 실현 시뮬레이션
불필요한 주석 삭제
코드 충돌 여부 확인
전체 코드 라인 정리
HTML/SVG 확인 리포트 생성
```
