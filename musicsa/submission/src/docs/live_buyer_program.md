# Live Buyer Program

## 목적

지금까지 만든 공개 지표 기반 추천 로드맵을 실제 사용자가 만질 수 있는 수집기와 UI로 연결한다.

사용자 입력 예시는 다음과 같다.

```text
검은색 반팔 무지티를 2~3만원대에서 40대 남성이 입기 좋은 제품으로 찾아줘
```

## 구현 파일

```text
src/scripts/musinsa_live_buyer_app.py
src/scripts/musinsa_buyer_server.py
src/scripts/musinsa_runtime_paths.py
src/tests/test_musinsa_live_buyer_app.py
src/tests/test_musinsa_buyer_server.py
src/tests/test_musinsa_runtime_paths.py
src/app/musinsa_buyer_app.html
src/packaging/musinsa_buyer_app.spec
src/packaging/build_exe.bat
src/reports/live_buyer_app_status.html
src/reports/live_buyer_app_status.svg
```

## 작동 흐름

```text
구매 의도 입력
검색어 후보 생성
무신사 공개 HTML/JSON 신호 수집
상품 후보 정규화
공개/대체/추정 지표 점수화
5개 후보 비교
3개 후보 shortlist 세부 비교
```

## 수집 대상

수집기는 공개 HTML 또는 공개 JSON 스크립트에 노출된 상품 후보를 찾는다.

수집 순서:

```text
1. 전달된 HTML 파일 안의 JSON 스크립트 파싱
2. 라이브 요청 시 랭킹 HTML 안의 공개 ranking API URL 탐색
3. 공개 ranking API JSON 파싱
4. 요청 카테고리/색상과 맞지 않는 후보 1차 제외
5. 부족한 후보는 sample_fallback으로 UI 흐름 보완
```

직접 수집 대상:

```text
상품명
브랜드명
상품 ID
가격
리뷰 수
리뷰 평점
랭킹 위치
상품 URL
이미지 URL
```

점수화에 연결되는 정규화 필드:

```text
product_id
product_name
brand_name
price
review_count
review_score
ranking_position
sales_label_count
colors
styles
gender
age_40s_ranking_position
```

## 수집하지 않는 대상

```text
실제 구매자 수
실제 판매량
40대 남성 실제 구매자 수
성별/연령별 전환율
광고 노출 가중치
무신사 내부 랭킹 알고리즘
상품별 장바구니 전환율
반품률
재구매율
```

위 항목은 공개 자료로 직접 확인할 수 없으므로 프로그램 결과에서도 단정하지 않는다.

## 실행 방식

저장된 HTML 파일을 파싱하는 방식:

```text
python src/scripts/musinsa_live_buyer_app.py --html-file saved_musinsa.html
```

라이브 공개 페이지를 직접 요청하는 방식:

```text
python src/scripts/musinsa_live_buyer_app.py --fetch-live
```

구매자 UI를 실제 실행하는 방식(소스에서 직접 실행):

```text
python src/scripts/musinsa_buyer_server.py --port 8765
```

서버가 뜨면 기본 브라우저가 `http://127.0.0.1:8765/`로 자동으로 열린다. 브라우저를 열지 않고 URL만 출력하려면 `--no-browser` 옵션을 추가한다.

이 주소에서 분석 버튼을 누르면 `/api/recommend`가 실행되고, 수집 결과가 화면에 반영된다.

라이브 요청은 사이트 응답 구조, 네트워크 상태, 접근 정책에 따라 실패할 수 있다. 실패해도 UI와 점수화 흐름은 sample_fallback으로 확인할 수 있다.

## 더블클릭 실행 (Windows EXE)

실 사용자가 파이썬 환경 없이 바로 쓸 수 있도록, `musinsa_buyer_server.py`를 PyInstaller로 단일 실행 파일(`MusinsaBuyerApp.exe`)로 묶을 수 있다.

빌드(Windows, `submission/src`에서):

```text
packaging\build_exe.bat
```

이 배치 파일은 PyInstaller 설치 → 전체 테스트 실행(안전장치) → `packaging/musinsa_buyer_app.spec` 기준 빌드를 순서대로 수행하고, 결과물을 `submission/src/dist/MusinsaBuyerApp.exe`에 만든다.

`MusinsaBuyerApp.exe`를 더블클릭했을 때의 동작:

```text
1. 콘솔 창 없이 로컬 서버가 127.0.0.1:8765에서 즉시 기동한다.
2. 잠시 후 기본 브라우저로 앱 화면이 자동으로 열린다.
3. 이미 실행 중인 상태에서 다시 더블클릭하면 새 서버를 만들지 않고
   기존 서버 주소로 브라우저만 다시 연다.
4. 콘솔이 없으므로 오류가 나면 화면 대신 exe 옆의
   musinsa_buyer_app.log 파일에 기록된다.
5. config/keyword_learning_queue.json은 exe 옆으로 복사되어 유지되므로,
   PyInstaller가 매 실행마다 지우는 임시 압축 해제 폴더가 아니라
   exe 옆 폴더에서 학습 큐가 재시작 후에도 이어진다.
```

즉 실 사용자 입장에서는 파이썬 설치나 명령줄 실행 없이, exe 파일 하나를 더블클릭하는 것만으로 검색기를 바로 열어볼 수 있다.

## 구매자 UI

브라우저에서 확인할 수 있는 파일:

```text
src/app/musinsa_buyer_app.html
```

단, 파일을 직접 열면 Python 수집기를 호출할 수 없다. 실제 실행은 `musinsa_buyer_server.py`로 로컬 서버를 띄우거나(소스 실행), `MusinsaBuyerApp.exe`를 더블클릭해(빌드된 배포본) 접속해야 한다.

UI 구성:

```text
검색 입력
수집/점수화 workflow
5개 후보 세로 막대그래프
비교표
3개 shortlist 선택
목적/리뷰/가격/타겟/리스크 세부 지표
공개 데이터 경계 문구
```

## 검수 기준

```text
공개 HTML fixture에서 상품 2개 이상 파싱
파싱 결과를 5개 후보 비교 흐름으로 연결
3개 shortlist 세부 비교 생성
실제 구매자 수와 내부 데이터 경계 유지
정적 검사와 전체 테스트 통과
```
