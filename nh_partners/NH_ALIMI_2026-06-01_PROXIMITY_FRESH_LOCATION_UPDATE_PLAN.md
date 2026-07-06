# NH알리미 근접 구간 Fresh 위치 확보 업데이트 기획서

**작성일:** 2026-06-01  
**대상 앱:** NH알리미  
**문서 목적:** 출퇴근 진입 알림 실탐률을 높이면서 기존 저전력 구조와 배터리 안정성을 유지하기 위한 다음 버전 구현 기준 확정

---

## 1. 배경

2026-06-01 출근 시 앱의 예약 시작, 백그라운드 감시, 네이티브 서비스는 정상 작동했으나 진입 알림이 발송되지 않았다.

로그상 앱은 목적지 접근을 추적했지만 `service_only` 저전력 상태에서 `lastKnown` 캐시 위치를 우선 사용했다. 도착 구간에서도 위치가 약 `81~85m`, 정확도 `93~100m` 수준에 머물러 실제 진입 순간의 위치를 확보하지 못했다.

현재 감지 반경은 `40m`다. 측정 오차가 반경보다 큰 상황에서는 기존 판정 로직이 정상이어도 진입을 확정할 수 없다.

---

## 2. 핵심 문제

### 2.1 저전력 입력값 고착

`background_recent`, `service_only` 상태에서는 배터리 절약을 위해 사용 가능한 `lastKnown` 위치를 우선 사용한다. 평상시에는 적절하지만 목적지 접근 순간에도 오래된 캐시가 유지되면 실제 진입을 놓칠 수 있다.

### 2.2 현재 Fresh 요청의 품질 한계

현재 fresh 요청은 이름과 달리 정밀 측정을 보장하지 않는다.

- Flutter 백그라운드 감시: `LocationAccuracy.medium`
- Android Native 보조 감시: `NETWORK_PROVIDER` 우선 단발 요청

따라서 fresh 요청을 실행해도 Wi-Fi 또는 기지국 기반의 `80~100m` 위치가 다시 들어올 수 있다.

### 2.3 접근대기 로직의 역할 확대

접근대기(`approach pending`)는 본래 애매한 위치값을 보조하기 위한 장치다. 그러나 현재 일부 초기 알림 후보 경로에서는 접근대기가 필수 `AND` 조건으로 작동한다.

보조 신호가 비어 있으면 기존 초기 알림 후보까지 막힐 수 있으므로, 접근대기는 실탐을 늘리는 보강 수단으로만 사용해야 한다.

---

## 3. 업데이트 목표

1. 기존 3.3 계열의 안정적인 알림 판정 틀을 유지한다.
2. 평상시에는 기존 저전력 감시를 유지한다.
3. 목적지 접근이 감지된 짧은 구간에서만 정밀 위치 요청을 실행한다.
4. 정밀 측정 실패 시 기존 저전력 경로로 안전하게 복귀한다.
5. 알림 반복, 출퇴근 확인 차단, 예약 시작·종료 로직에는 영향을 주지 않는다.
6. Flutter 백그라운드 감시와 Android Native 보조 감시가 동일한 정책으로 동작하게 한다.

미확인 저전력 상태에서 `lastKnown` 캐시가 장시간 고착되지 않도록 캐시 허용 시간은 `10분`에서 `3분`으로 제한한다. 알림 활성 상태와 출퇴근 확인 차단 상태의 절전값은 기존대로 유지한다.

---

## 4. 유지할 기존 정책

| 항목 | 유지 값 |
|---|---:|
| 기본 감지 반경 | `40m` |
| 이탈 기준 | `55m` |
| 평상시 백그라운드 감시 | `120초` |
| 접근권 감시 | 기존보다 짧게 조정 |
| 알림 시작 후 반복 알림 | `30초` |
| 알림 시작 후 위치 재확인 | `300초` |
| 출퇴근 확인 후 차단 상태 위치 재확인 | `300초` |
| 서대문역 기본 좌표 | 기존 설정 유지 |
| 위치보정 버튼 | 현재 위치를 기준점으로 저장 |

반경 확대 방식은 사용하지 않는다. 반경을 과도하게 넓히면 회사 위치와 서대문역 진입권이 겹쳐 출근·퇴근 사이클 분리가 어려워지고 오탐 가능성이 높아진다.

---

## 5. 제안 구조

### 5.1 전체 흐름

```text
평상시 원거리
  120초 간격 lastKnown 저전력 감시
        |
        v
목적지 200~300m 이내 접근 감지
  근접 정밀 측정 모드 진입
        |
        v
Native: GPS_PROVIDER 우선 단발 요청
Flutter: LocationAccuracy.high 단발 요청
        |
        v
60~80m 접근권 또는 불확실한 근접값
  제한된 횟수만 20~30초 간격 재확인
        |
        v
기존 진입 판정 로직으로 알림 결정
        |
        +--> 성공: 30초 반복 알림 시작
        |
        +--> 실패/timeout: 기존 lastKnown 또는 NETWORK 경로 fallback
```

### 5.2 중요한 원칙

정밀 측정 모드는 새로운 상시 감시 모드가 아니다. 목적지 근처에서만 잠깐 실행되는 보조 단계다.

기존 알림 판정을 대체하지 않는다. 기존 판정기가 더 신선한 입력값을 받을 수 있도록 돕는다.

---

## 6. 상태별 동작 정의

### 6.1 평상시 원거리

조건:

```text
목적지 거리 > 300m
알림 비활성
출퇴근 확인 차단 비활성
```

동작:

```text
120초 간격 저전력 감시
lastKnown 우선 사용
정밀 GPS 요청 안 함
```

### 6.2 근접 정밀 측정 모드

진입 조건:

```text
목적지 거리 <= 300m
알림 비활성
출퇴근 확인 차단 비활성
cooldown 미적용 상태
```

동작:

```text
Native: GPS_PROVIDER 우선 단발 요청
Flutter: LocationAccuracy.high 단발 요청
timeout: 10~15초
```

GPS 측정이 성공하면 해당 값을 기존 진입 판정기에 전달한다.

GPS 측정이 실패하거나 timeout이면 기존 `NETWORK_PROVIDER`, `LocationAccuracy.medium`, 사용 가능한 `lastKnown` 순서의 fallback으로 복귀한다.

### 6.3 접근권 재확인

조건:

```text
거리 60~80m
또는 근접 측정값의 정확도가 낮아 진입을 확정하기 어려움
```

동작:

```text
20~30초 후 fresh 재확인
최대 1~2회
무한 반복 금지
```

목적은 이동 중 짧은 진입 구간을 놓치지 않는 것이다. 정밀 GPS를 계속 유지하는 구조로 만들지 않는다.

### 6.4 진입 알림 활성

동작:

```text
초기 알림 1회 발송
NH파트너스 확인 전까지 30초 반복 알림 유지
위치 재확인은 300초로 완화
```

연속 알림은 위치 감시 주기와 분리한다. 위치 감시를 절전 상태로 낮춰도 반복 알림은 끊기지 않아야 한다.

### 6.5 출퇴근 확인 차단

조건:

```text
사용자가 NH파트너스 앱을 열어 출퇴근 확인 완료
dismissedUntilExit = true
```

동작:

```text
반복 알림 중지
300초 저전력 위치 재확인
근접 정밀 측정 모드 진입 금지
```

차단 상태에서 근접 정밀 요청을 반복하면 배터리 절감 효과가 사라질 수 있으므로 실행하지 않는다.

---

## 7. 접근대기 로직 정리

### 7.1 역할

접근대기는 진입 알림을 막는 필수 조건이 아니다. 다음과 같은 보조 데이터로만 사용한다.

```text
최근 목적지 접근 정황 존재
근접 fresh 재확인 필요
애매한 위치값을 즉시 폐기하지 않고 짧게 추적
```

### 7.2 변경 원칙

```text
현재 일부 경로:
  초기 알림 후보 AND 접근대기

변경 방향:
  기존 진입 판정 유지
  접근대기는 fresh 재확인 또는 보조 통과 판단에만 사용
```

단순히 접근대기 조건만 제거해서는 안 된다. 기존 오탐을 되살릴 수 있으므로 근접 fresh 재확인과 함께 조정한다.

---

## 8. 안전장치

### 8.1 Timeout

GPS 신호가 약한 실내, 지하, 고층 환경에서는 정밀 측정이 늦거나 실패할 수 있다.

```text
정밀 측정 timeout: 10~15초
timeout 발생 시 기존 저전력 경로 fallback
```

### 8.2 재시도 횟수 제한

```text
근접 구간 정밀 재시도: 최대 1~2회
```

무한 재시도는 금지한다.

### 8.3 Cooldown

GPS 튐으로 `300m` 경계를 반복 통과할 수 있다.

```text
정밀 측정 발동 후 cooldown: 2~5분
```

cooldown 동안에는 같은 조건으로 정밀 요청을 반복하지 않는다.

### 8.4 Fallback

```text
GPS_PROVIDER / high 실패
  -> NETWORK_PROVIDER 또는 medium
  -> 사용 가능한 lastKnown
  -> 기존 판정 및 다음 예약 유지
```

정밀 측정 실패가 감시 중단으로 이어져서는 안 된다.

### 8.5 권한 상태 기록

Android 설정에서 정밀 위치가 꺼져 있으면 `ACCESS_FINE_LOCATION` 선언만으로 충분하지 않다.

앱 실행 및 진단 로그에 다음 상태를 남긴다.

```text
위치 서비스 활성 여부
fine 위치 권한 여부
coarse 위치 권한 여부
background 위치 권한 여부
선택된 provider
fresh 요청 결과 정확도
fresh timeout 및 fallback 여부
```

---

## 9. Native 및 Flutter 정합성

두 감시 경로는 같은 정책을 사용해야 한다.

| 항목 | Flutter | Android Native |
|---|---|---|
| 평상시 절전 | `lastKnown` 우선 | `lastKnown` 우선 |
| 원거리 감시 | `120초` | `120초` |
| 근접 정밀 요청 | `LocationAccuracy.high` | `GPS_PROVIDER` 우선 |
| timeout | `10~15초` | `10~15초` |
| fallback | `medium`, `lastKnown` | `NETWORK_PROVIDER`, `lastKnown` |
| 접근권 재확인 | `20~30초`, 제한 횟수 | `20~30초`, 제한 횟수 |
| 알림 활성 위치 재확인 | `300초` | `300초` |
| 반복 알림 | `30초` | `30초` |

장기적으로 Native는 GPS 단독 호출보다 Fused Location Provider의 `PRIORITY_HIGH_ACCURACY`를 근접 구간에서만 사용하는 방향을 검토한다. 이번 버전에서는 변경 범위를 통제하기 위해 기존 `LocationManager` 구조를 유지하고 GPS 우선 fallback 방식으로 구현한다.

---

### 9.1 공유 검증 사이클 보강

초기 구현 점검에서 평상시 배터리 보호용 `3분` cooldown이 `30초` 재확인에도 적용되는 충돌이 확인되었다. 이 상태에서는 예약은 `30초`로 당겨져도 실제 입력값은 `lastKnown`으로 남을 수 있다.

Flutter와 Native는 독립적인 정밀 측정 루프를 만들지 않는다. SharedPreferences에 단일 검증 사이클 상태를 공유하고, 먼저 사이클을 확보한 한쪽만 GPS/high 요청을 실행한다.

```text
평상시 접근 감시
  3분 cooldown 검사
        |
        v
Flutter 또는 Native 중 먼저 확보한 쪽이 owner
        |
        v
0초 fresh + 30초 fresh + 60초 fresh
        |
        v
검증 종료 후 다시 3분 cooldown
```

공유 상태:

```text
cycle_active
cycle_owner
cycle_id
cycle_started_ms
cycle_finished_ms
rechecks_remaining
verified_at_ms
verified_distance_mm
verified_accuracy_mm
verified_source
```

거리와 정확도는 Flutter와 Android Native가 같은 형식으로 읽을 수 있도록 밀리미터 정수로 저장한다. 원시 위경도는 공유하지 않는다.

안전장치:

```text
owner만 내부 재확인 실행
다른 실행 주체는 최근 검증값을 소비하고 GPS를 중복 요청하지 않음
검증 사이클 내부 재확인은 최대 2회
검증 사이클 최대 유지 시간은 2분
검증 결과 재사용 시간은 최대 45초
알림 활성, 출퇴근 확인 차단, 300m 이탈 시 사이클 종료
```

이 구조는 `3분` cooldown을 제거하지 않는다. 평상시 반복 실행은 계속 제한하고, 하나의 검증 사이클 안에서만 두 번의 짧은 fresh 재확인을 허용한다.

---

## 10. 로그 기록 요구사항

개발자 로그에는 다음 항목을 남긴다.

```text
[NH알리미] 근접 정밀 측정 진입 — 거리:___m, source:lastKnown, cooldown:false
[NH알리미] 근접 정밀 측정 요청 — provider:gps, timeout:___초, attempt:1/2
[NH알리미] 근접 정밀 측정 성공 — 거리:___m, 정확도:___m, provider:gps
[NH알리미] 근접 정밀 측정 timeout — provider:gps, fallback:network
[NH알리미] 근접 정밀 측정 fallback — provider:network, 거리:___m, 정확도:___m
[NH알리미] 근접 재확인 예약 — ___초 후, attempt:___/2
[NH알리미] 근접 정밀 측정 cooldown 유지 — 남은시간:___초
[NH알리미] 위치 권한 상태 — fine:___, coarse:___, background:___
```

사용자 핵심 로그에는 다음만 간단히 남긴다.

```text
근접 위치 재확인 시작
근접 위치 재확인 성공
근접 위치 재확인 실패 후 일반 감시 유지
진입 알림 시작
```

---

## 11. 테스트 계획

### 11.1 정적 검사

```text
flutter analyze
flutter test
git diff --check
flutter build apk --debug
flutter build apk --release
```

### 11.2 단위 테스트

필수 케이스:

```text
원거리에서는 정밀 요청이 발생하지 않음
300m 이내 접근 시 정밀 요청 1회 발생
cooldown 동안 정밀 요청이 반복되지 않음
GPS timeout 시 fallback 후 감시가 유지됨
접근권 재확인이 최대 횟수를 넘지 않음
알림 활성 상태에서는 정밀 요청 없이 300초 위치 재확인
출퇴근 확인 차단 상태에서는 정밀 요청 없이 300초 위치 재확인
접근대기가 없어도 기존 reliableInside 경로가 차단되지 않음
```

### 11.3 실기 테스트

1. 앱을 설치하고 위치 권한을 `항상 허용`, 정밀 위치를 활성화한다.
2. 앱을 최근 앱에 둔 `background_recent` 상태로 서대문역 기준점에 접근한다.
3. 앱을 닫은 `service_only` 상태로 동일 경로를 다시 테스트한다.
4. 목적지 약 `200~300m` 구간에서 근접 정밀 측정 로그가 1회 발생하는지 확인한다.
5. 진입 시 즉시 또는 접근권 재확인 시간 내 알림이 시작되는지 확인한다.
6. 알림 시작 후 NH파트너스 앱을 열지 않고 `30초` 반복 알림이 유지되는지 확인한다.
7. NH파트너스 앱을 열어 알림을 중지한 뒤 정밀 위치 요청이 반복되지 않는지 확인한다.
8. 위치 권한의 정밀 위치를 끈 상태에서도 timeout 및 fallback이 정상 작동하는지 확인한다.

---

## 12. 배터리 영향 예상

평상시 `120초 + lastKnown` 절전 구조는 그대로 유지한다.

추가 전력 사용은 목적지 근처에서 실행되는 제한된 정밀 측정 `1~3회`에 집중된다. 상시 GPS 활성화가 아니므로 기존 안정화 버전 대비 배터리 증가 폭은 제한적일 것으로 예상한다.

실사용 검증에서는 다음 수치를 비교한다.

```text
Wake up 횟수
Wake lock 시간
GPS 사용 시간
Native 위치 요청 횟수
lastKnown 사용 횟수
근접 정밀 요청 횟수
timeout 횟수
fallback 횟수
초기 알림 성공 여부
알림 도착 지연 시간
```

---

## 13. 비적용 항목

이번 업데이트에는 다음 항목을 포함하지 않는다.

```text
상시 고정밀 GPS 감시
감지 반경 100~150m 확대
시간표 기반 출퇴근 판정 강화
칼만 필터 또는 센서 융합 직접 구현
가속도 센서 기반 이동 감지
geofence_service 패키지 교체
Fused Location Provider 전면 마이그레이션
```

이 항목들은 효과가 있을 수 있으나 변경 범위와 검증 비용이 크다. 이번 수정의 효과를 확인한 후 별도 버전에서 검토한다.

---

## 14. 롤백 기준

다음 문제가 확인되면 바로 이전 안정 버전으로 회귀한다.

```text
원거리에서 정밀 GPS 요청이 반복됨
GPS 사용 시간이 다시 장시간 유지됨
Wake up 또는 Wake lock이 비약적으로 증가함
출퇴근 확인 후 반복 알림이 중지되지 않음
알림 활성 중 위치 재확인이 300초보다 짧아짐
Native와 Flutter가 중복 팝업을 반복 발송함
예약 종료 19:00 또는 예약 시작 06:00 동작이 깨짐
```

---

## 15. 구현 우선순위

1. Flutter 및 Native 공통 근접 정밀 측정 상태 정의
2. `200~300m` 접근 시 GPS/high 우선 단발 요청 추가
3. timeout, fallback, 재시도 상한, cooldown 추가
4. 접근권 `20~30초` 제한 재확인 추가
5. 접근대기를 필수 게이트가 아닌 보조 로직으로 정리
6. 개발자 로그 및 사용자 핵심 로그 추가
7. 단위 테스트, 정적 검사, 실기 테스트
8. 배터리 사용량 비교 후 배포 여부 결정

---

## 16. 최종 결론

이번 업데이트의 목적은 감지 반경을 넓히거나 GPS를 상시 켜는 것이 아니다.

기존 저전력 구조를 유지하면서, 목적지 접근 순간에만 더 신선하고 정밀한 위치값을 확보하여 기존 알림 판정기가 정상적으로 판단할 수 있게 하는 것이다.

핵심 문장은 다음과 같다.

> 평상시에는 `120초 + lastKnown` 저전력 감시를 유지한다. 목적지 `200~300m` 이내 접근 구간에서만 Native는 `GPS_PROVIDER` 우선, Flutter는 `LocationAccuracy.high`로 일시 승격한다. timeout, 재시도 상한, cooldown, fallback을 반드시 함께 적용한다. 접근대기는 기존 알림을 막는 필수 조건이 아니라 실탐률을 보강하는 보조 데이터로만 사용한다.

---

## 17. 2026-06-01 안전장치 보완 적용

공유 검증 사이클 적용 후 확인된 오탐 및 중복 요청 가능성을 줄이기 위해 다음 방어 로직을 추가했다.

### 17.1 약한 fallback 후보의 즉시 알림 차단

```text
강한 후보:
  거리 50m 이하 + 정확도 80m 이하
  -> 기존처럼 알림 허용

약한 후보:
  거리 60m 이하 + 정확도 120m 이하
  -> 단순 lastKnown만으로는 알림 보류
  -> 공유 fresh 검증 사이클에서 얻은 값일 때만 알림 허용
```

이 변경은 회사 안에서 오래되거나 부정확한 캐시가 서대문역 근처로 튀어 오탐 알림을 만드는 상황을 줄인다.

### 17.2 Native 정밀 사이클 진입 전 캐시 유효성 검사

Native가 새로운 정밀 사이클을 열 때는 근접 판정에 사용하는 캐시의 age와 accuracy를 먼저 검사한다.

```text
허용 캐시 age: 최대 3분
허용 캐시 accuracy: 최대 150m
```

단, 이미 시작된 owner 재확인은 캐시가 오래됐다는 이유로 중단하지 않는다. 재확인 자체가 새로운 GPS 값을 확보하기 위한 작업이기 때문이다.

### 17.3 Flutter fallback 보강

Flutter 정밀 측정 순서를 다음처럼 보강했다.

```text
LocationAccuracy.high
  -> 실패 또는 timeout
LocationAccuracy.medium
  -> 실패 또는 timeout
기존 lastKnown 또는 기존 medium 판정 유지
```

`medium` fallback 성공값도 공유 fresh 결과로 기록하여 Native와 Flutter가 함께 재사용한다.

### 17.4 owner 선점 충돌 방어

Flutter와 Native가 거의 동시에 정밀 사이클을 시작해도 하나만 owner가 되도록 공통 lock 파일을 적용했다.

```text
공통 내부 파일:
  filesDir/nh_proximity_fresh_cycle.lock

owner 선점:
  Flutter와 Native 모두 exclusive create를 먼저 시도
  파일 생성에 성공한 한쪽만 사이클 owner가 됨
  lock 확보에 실패한 실행자는 GPS를 중복 요청하지 않음
  공유 fresh 값이 있으면 이를 재사용

안전장치:
  실제 high/GPS 요청 직전 prefs owner와 lock token을 함께 재검증
  비정상 종료로 남은 lock은 최대 2분 후 만료 처리

알림:
  Native 팝업 직전 Flutter/Native 공유 알림 활성 상태를 다시 검사
```

SharedPreferences만으로는 원자적 compare-and-swap을 보장할 수 없다. 공통 lock 파일의 원자 생성 결과를 owner 선점 기준으로 사용하여 Flutter와 Native의 중복 정밀 위치 요청을 구조적으로 차단한다.

### 17.5 추가 회귀 테스트

다음 조건을 단위 테스트로 고정했다.

```text
약한 캐시 후보는 fresh 검증 없이 알림 불가
약한 후보도 공유 fresh 검증 후에는 알림 가능
강한 후보는 추가 검증 없이 알림 가능
Flutter가 owner를 잃으면 정밀 GPS 요청 불가
완전한 공유 payload는 소비 가능
일부 필드만 기록된 공유 payload는 소비 불가
45초를 넘긴 공유 payload는 소비 불가
```

### 17.6 SharedPreferences 타입 및 부분 갱신 방어

Flutter `SharedPreferences.setInt()`는 Android에서 `Long`으로 저장된다. Native가 같은 값을 `getInt()`로 읽으면 `ClassCastException`이 발생할 수 있으므로, 공유 재확인 횟수는 Native에서도 `Long`으로 통일했다. 이전 설치 상태의 `Int` 값도 안전하게 읽을 수 있도록 호환 getter를 함께 적용했다.

공유 fresh 결과는 기존처럼 timestamp, distance, accuracy, source를 각각 저장하지 않는다. 다음 JSON payload 하나를 한 번의 `putString`으로 저장한다.

```json
{
  "verifiedAtMs": 0,
  "distanceMm": 0,
  "accuracyMm": 0,
  "source": "flutter 또는 native"
}
```

이 구조는 새 timestamp와 이전 distance가 섞이는 부분 갱신 소비를 막는다. payload가 불완전하거나, 음수 값이 있거나, 저장 후 45초를 초과하면 fresh 결과로 사용하지 않는다.
