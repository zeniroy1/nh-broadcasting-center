# 2단계 구현 기록: 무신사 공개 데이터 구조와 지표 카탈로그

## 목표

무신사 공개 자료에서 추출 가능한 원천 필드와 지표 풀을 정리한다.

이번 단계의 핵심은 지표를 다음 세 분류로 나누는 것이다.

```text
직접 지표: 무신사 공개 화면/API에서 그대로 가져올 수 있는 값
정제 지표: 공개 텍스트와 필드를 가공해 만드는 값
추정 지표: 직접/정제 지표를 조합해 가능성으로 계산하는 값
```

## 구현 파일

```text
src/scripts/musinsa_signal_catalog.py
src/tests/test_musinsa_signal_catalog.py
```

## 정의한 공개 데이터 소스

```text
ranking_page
search_results_page
category_page
product_detail_page
review_area
brand_page
```

## 직접 지표 예시

```text
상품 ID
상품명
브랜드명
판매가
할인율
리뷰 수
평점
랭킹 순위
판매 라벨
현재 보는 중/구매 중 라벨
배송 정보
품절 여부
```

## 정제 지표 예시

```text
색상 분류
스타일 분류
핏 분류
소재/착용감 분류
재구매 언급
낮은 평점 이슈
```

## 추정 지표 예시

```text
목적 적합도
40대 남성 적합도 추정
구매 신뢰도 추정
반품 리스크 추정
재구매 가능성 추정
```

## 신뢰도 정책

추정 지표는 반드시 신뢰도 퍼센트 정책을 가진다.

원칙:

```text
직접 지표: 공개 값 자체의 신뢰도는 100%에 가깝게 취급
정제 지표: 키워드/텍스트 매칭 강도에 따라 신뢰도 산정
추정 지표: score와 confidence_percent를 함께 출력
```

예시:

```text
40대 남성 적합도: 82점
추정 신뢰도: 68%
```

## CLI 사용 예시

카탈로그 요약:

```text
python src/scripts/musinsa_signal_catalog.py --summary
```

카탈로그 검증:

```text
python src/scripts/musinsa_signal_catalog.py --validate
```

사용자 요청 기반 수집 계획 생성:

```text
python src/scripts/musinsa_signal_catalog.py --plan "검은색 반팔 무지티를 2~3만원대에서 40대 남성이 입기 좋은 제품으로 찾아줘"
```

## 자체 검수 항목

```text
정적 검사
단위 테스트
카탈로그 유효성 검사
구현 스킬 실현 시뮬레이션
불필요한 주석 삭제
코드 충돌 여부 확인
전체 코드 라인 정리
HTML/SVG 확인 리포트 생성
```
