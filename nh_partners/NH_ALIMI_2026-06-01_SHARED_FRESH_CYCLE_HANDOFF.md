# NH알리미 근접 정밀 검증 사이클 작업 인수인계

작성일: 2026-06-01  
작업 폴더: `D:\codding\nh_partners\nh_reminder_v2_source_candidate_20260511`

## 1. 문서 목적

이 문서는 새 채팅에서 NH알리미 수정 작업을 바로 이어가기 위한 인수인계 자료다.

현재 코드는 저전력 감시 구조를 유지하면서 목적지 접근 순간에만 fresh 위치를 얻도록 보강된 상태다. Flutter와 Android Native가 동시에 GPS를 호출하지 않도록 공유 검증 사이클도 추가했다.

다만 마지막 검수에서 `pause 또는 19:00 종료`와 진행 중 위치 요청이 겹칠 때 발생할 수 있는 race condition 2건이 발견됐다. 이 2건은 아직 수정하지 않았다. release APK를 만들기 전에 먼저 보완해야 한다.

---

## 2. 유지해야 하는 핵심 제품 정책

### 2.1 기본 위치 감시

```text
평상시 background_recent / service_only:
  저전력 감시 유지
  기본 재확인 120초

접근권:
  반응 속도 보강
  필요 시 60초 재확인

알림 활성 상태:
  반복 알림은 30초 간격 유지
  위치 재확인은 300초 저전력으로 완화
```

반복 알림과 위치 감시는 분리되어 있다. 위치 감시가 300초로 느려져도 사용자가 NH파트너스 앱을 열어 확인하기 전까지 반복 알림은 30초 간격으로 유지되어야 한다.

### 2.2 감지 반경과 기본 좌표

```text
허용 감지 반경:
  최소 20m
  최대 50m

기본 반경:
  30m

서대문역 기본 좌표:
  lat 37.566
  lng 126.9673

초기 알림 후보 상한:
  60m 고정
```

서대문역 기본 위치 버튼을 누르면 위 좌표로 다시 설정된다. 위치보정 버튼은 현재 사용자 위치를 새 기준점으로 저장한다.

### 2.3 알림 후보 정책

```text
강한 후보:
  거리 50m 이하
  정확도 80m 이하
  추가 fresh 검증 없이 알림 허용

약한 후보:
  거리 60m 이하
  정확도 120m 이하
  lastKnown만으로 즉시 알림 금지
  공유 fresh 검증 사이클에서 얻은 값일 때만 알림 허용

접근 대기 seed:
  거리 60~80m
  정확도 30m 이하
  최대 5분 유지
  120m 초과 시 해제
```

약한 캐시 값으로 회사 안에서 서대문역 알림이 잘못 울리는 오탐을 막으면서, 실제 접근 시 fresh 위치로 실탐률을 보완하는 정책이다.

---

## 3. 2026-06-01 적용 완료 사항

### 3.1 근접 구간 fresh 위치 요청

목적지 약 `300m` 이내 접근 시 평상시 저전력 위치만 믿지 않고 제한적으로 fresh 위치를 요청한다.

```text
Flutter:
  LocationAccuracy.high
  실패 또는 timeout 시 LocationAccuracy.medium
  medium도 실패하면 기존 lastKnown 또는 기존 판정 유지

Native:
  GPS_PROVIDER 우선
  실패 또는 timeout 시 network/passive fallback
```

검증 사이클 내부에서는 다음 시점에 fresh 재측정을 허용한다.

```text
0초
30초
60초
```

검증 사이클 종료 후에는 다시 평상시 `3분 cooldown`으로 복귀한다. cooldown은 배터리 보호를 위한 값이며, 검증 사이클 내부 재확인을 막는 용도로 사용하지 않는다.

### 3.2 Flutter와 Native의 중복 GPS 요청 차단

SharedPreferences만으로 owner를 선점하면 원자적 compare-and-swap을 보장할 수 없다. Flutter와 Native가 동시에 비활성 상태를 읽으면 두 쪽이 모두 high GPS를 시작할 수 있다.

이를 막기 위해 공통 내부 lock 파일을 추가했다.

```text
filesDir/nh_proximity_fresh_cycle.lock
```

동작:

```text
Flutter와 Native 모두 lock 파일 exclusive create 시도
파일 생성에 성공한 한쪽만 owner 확보
owner만 high GPS 또는 GPS_PROVIDER 요청
다른 쪽은 중복 GPS 요청을 하지 않음
최근 공유 fresh 값이 있으면 재사용
비정상 종료로 남은 lock은 최대 2분 후 만료
```

Flutter `getApplicationSupportDirectory()`는 Android `filesDir`를 반환한다. Native도 `filesDir`를 사용하므로 양쪽이 같은 lock 파일을 본다.

적용 파일:

- `lib/services/background_monitor_service.dart`
- `android/app/src/main/kotlin/com/example/nh_reminder/NhBackgroundService.kt`

### 3.3 SharedPreferences 숫자 타입 충돌 방지

Flutter `SharedPreferences.setInt()`는 Android에서 `Long`으로 저장된다.

기존 검수에서 Native가 공유 재확인 횟수를 `getInt()`로 읽는 문제가 발견됐다. Flutter가 먼저 owner가 된 뒤 Native 타이머가 실행되면 `ClassCastException`이 발생할 수 있었다.

수정:

```text
Native 공유 재확인 횟수:
  getInt / putInt 제거
  Long 읽기·쓰기로 통일

호환 처리:
  이전 설치 상태에 Int가 남아 있어도 Long으로 변환하여 읽음
```

Native 호환 getter:

```text
getLongPreference(...)
```

### 3.4 공유 위치 결과의 부분 갱신 방지

기존에는 `timestamp`, `distance`, `accuracy`, `source`를 순차 저장했다. 동시에 다른 실행자가 읽으면 새 timestamp와 이전 거리값이 섞일 수 있었다.

수정 후에는 JSON payload 하나를 한 번의 `putString`으로 저장한다.

```json
{
  "verifiedAtMs": 0,
  "distanceMm": 0,
  "accuracyMm": 0,
  "source": "flutter 또는 native"
}
```

다음 payload는 사용하지 않는다.

```text
필수 필드가 누락됨
음수 값이 포함됨
저장 후 45초를 초과함
미래 timestamp 등 비정상 값
```

### 3.5 오탐 방어

약한 fallback 후보는 fresh 검증 없이 알림을 시작할 수 없도록 보강했다.

```text
strong 후보 또는 verified fresh 결과:
  알림 가능

오래되거나 부정확한 lastKnown 약한 후보:
  알림 보류
```

Native도 정밀 사이클 진입 전에 캐시 age와 accuracy를 검사한다.

```text
허용 캐시 age:
  최대 3분

허용 캐시 accuracy:
  최대 150m
```

---

## 4. 현재 검증 완료 결과

마지막 코드 수정 후 다음 검사를 통과했다.

```text
dart format:
  통과

flutter analyze:
  No issues found

flutter test:
  28개 전부 통과

git diff --check:
  공백 오류 없음
  LF -> CRLF 경고만 존재

충돌 마커 검색:
  <<<<<<<, =======, >>>>>>> 없음

방치 주석 검색:
  TODO, FIXME 없음

Native Kotlin debug 컴파일:
  통과
```

새로 추가된 회귀 테스트:

```text
약한 캐시는 fresh 검증 없이 알림 불가
약한 후보도 공유 fresh 검증 후에는 알림 가능
강한 후보는 추가 검증 없이 알림 가능
Flutter가 owner를 잃으면 fresh GPS 요청 불가
완전한 공유 JSON payload는 소비 가능
일부 필드만 기록된 payload는 소비 불가
45초를 넘긴 payload는 소비 불가
```

주의:

```text
사용자가 release APK 생성 중단을 요청함
release APK는 생성하지 않음
요청 도착 직전에 debug APK 빌드만 완료됨
```

---

## 5. 마지막 검수에서 발견된 미수정 이슈

아래 2건은 확인만 했고 아직 수정하지 않았다. 새 채팅에서 가장 먼저 처리해야 한다.

### 5.1 높음: pause 또는 19:00 종료 직후 Flutter 알림 재시작 가능

문제 흐름:

```text
18:59:55 Flutter fresh GPS 요청 시작
19:00:00 자동 종료
  is_paused = true
  모니터링과 알림 중지
19:00:05 진행 중이던 GPS 응답 도착
기존 메모리 상태로 판정
startReminder() 호출
알림이 다시 살아날 수 있음
```

원인:

- 위치 요청 전에만 pause 상태를 확인한다.
- fresh high 또는 fallback medium 요청이 끝난 뒤 SharedPreferences 최신 상태를 다시 읽지 않는다.
- `NotificationService.startReminder()`도 최종 pause gate를 갖고 있지 않다.

관련 파일:

- `lib/services/background_monitor_service.dart`
  - `runPositionCheck()`
  - `_getJudgmentForMonitor()` 이후
  - `NotificationService().startReminder()` 직전
- `lib/services/notification_service.dart`
  - `startReminder()`
- `lib/services/alarm_scheduler.dart`
  - `_onStopAlarm()`

권장 수정:

```text
Flutter 위치 요청 완료 직후:
  prefs.reload()
  is_paused 확인
  monitor_active 확인
  pause 또는 monitor_active=false이면 알림 시작 금지
  진행 중 cycle 정리 후 return false

NotificationService.startReminder() 직전:
  prefs.reload()
  is_paused 확인
  pause이면 알림 예약 및 notif_active=true 저장 금지
```

### 5.2 중간: 감시 중단 시 fresh cycle과 lock 파일 정리 누락

Flutter 일반 `BackgroundMonitorService.stop()`은 알람만 취소한다. 공유 fresh cycle과 lock 파일을 정리하지 않는다.

Native도 다음 경로에서 모니터링은 중단하지만 cycle cleanup을 호출하지 않는다.

```text
ACTION_STOP
stopServiceNow()
onDestroy()
```

영향:

```text
근접 fresh 측정 중 pause 또는 19:00 종료
이전 owner prefs와 lock 파일이 남음
재개 시 최대 2분간 새 검증 사이클이 막힐 수 있음
이전 재확인을 이어갈 가능성도 있음
```

관련 파일:

- `lib/services/background_monitor_service.dart`
  - `stop()`
  - `clearProximityFreshState()`
- `android/app/src/main/kotlin/com/example/nh_reminder/NhBackgroundService.kt`
  - `ACTION_STOP`
  - `stopServiceNow()`
  - `onDestroy()`
  - `finishNativeProximityFreshCycle()`
  - `clearNativeProximityFreshCycleLock()`

권장 수정:

```text
Flutter BackgroundMonitorService.stop():
  clearProximityFreshState(prefs) 호출

Native 종료 경로:
  finishNativeProximityFreshCycle(prefs) 호출
  active prefs가 없어도 lock 파일 직접 삭제
```

주의:

Native는 generation 검사로 종료 후 위치 callback 소비를 어느 정도 차단한다. Flutter 경로는 동일한 완료 후 gate가 부족하다.

---

## 6. 다음 채팅에서 권장하는 작업 순서

```text
1. 이 문서를 읽고 현재 상태 확인
2. pause / monitor_active 최종 gate 추가
3. Flutter stop()에서 fresh cycle 및 lock cleanup 추가
4. Native ACTION_STOP / stopServiceNow() / onDestroy() cleanup 추가
5. pause와 GPS 응답이 겹치는 race 회귀 테스트 추가
6. lock 파일 생명주기 테스트 또는 최소한 helper 테스트 추가
7. dart format
8. flutter analyze
9. flutter test
10. git diff --check
11. Native Kotlin debug 컴파일
12. 사용자가 승인하기 전에는 release APK 생성 금지
```

---

## 7. 실기 테스트 시나리오

### 7.1 근접 fresh 중복 요청 확인

```text
앱을 background_recent 또는 service_only 상태로 둠
지오펜스 약 200~300m 접근
로그 확인

기대:
  Flutter 또는 Native 한쪽만 검증 사이클 시작
  owner 한쪽만 high/GPS 요청
  다른 쪽은 공유값 재사용 또는 양보
```

### 7.2 pause race 확인

미수정 이슈를 보완한 후 반드시 확인한다.

```text
근접 fresh 요청이 시작된 직후 모니터링 OFF
또는 19:00 자동 종료 시점과 fresh 요청을 겹치게 테스트

기대:
  GPS 응답이 늦게 도착해도 알림 시작 안 함
  notif_active=false 유지
  공유 cycle과 lock 파일 정리
```

### 7.3 정상 진입 알림 확인

```text
background_recent 상태 진입
service_only 상태 진입

각각 확인:
  지오펜스 진입 시 초기 알림 도착
  알림 시작 후 30초 반복 유지
  NH파트너스 확인 후 반복 알림 중지
```

---

## 8. 관련 문서

- `D:\codding\nh_partners\NH_ALIMI_2026-06-01_PROXIMITY_FRESH_LOCATION_UPDATE_PLAN.md`
- `D:\codding\nh_partners\NH_ALIMI_2026-05-22_GEOFENCE_STABILITY_UPDATE_REPORT.md`

---

## 9. 작업트리 주의사항

현재 작업트리는 clean 상태가 아니다. 기존 수정 파일과 보고서가 남아 있다. 새 채팅에서 관련 없는 변경을 되돌리지 않는다.

현재 확인된 변경 파일:

```text
NH_ALIMI_2026-05-22_GEOFENCE_STABILITY_UPDATE_REPORT.md
nh_reminder_v2_source_candidate_20260511/android/app/src/main/kotlin/com/example/nh_reminder/NhBackgroundService.kt
nh_reminder_v2_source_candidate_20260511/lib/providers/settings_provider.dart
nh_reminder_v2_source_candidate_20260511/lib/services/background_monitor_service.dart
nh_reminder_v2_source_candidate_20260511/lib/services/monitoring_recovery_service.dart
nh_reminder_v2_source_candidate_20260511/test/widget_test.dart
```

미추적 보고서와 로그 폴더도 존재한다. 사용자 자료일 수 있으므로 임의 삭제하거나 커밋하지 않는다.

---

## 10. 새 채팅 시작용 요청문

아래 문장을 새 채팅에 그대로 전달하면 된다.

```text
D:\codding\nh_partners\NH_ALIMI_2026-06-01_SHARED_FRESH_CYCLE_HANDOFF.md
문서를 먼저 읽고 이어서 작업해줘.

문서 5장의 미수정 이슈 2건을 우선 수정해줘.
특히 pause 또는 19:00 종료와 진행 중 fresh GPS 응답이 겹쳐도 알림이 다시 살아나지 않도록 최종 gate를 넣고,
Flutter와 Native 종료 경로에서 fresh cycle 및 lock 파일을 정리해줘.

정적 검사와 테스트, debug Kotlin 컴파일까지만 진행하고 release APK는 만들지 마.
기존 작업트리의 관련 없는 변경은 되돌리지 마.
```
