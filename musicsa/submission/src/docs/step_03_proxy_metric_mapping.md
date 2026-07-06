# 3단계 구현 기록: 공개 지표와 대체 지표 매핑

## 목표

2단계에서 정의한 직접 지표와 정제 지표를 바탕으로 추정 지표를 계산하는 규칙을 구현한다.

핵심 원칙:

```text
추정 지표는 반드시 score와 confidence_percent를 함께 가진다.
score는 목적 적합성 점수다.
confidence_percent는 그 점수를 얼마나 믿을 수 있는지에 대한 신뢰도다.
```

## 구현 파일

```text
src/scripts/musinsa_proxy_metrics.py
src/tests/test_musinsa_proxy_metrics.py
```

## 구현한 추정 지표

```text
purpose_fit_score
age_male_40s_fit_score
purchase_trust_score
return_risk_score
repurchase_likelihood_score
```

## score와 confidence의 차이

```text
score:
상품이 사용자 목적에 얼마나 잘 맞는지 나타내는 점수

confidence_percent:
그 점수를 계산하는 공개 근거가 얼마나 충분한지 나타내는 신뢰도
```

예시:

```text
score: 90
confidence_percent: 45
→ 조건에는 잘 맞아 보이지만 공개 근거가 부족하다.

score: 78
confidence_percent: 90
→ 조건 적합도는 조금 낮지만 근거는 탄탄하다.
```

## 신뢰도 계산 원칙

신뢰도는 다음 기준을 반영한다.

```text
필수 공개 근거가 얼마나 있는가
사용 가능한 가중치 근거가 얼마나 많은가
핵심 근거가 누락되었는가
```

특히 다음 값은 실제 내부 데이터가 아니므로 신뢰도와 한계를 함께 표시한다.

```text
40대 남성 적합도
구매 신뢰도
반품 리스크
재구매 가능성
```

## CLI 사용 예시

정의 검증:

```text
python src/scripts/musinsa_proxy_metrics.py --validate
```

샘플 시뮬레이션:

```text
python src/scripts/musinsa_proxy_metrics.py --sample
```

## 자체 검수 항목

```text
정적 검사
단위 테스트
프록시 정의 검증
구현 스킬 실현 시뮬레이션
불필요한 주석 삭제
코드 충돌 여부 확인
전체 코드 라인 정리
HTML/SVG 확인 리포트 생성
```
