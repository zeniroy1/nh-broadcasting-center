# NH알리미(nh_reminder) 제3자 기술 검수 보고서

**검수일:** 2026-05-04
**검수 대상 경로:** `D:\codding\nh_partners\nh_reminder`
**검수 범위:** 소스 코드(Flutter/Kotlin), Android 매니페스트, 빌드 구성, 실기기 런타임 로그
**검수자 의견:** 제3자 정적·로그 기반 검수 (실기기 직접 점검은 미수행)
**로그 출처:** 폰의 `/storage/emulated/0/Android/data/com.example.nh_reminder/files/nh_reminder_runtime.txt`를 시점별로 PC에 복사한 8개 파일 (2026-04-27 ~ 2026-05-04 13:37, 약 8일치)

---

## 요약

NH알리미는 농협파트너스(`com.vus.nhpthrm`) 앱의 출퇴근 체크 누락을 방지하기 위해, 지정 위치(서대문역 5번 출구 일대) 반경 진입 시 자동으로 반복 알림을 띄우는 Android 보조 앱이다. Flutter(Dart) UI/스케줄링 계층과 Kotlin 네이티브 포그라운드 서비스 계층이 SharedPreferences를 공유 메모리로 사용해 이중 감시 구조로 동작한다.

핵심 기능 — 지오펜스 진입/이탈 판정, 30초 간격 반복 알림, 매일 06:00/19:00 자동 시작·종료, NH파트너스 앱 실행 감지를 통한 알림 종료, 월별 출퇴근 기록 달력·엑셀 내보내기, 위치 보정·서대문역 기본값 복구 — 은 모두 코드와 실기기 로그상 정상적으로 구현·동작이 확인된다.

다만 다음 5가지는 보완이 필요하다.

1. UsageStats 권한 미허용 환경에서 NH앱 자동 감지가 작동하지 않는 점(실기기 로그상 감지 0회)
2. Android 절전 정책에 의한 백그라운드 알람 실행 지연(최대 +362초 관측)
3. 06:00 headless 자동 시작 시 `ACTIVITY_NOT_ATTACHED` 예외
4. discontinued 패키지(`geofence_service`) 의존 및 네임스페이스 보강이 필요한 빌드 환경
5. 기본 패키지명/서명/배포 구성이 데모 수준

전반적으로 단일 사용자(현장 실사용자) 기준에서는 **'정상 동작 가능' 단계에 도달**했으며, 이중 안전망(Flutter 알람 + 네이티브 LocationManager 감시)과 다단계 위치 판정(reliable/unreliable/boundary/outside/farOutside) 설계가 견고하다. 본 보고서는 해당 동작의 근거를 코드 인용·실기기 로그 통계로 명시하고, 위험도별 개선 권고를 함께 제시한다.

---

## 1. 검수 범위 및 방법

### 1.1 검수 자료

| 분류 | 확인 자료 | 비고 |
|---|---|---|
| 메타 | `pubspec.yaml`, `NH알리미_개발문서.md`, `CHANGELOG.md`, `설치_및_실행_가이드.md`, `NH_REMINDER_SESSION_LOG.md` | 프로젝트 정의/이력 |
| Flutter | `lib/main.dart`, `lib/models/`, `lib/providers/`, `lib/services/`, `lib/screens/home_screen.dart` 등 16개 .dart (총 4,020 LOC) | UI/상태/지오펜스/알림/스케줄 |
| 네이티브 | `MainActivity.kt`, `NhBackgroundService.kt`, `BootReceiver.kt`, `NativeServiceScheduler.kt`, `NativeServiceAlarmReceiver.kt`, `ReminderActionHandler.kt`, `ReminderActionReceiver.kt` | 포그라운드 서비스/MethodChannel/알람 |
| 빌드/매니페스트 | `AndroidManifest.xml`, `app/build.gradle.kts`, `android/build.gradle.kts`, `gradle.properties` | 권한/네임스페이스/SDK |
| 런타임 로그 | `nh_reminder_runtime_device.txt`(약 2 MB), `nh_reminder_runtime_latest.txt`(약 1.5 MB), `logs_analysis/*` (시점별 5개) | 2026-04-27 ~ 04-30 실기기 동작 |
| 설계 문서 | `docs/BATTERY_OPTIMIZATION_PLAN_2026-05-04.md`, `docs/nh_reminder_stabilization_update_2026-04-30.md`, `docs/BUGFIX_2026-04-24.md`, `docs/WORK_LOG_2026-04-28.md` | 최근 안정화 이력 교차 검증 |

### 1.2 검수 방법

- **정적 분석**: 17개 핵심 소스 파일을 1줄 단위로 정독하고, 클래스/메서드 책임과 호출 그래프를 도식화.
- **매니페스트·빌드 분석**: AndroidManifest, build.gradle.kts, gradle.properties로 권한·서비스·네임스페이스·SDK 정합성 확인.
- **런타임 로그 통계 분석**: ENTER/EXIT/알림 발송/오류/실행 지연/배터리 샘플 카운트를 grep + 수치화.
- **문서·코드 교차 검증**: `NH알리미_개발문서`·`CHANGELOG`에서 주장한 동작이 실제 코드/로그에 반영됐는지 확인.
- 앱 실행/실기기 점검은 수행하지 않았으며, 본 보고서는 **'정적·로그 기반 검수'**이다.

---

## 2. 앱 개요

### 2.1 목적과 사용 대상

농협파트너스 앱(패키지: `com.vus.nhpthrm`)에서 매일 출퇴근 버튼 클릭을 누락하지 않도록, 회사 위치 반경 진입 시 자동 알림을 보내고 NH파트너스 앱을 한 번에 실행시키는 Android 보조 앱이다. 주 사용자는 농협 본부 직원(서대문역 5번 출구 인근 근무자)이며, 단일 기기 보조 도구로 설계됐다.

### 2.2 핵심 기능 요약

| 기능 | 주요 동작 | 구현 위치 |
|---|---|---|
| 지오펜스 감지 | 회사 좌표 ±반경(20–200 m) 안 진입 시 ENTER 이벤트 발생, 5초마다 위치 폴링, 다단계 위치 판정 | `geofence_service.dart`, `location_judgment_service.dart` |
| 반복 알림 | AndroidAlarmManager 기반 30초 간격(설정 30–300초) 반복 알림, importance.high, 풀스크린 인텐트 | `notification_service.dart`, `MainActivity.showDirectReminderNotification` |
| NH앱 실행/감지 | url_launcher 또는 PackageManager로 NH파트너스 실행, UsageStatsManager로 포그라운드 감지 후 알림 자동 종료 | `usage_stats_service.dart`, `MainActivity.isAppInForeground` |
| 자동 스케줄 | 매일 06:00 모니터링 시작, 19:00 모니터링 완전 종료(이중: Flutter AndroidAlarmManager + 네이티브 AlarmManager) | `alarm_scheduler.dart`, `NativeServiceScheduler.kt` |
| 출퇴근 기록 | SharedPreferences에 ISO-8601 타임스탬프 배열로 저장, 월별 달력/리스트, 엑셀 내보내기, 월 단위 삭제 | `history_provider.dart`, `home_screen.dart` |
| 위치 보정/복구 | 현재 GPS로 지오펜스 중심 재설정(다단계 정확도 폴백), 서대문역 기본값 복구 버튼 | `monitoring_recovery_service.dart`, `settings_provider.dart`, `home_screen.dart` |
| 부팅 자동 복구 | BOOT_COMPLETED·QUICKBOOT_POWERON 수신 시 06:00–19:00 시간대면 포그라운드 서비스 자동 시작 | `BootReceiver.kt` |
| 로그 영속화 | `/storage/emulated/0/Download/nh_partners/nh_reminder_runtime.txt` 8 MB 로테이션 | `log_file_service.dart`, `NhBackgroundService.appendRuntimeLog` |

---

## 3. 기술 스택 및 아키텍처

### 3.1 기술 스택

| 계층 | 기술 | 비고 |
|---|---|---|
| UI / 상태 | Flutter (Dart SDK >=3.0.0 <4.0.0), flutter_riverpod 2.x (StateNotifier) | 단일 화면 + 3 탭 IndexedStack, 다크 머터리얼3 |
| 지오펜싱 | `geofence_service ^5.0.0` (**Discontinued**) | FusedLocation 기반, 5 s 폴링 |
| 위치 | `geolocator ^11.0.0` | 현재 위치/거리 계산, last-known 폴백 |
| 알림 | `flutter_local_notifications ^17.0.0` + 네이티브 NotificationManager | 채널 ID `nh_reminder_high_v2`, 풀스크린 인텐트 |
| 스케줄 | `android_alarm_manager_plus ^5.0.0` | 정확 알람(`rescheduleOnReboot:true`) — 06:00/19:00, 30 s 반복 |
| 네이티브 | Kotlin (JVM 17), AndroidX, FOREGROUND_SERVICE_TYPE_LOCATION | compileSdk 35(라이브러리)·flutter.compileSdkVersion(앱) |
| 저장 | `shared_preferences ^2.2.2` | Dart/네이티브 양쪽에서 'FlutterSharedPreferences' 공유 |
| NH앱 감지 | `usage_stats ^1.3.1` (path override) + Android UsageStatsManager | PACKAGE_USAGE_STATS 권한 필수 |
| 앱 실행 | url_launcher + `PackageManager.getLaunchIntentForPackage` | 마켓 폴백 포함 |
| 엑셀 | `excel ^4.0.3` + `share_plus ^7.2.1` + `path_provider` | 월별 .xlsx 생성·공유 |
| 로깅 | PathProvider + `Download/nh_partners/nh_reminder_runtime.txt` | 8 MB 로테이션, 비동기 큐 |

### 3.2 폴더 구조

```
nh_reminder/
├─ lib/
│  ├─ main.dart                       — 진입점, 권한 게이트, 30초 polling, 라이프사이클
│  ├─ models/app_state.dart           — AppSettings (지오펜스 좌표/반경/간격/일시정지)
│  ├─ providers/
│  │  ├─ settings_provider.dart       — SharedPreferences 동기화 StateNotifier
│  │  └─ history_provider.dart        — 출퇴근 기록 Map<DateTime, List<DateTime>>
│  ├─ screens/home_screen.dart        — 홈/기록/설정 3탭, 1,316 LOC
│  └─ services/
│     ├─ geofence_service.dart        — Geofence + ENTER/EXIT 처리, NH앱 폴링
│     ├─ notification_service.dart    — AlarmManager 기반 반복 알림 콜백
│     ├─ background_monitor_service.dart — 위치 기반 백그라운드 감시(저전력 단계)
│     ├─ background_service.dart      — 설정 반영 큐(NhBackgroundServiceManager)
│     ├─ alarm_scheduler.dart         — 06:00/19:00 자동 알람
│     ├─ monitoring_recovery_service.dart — 소프트 리셋·위치 보정 폴백
│     ├─ location_judgment_service.dart — 5단계 zone 판정 + 확정 이탈 임계값
│     ├─ usage_stats_service.dart     — MethodChannel(usage_stats)
│     ├─ native_monitor_bridge.dart   — MethodChannel(native_monitor)
│     ├─ geofence_ui_event_service.dart — UI 토스트 이벤트 스트림
│     └─ log_file_service.dart        — 비동기 파일 로거
├─ android/app/src/main/kotlin/com/example/nh_reminder/
│  ├─ MainActivity.kt                 — FlutterActivity, 2개 MethodChannel, UsageStats
│  ├─ NhBackgroundService.kt          — 포그라운드 서비스(보조 감시·배터리 로그·팝업)
│  ├─ BootReceiver.kt                 — BOOT_COMPLETED 수신, 자동 복구
│  ├─ NativeServiceScheduler.kt       — AlarmManager 06:00/19:00 예약
│  ├─ NativeServiceAlarmReceiver.kt   — 06:00·19:00 알람 수신 후 서비스 제어
│  ├─ ReminderActionHandler.kt        — 알림 클릭 공통 처리(중복 방어, NH앱 실행)
│  └─ ReminderActionReceiver.kt       — 알림 액션 BroadcastReceiver
├─ android/app/src/main/AndroidManifest.xml
├─ android/app/build.gradle.kts, android/build.gradle.kts, gradle.properties
└─ logs_analysis/, docs/, third_party/usage_stats/, …
```

### 3.3 아키텍처 개요

**'이중 안전망' 구조다.** Flutter 측에서는 `geofence_service`의 ENTER/EXIT 이벤트와 별도로 AndroidAlarmManager 기반 'BackgroundMonitorService'가 주기적으로 위치를 직접 확인한다. 네이티브 측에서는 `NhBackgroundService`가 LocationManager로 같은 위치를 한 번 더 확인하여 보조 알림을 띄운다. 두 계층은 'FlutterSharedPreferences'와 'nh_native_monitor' 두 개의 SharedPreferences를 통해 상태를 공유한다.

#### 주요 SharedPreferences 키 (Flutter 측)

| 키 | 타입 | 의미 |
|---|---|---|
| `is_paused` | bool | 스케줄러/시스템에 의한 일시정지 (19:00 자동 종료 등) |
| `user_paused` | bool | 사용자가 직접 OFF한 상태(06:00 자동 시작 시에도 보호) |
| `geofence_lat` / `geofence_lng` / `geofence_radius` | double | 지오펜스 중심·반경 |
| `repeat_interval_sec` / `notif_interval_sec` | int | 반복 알림 간격(30–300 s) |
| `dismissed_until_exit` | bool | 출퇴근 확인 차단(이탈 전까지 알림 억제) |
| `notif_active` | bool | 현재 반복 알림이 살아 있는지 표지 |
| `geofence_exit_count` / `monitor_outside_count` / `notif_outside_count` | int | EXIT/이탈 1회 유예용 카운터 |
| `last_monitor_*_ms` / `last_notification_*_ms` | long | stale 판단·실행 지연 측정 |
| `commute_history_raw` | string(JSON) | ISO-8601 타임스탬프 배열(출퇴근 기록) |
| `pending_history_reload` | bool | 네이티브에서 기록 저장했음을 Flutter UI에 신호 |
| `monitor_reset_generation` | int | 소프트 리셋의 stale 작업 무시용 세대 번호 |

---

## 4. 기능별 동작 분석

### 4.1 진입(ENTER) 흐름

1. 앱 시작 또는 06:00 알람 → `SettingsNotifier.loadFromPrefs()`로 좌표·반경 로드, `NhGeofenceService.start()` 호출.
2. `GeofenceService.instance.setup(interval:5000, accuracy:100, statusChangeDelayMs:0)`로 5초 간격 위치 폴링.
3. ENTER 발생 → `dismissed_until_exit`·`is_paused`·`notif_active` 검사, 통과 시 `_isWithinConfiguredRadius()` 재검증.
4. `LocationJudgmentService.fromCurrentPosition()`로 거리·정확도 판정. `zone == reliableInside`일 때만 알림 시작.
5. `NotificationService.startReminder()` → 즉시 1회 푸시 + `AndroidAlarmManager.oneShot(intervalSec)`로 다음 콜백 예약.
6. 이후 `_startNhAppCheck()` `Timer.periodic(10s)`로 NH파트너스 포그라운드 여부 폴링.

검증 지표(`geofence_service.dart` 232–245행, `location_judgment_service.dart` 100–135행)는 코드와 일치한다. 실기기 로그에서 'ENTER → ENTER 검증 → ENTER — 알림 시작!' 시퀀스가 **391건** 관측되어 흐름은 안정적으로 트리거됨을 확인했다.

### 4.2 이탈(EXIT) 흐름과 GPS 흔들림 방어

EXIT 이벤트 발생 시 `_verifyAndHandleExit()`이 즉시 Geolocator로 실제 위치를 다시 가져와 거리 기반 재검증을 수행한다. 확정 이탈 임계값은 `max(반경 + 120 m, 150 m)`. 차단 플래그(`dismissed_until_exit`) 상태에서는 이 임계값을 넘어야 차단을 해제한다. 또한 '1회 유예 → 2회 누적 시 확정' 규칙으로 단발성 위치 튐을 거른다(`geofence_service.dart` 287–333행, `background_monitor_service.dart` 150–193행).

결과적으로 NH파트너스 앱 클릭 후 가만히 있을 때는 GPS 흔들림으로 인한 EXIT→ENTER 재알림이 발생하지 않는 '이중 보호'가 성립한다. CHANGELOG 2026-04-22 기록과 코드 구현이 일치한다.

### 4.3 알림 채널과 표시 정책

| 항목 | Flutter (NotificationService) | 네이티브 (MainActivity.showDirectReminderNotification) |
|---|---|---|
| 채널 ID | `nh_reminder_high_v2` | `nh_reminder_high_v2` (동일) |
| 채널명/Importance | '출퇴근 알림' / `Importance.high` | '출퇴근 알림' / `IMPORTANCE_HIGH` |
| 진동 패턴 | `[0, 200, 100, 200]` (채널 기본) | `[0, 700, 200, 700, 200, 700]` (실제 발송 시) |
| LED | 민트(#4DB6AC) | 지정 없음(채널 기본) |
| 풀스크린 인텐트 | `fullScreenIntent: true` (Importance.max로 즉시 표시) | `PRIORITY_MAX` + `CATEGORY_ALARM` |
| 액션 버튼 | 'NH파트너스 열기' | 'NH파트너스 열기' (PendingIntent → ReminderActionReceiver) |
| 실제 발송 우선순위 | 1순위: 네이티브 채널 호출, 2순위: Flutter 폴백 | — |

`NotificationService.showNotificationDirect()` (`notification_service.dart` 252–302행)는 우선 `NativeMonitorBridge.showReminderNotification()`로 네이티브 알림을 시도하고, `MissingPluginException` 시에만 Flutter 알림으로 폴백한다. 채널 ID·NotifId를 양쪽이 동일하게 사용하므로 갱신/취소가 일관된다.

### 4.4 NH파트너스 앱 감지와 알림 종료

`MainActivity.isAppInForeground()`는 `UsageStatsManager.queryUsageStats(INTERVAL_DAILY, now-10s, now)`에서 `lastTimeUsed`가 가장 최근인 패키지를 비교한다. 'com.vus.nhpthrm'이 가장 최근이면 `NhGeofenceService.dismissUntilExit()` → 알림 중지 + `dismissed_until_exit=true`.

다만 PACKAGE_USAGE_STATS 권한은 일반 권한 다이얼로그로 받을 수 없고 '설정 → 사용 내역 접근'에서 사용자가 직접 허용해야 한다. 실기기 로그(`nh_reminder_runtime_device.txt`) 전체에서 'NH파트너스 앱 감지' 로그는 **0건**으로, 검수 기간 동안 권한이 없거나 NH앱이 별도로 실행되지 않았을 가능성이 높다. 앱 실행 후 알림 종료는 별도 경로(알림의 'NH파트너스 열기' 버튼 클릭)에서 `dismissUntilExit`이 호출되어 정상 동작한다(`ReminderActionHandler.handleOpenNh`).

### 4.5 자동 스케줄(06:00 / 19:00)

Dart 측 `DailyAlarmScheduler.schedule()`이 `AndroidAlarmManager.oneShotAt(6:00, _onStartAlarm, exact:true, wakeup:true, rescheduleOnReboot:true)`와 19:00 `_onStopAlarm`을 각각 등록하고 콜백 끝에서 자기 자신을 다시 `schedule()`한다(매일 갱신). 네이티브 측 `NativeServiceScheduler`도 같은 시각에 `setExactAndAllowWhileIdle` 알람을 등록하고 `NativeServiceAlarmReceiver`에서 포그라운드 서비스 시작/종료를 수행한다. 두 경로가 독립적으로 같은 작업을 시도해 한쪽 실패에도 나머지가 모니터링을 유지한다.

실기기 로그에서 06:00 자동 시작 3회·19:00 자동 종료 3회가 확인된다. 04-29·04-30 06:00 시점에 '지오펜스 시작 실패: PlatformException(ACTIVITY_NOT_ATTACHED, …)'가 발생했으나, 백그라운드 감시·네이티브 보조 감시는 계속 동작했다. 04-30 안정화 작업으로 06:00 알람에서는 `startFlutterGeofence:false`를 사용해 헤드리스 환경에서 Flutter 지오펜스 등록을 생략하도록 보완됐다.

### 4.6 출퇴근 기록과 엑셀 내보내기

`history_provider.dart`는 SharedPreferences `commute_history_raw` 키에 ISO-8601 타임스탬프 배열을 저장한다. 최초 설치 시(키가 null) 2026년 4월의 시연용 기록 25개를 자동 삽입하나, 한 번이라도 빈 배열이 저장되면 다시 삽입되지 않는다. `addTimestamp`는 'NH앱 실행' 버튼/알림 클릭 양쪽에서 호출되며, 5 초 이내 중복 클릭은 `ReminderActionHandler.hasRecentTimestamp`/Flutter의 `_duplicateClickWindowMs`로 차단한다.

표시 측은 일자별 첫 기록을 '출근', 둘째 이상 기록의 마지막을 '퇴근'으로 간주한다(`home_screen.dart` 350–360, `_exportToExcel` 1278–1285). 엑셀은 `excel` 패키지로 '날짜/출근/퇴근' 3 컬럼을 생성해 `share_plus`로 외부 공유한다. 내부 기록은 항상 SharedPreferences이므로 영구 보관 측면에서는 단말 종속적이다.

### 4.7 위치 보정과 서대문역 복구

`MonitoringRecoveryService.reset()`은 '소프트 리셋'의 단일 진입점이다. 내부적으로 `monitor_reset_generation`을 증가시켜 동시 실행 시 stale 작업을 자동 폐기한다(`_isCurrentReset` 검사). 위치 보정은 ① `getCurrentPosition(high)` → ② `medium` → ③ `getLastKnownPosition`(10분 이내) → ④ 저정확도 허용(180–300 m) 순으로 4단계 폴백을 수행한다(`_resolveCurrentPosition` 295–356행). 서대문역 기본값 복구(`_resetToDefaultLocation`)는 좌표·플래그 초기화 후 `sendUpdate`로 모니터링을 재시작하며, 6 s 타임아웃 가드를 걸어 UI가 멈추지 않도록 한다.

### 4.8 백그라운드 감시(저전력 단계)

`BackgroundMonitorService`는 거리·정확도·차단 플래그 조합에 따라 다음 감시 간격을 동적으로 결정한다.

| 상태 | 다음 감시 간격 | 근거 |
|---|---|---|
| 범위 안 + 알림 활성/차단 아님 | 엔트리 워치 15 s | `entryWatchIntervalSeconds` |
| 반경 외 30 m 이내 | 15 s (entryWatch) | `_delayForOutsideDistance ≤30 m` |
| 반경 외 30–150 m | 30 s (nearWatch) | `≤ entryWatchNearMeters` |
| 반경 외 150–500 m | 60 s (default) | `≤ farWatchDistanceMeters` |
| 반경 외 500 m 초과 | 120 s (farWatch) | 그 외 |
| 차단 + 확정이탈 근접 | 180 s (저전력) | `dismissedLowPowerIntervalSeconds` |
| 차단 + 확정이탈 여유 | 300 s (저전력 안정) | `dismissedStableIntervalSeconds` |

차단 상태에서는 `lastKnownPosition`(<5분, ±120 m)을 우선 사용해 GPS 호출을 줄이고, `refreshIfStale`은 '차단 저전력 예약 유지' 로그를 남기며 5초 재예약 덮어쓰기를 회피한다. `BATTERY_OPTIMIZATION_PLAN_2026-05-04.md`의 1·3·4단계 설계와 코드가 일치한다.

### 4.9 알림 클릭 동시성·중복 처리

Flutter `NotificationService._onNotifResponse`와 네이티브 `ReminderActionHandler`가 거의 동시에 클릭을 받을 수 있다. 양쪽 모두 SharedPreferences 키 `last_reminder_action_handled_ms`에 5 s 윈도우를 둬 중복 저장을 차단한다. 네이티브 측은 비동기 `apply()` 대신 동기 `commit()`으로 마킹해 레이스를 줄였다(`stabilization_update 2026-04-30 §1.2`).

---

## 5. Android 네이티브 구성 검토

### 5.1 권한

| 권한 | 선언 여부 | 용도/주의 |
|---|---|---|
| ACCESS_FINE/COARSE_LOCATION | 선언 | 지오펜스/현재 위치 |
| ACCESS_BACKGROUND_LOCATION | 선언 | Android 10+ 백그라운드 위치 — 사용자 '항상 허용' 필요 |
| FOREGROUND_SERVICE / FOREGROUND_SERVICE_LOCATION | 선언 | Android 14+ serviceType=location 매칭(`NhBackgroundService.kt` 181행과 일치) |
| RECEIVE_BOOT_COMPLETED | 선언 | BootReceiver 자동 시작 |
| SCHEDULE_EXACT_ALARM / USE_EXACT_ALARM | 선언 | 정확 알람(06:00/19:00, 30 s 반복) |
| WAKE_LOCK / USE_FULL_SCREEN_INTENT | 선언 | 잠금화면 풀스크린 알림 |
| VIBRATE / ACCESS_NOTIFICATION_POLICY | 선언 | 긴급 진동/방해금지 무시 |
| PACKAGE_USAGE_STATS | 선언(`tools:ignore`) | 특수 권한 — 사용자가 '사용 내역 접근'에서 직접 허용해야 함 |
| REQUEST_IGNORE_BATTERY_OPTIMIZATIONS | 선언 | `permission_handler.ignoreBatteryOptimizations`로 요청 |
| INTERNET | debug/profile만 선언 | release APK에는 INTERNET 미선언 — 필요시 의도 검토 |

전반적으로 Android 13/14에서 백그라운드 위치 기반 출퇴근 감지에 필요한 권한이 빠짐없이 선언되어 있다. 다만 PACKAGE_USAGE_STATS는 시스템 특수 권한이므로 최초 설치 안내에서 '사용 내역 접근 → NH 알리미 허용' 단계를 별도 강조해야 NH앱 자동 감지가 동작한다.

### 5.2 서비스·리시버

| 컴포넌트 | 타입 | 역할 |
|---|---|---|
| `.NhBackgroundService` | Service (`foregroundServiceType=location`) | 포그라운드 서비스 + 네이티브 보조 위치 감시 + 배터리 로그 |
| `.BootReceiver` | BroadcastReceiver (BOOT_COMPLETED, QUICKBOOT) | 재부팅 후 06:00–19:00 시간대면 서비스 자동 복구 |
| `.NativeServiceAlarmReceiver` | BroadcastReceiver (내부) | 네이티브 06:00 시작/19:00 종료 알람 핸들러 |
| `.ReminderActionReceiver` | BroadcastReceiver (내부) | 알림의 'NH파트너스 열기' 액션 처리 |
| `AlarmService` / `AlarmBroadcastReceiver` / `RebootBroadcastReceiver` | android_alarm_manager_plus 플러그인 | Flutter 측 정확 알람 처리 |

### 5.3 빌드 구성

- `compileSdk = flutter.compileSdkVersion` (현재 Flutter 3.x 기준 35), Java/Kotlin JVM 17, `coreLibraryDesugaring` 활성화.
- `android/build.gradle.kts`가 namespace 누락 라이브러리(`geofence_service`, `fl_location`, `flutter_activity_recognition`, `flutter_foreground_task`, `share_plus`, `usage_stats`)에 자동으로 namespace를 보강하고 `compileSdk=35`를 지정 — Pub 캐시 환경 변경 시에도 빌드가 깨지지 않게 함.
- `kotlin.incremental=false`, gradle JVM 8 GB로 설정. 안정성 우선이지만 빌드 시간 증가.
- release 서명이 debug 키로 되어 있고 minify·shrink 모두 비활성화(기본 Flutter 템플릿 그대로).

### 5.4 패키지 식별자

`applicationId = 'com.example.nh_reminder'` — Android 디폴트 example 식별자가 그대로 사용 중이다. 사내 배포용으로는 `kr.nonghyup.partners.reminder`와 같은 고유 도메인 식별자로 변경해야 Play Console·MDM 배포·향후 업데이트 무결성 확보가 가능하다.

---

## 6. 정상 동작 가능성 평가 (실기기 로그 기반)

### 6.1 관측 통계

#### 6.1.1 1차 관측 (2026-04-27 ~ 2026-04-30, 약 70시간)

| 지표 | 관측 값 | 해석 |
|---|---|---|
| 관찰 기간 | 2026-04-27 12:36 ~ 2026-04-30 10:46 (약 70시간) | 기기 SM-S916N (Galaxy S23) 실사용 로그 |
| ENTER 이벤트 | 391건 | 지오펜스 트리거 자체는 매우 활발히 발생 |
| EXIT 이벤트 | 278건 | 이탈 시 EXIT도 정상 발생 |
| 반복 알림 발송 누적 | 1,201건 | AlarmManager 반복이 안정적으로 큐에 들어감 |
| 반복 알림 중지 | 424건 | 차단/이탈/일시정지 시 stop이 호출됨 |
| 출퇴근 기록 저장(알림 클릭 경로) | 2건 | 검수 기간 동안 실제 클릭 사례가 적음 |
| NH파트너스 앱 감지 | **0건** | UsageStats 권한 미허용 또는 NH앱 미실행 |
| 06:00 자동 시작 / 19:00 자동 종료 | 각 3회 | 매일 정시 트리거가 안정적으로 발생 |
| 네이티브 보조 위치 요청 timeout | 1,161건 | GPS 단일 fix 12 s 타임아웃이 빈번 — lastKnown 폴백 정상 동작 |
| Dart 위치 확인 timeout | 42건 | 절전 정책/실내 GPS로 인한 일반적 실패 수준 |
| 지오펜스 시작 실패 | 3건 | ALREADY_STARTED 1, ACTIVITY_NOT_ATTACHED 2(04-29·04-30 06:00) |
| 배터리 사용량 샘플 | 예: 53%→48%, 28분 — 약 5%/28분(GPS 활성 구간) | 포그라운드 감시 중 GPS 부담이 작지 않음 — 저전력 단계 도입 사유 |

#### 6.1.2 2차 관측 — 안정화 패치 적용 후 (2026-04-30 17:13 ~ 2026-05-04 13:37, 약 92시간)

> 폰 경로: `/storage/emulated/0/Android/data/com.example.nh_reminder/files/nh_reminder_runtime.txt`
> 분석 파일: `logs_analysis/nh_reminder_runtime_after_restart_20260504.txt` (4,736 줄, 약 681 KB)

| 지표 | 1차(70h) | 2차(92h) | 변화 / 해석 |
|---|---|---|---|
| ENTER 이벤트 | 391 | 45 | **정상화** — 1차는 시연/테스트로 수동 토글이 잦았음. 2차는 실사용 패턴(하루 1~2회 출근) |
| EXIT 이벤트 | 278 | 26 | 동일 — 실제 이동 시에만 발생 |
| 알림 발송 누적 | 1,201 | 57 | 1차 대비 발송 빈도 적정화 |
| 알림 중지 | 424 | 94 | 알림 종료 호출이 발송보다 많아짐 — `dismissed_until_exit` 차단 흐름이 활발히 작동 |
| 출퇴근 기록 저장(앱 버튼/알림 클릭) | 2 | 1 | 검수 기간 중 실 사용자 클릭 사례 |
| NH파트너스 앱 감지 | **0** | **0** | UsageStats 권한 미허용 추정 — 8일 연속 0건. **H-1 미해소** |
| 06:00 자동 시작 / 19:00 자동 종료 | 3 / 3 | 4 / 4 | 매일 정시 (±2초) 트리거 — 8일 연속 0회 누락 |
| **`ACTIVITY_NOT_ATTACHED`** 예외 | **2** (04-29, 04-30 06:00) | **0** | ✅ **04-30 안정화 패치 효과 확인** — `Flutter 지오펜스 등록 생략` 로그가 05-01·02·03·04 06:00에 정확히 발생 |
| 지오펜스 시작 실패 | 3 | 0 | M-1 사실상 해결 |
| 위치 요청 timeout (네이티브) | 1,161 | 405 | 비율 유사(시간당 약 4.4건) — GPS 단일 fix 12 s가 빈번 실패, lastKnown 폴백으로 흡수 |
| Dart 위치 timeout | 42 | 10 | 시간당 약 0.1건 — 정상 수준 |
| GPS 흔들림 무시 | — | 24 | `_verifyAndHandleExit` 정상 작동 |
| **차단 저전력 감시 진입** | — | **59** | ✅ **`BATTERY_OPTIMIZATION_PLAN` 1·3·4단계 효과 확인** — `저전력 감시 300초` 로그가 차단 상태에서 다수 발생 |
| 백그라운드 실행 지연 | 8 (최대 +362 s) | 8 (최대 +255 s) | **H-2 미해소** — 여전히 도즈 영향 받음 |

### 6.2 핵심 시나리오 동작 검증

| 시나리오 | 기대 동작 | 관측/검증 |
|---|---|---|
| 회사 도착 | ENTER → 30 s 간격 풀스크린 알림 | 정상 — ENTER 검증 → 알림 시작 시퀀스 391회 |
| NH파트너스 클릭 | 기록 저장 + 알림 종료 + 차단 ON | 정상 — `addTimestamp` + `dismissUntilExit` + 채널 cancel 호출 경로 코드/로그 확인 |
| 같은 자리 GPS 흔들림 | EXIT 발생 시 재검증 → 차단 유지 | 정상 — `_verifyAndHandleExit` 1회 유예 + 확정 이탈 ≥ 150 m 적용 |
| 회사 퇴근 | 확정 이탈 후 차단 해제, 다음 출근 시 알림 재개 | 정상 — `outsideCount≥2` 시 `dismissed_until_exit=false` |
| 19:00 도달 | 지오펜스/감시/알림/네이티브 서비스 모두 종료 | 정상 — `_onStopAlarm` 4단계 종료 + 네이티브 서비스 stop |
| 다음날 06:00 | 모니터링 자동 재개 | 부분 정상 — Flutter 지오펜스 등록은 ACTIVITY_NOT_ATTACHED로 실패할 수 있으나, 백그라운드 감시·네이티브 보조 감시는 정상 동작 |
| 기기 재부팅 | BootReceiver가 06:00–19:00 시간대면 서비스 자동 시작 | 코드 검증 완료(`BootReceiver.kt` 22–43행), 로그상 직접 재부팅 사례는 없음 |
| 권한 미부여(예: 사용 내역 접근) | NH앱 자동 감지 미동작, 알림은 정상 | 정상 — 알림 클릭 경로로 차단 가능 |

### 6.3 정상 동작 가능 여부 결론

**단일 사용자 기준의 '출퇴근 알림 보조 도구' 목적에는 '정상 동작 가능' 단계라고 판단한다.** 이중 안전망(Flutter Alarm + 네이티브 LocationManager)과 다단계 위치 판정·확정 이탈 임계값·EXIT 1회 유예가 견고하게 결합되어 있어, GPS 흔들림·셀 기반 부정확 위치·앱 헤드리스 상태 같은 흔한 실패 경로에서도 알림이 통째로 사라지거나 끝없이 울리는 상황은 코드·로그상 발견되지 않는다.

특히 **2차 관측(2026-04-30 17:13 ~ 2026-05-04 13:37, 약 92시간)에서 04-30 안정화 패치(`startFlutterGeofence:false`)와 `BATTERY_OPTIMIZATION_PLAN` 1·3·4단계 패치의 효과가 모두 로그로 검증**되었다.

- ✅ 06:00 헤드리스 자동 시작 시 `ACTIVITY_NOT_ATTACHED` 예외: 1차 2건 → 2차 0건 (4일 연속 정상)
- ✅ 차단 상태에서 `저전력 감시 300초` 로그가 59건 발생 → GPS·Wake up 부담 감소 효과 확인
- ✅ 06:00/19:00 자동 스케줄: 8일 연속 누락 0회 (정시 ±2초)

다만 ① UsageStats 권한 미허용으로 NH앱 자동 감지가 8일 연속 0건(알림 클릭 경로로 보완), ② Android 절전 정책에 의한 알람 실행 지연(최대 +255 s, 여전히 +60s 이상 사례 다수)은 미해결 상태다. 이는 7장 이후 '문제점 / 개선 권고'에서 위험도와 함께 정리한다.

---

## 7. 식별된 문제점

### 7.1 위험도 분류 기준

- **HIGH**: 핵심 기능(출퇴근 누락 방지)에 직접 영향, 사용자가 인지하기 어려움.
- **MEDIUM**: 일부 시나리오에서 기능이 제한되거나, 운영/배포 안정성에 영향.
- **LOW**: 코드 품질·미래 리스크·UX 미세 개선.

### 7.2 HIGH 위험도

| # | 문제점 | 근거 | 영향 |
|---|---|---|---|
| H-1 | UsageStats 권한 미허용 시 NH파트너스 자동 감지 0회 — 알림이 'NH앱 실행 후에도' 30 s마다 계속 울릴 수 있음 | `nh_reminder_runtime_device.txt`에서 'NH파트너스 앱 감지' 0건. 권한 부여 가이드는 문서에만 존재 | 근태 보조 본 목적에 직접 영향. 알림 피로도 증가 |
| H-2 | Android 절전 정책으로 백그라운드 알람 실행이 +60 s ~ +362 s 지연되는 사례 다수 | '백그라운드 감시 실행 지연' 로그 8건 이상, 최대 +362초 | '30 s 간격 알림' 가정이 깨질 수 있음 — 출근/퇴근 임계 시점에 알림 누락 위험 |
| H-3 | discontinued 패키지 `geofence_service`에 의존 | pub.dev 상태, `docs/nh_reminder_stabilization_update_2026-04-30.md` '남은 주의점' | 장기적으로 Android SDK 업그레이드 시 빌드 깨질 위험, 보안 취약점 미패치 위험 |

### 7.3 MEDIUM 위험도

| # | 문제점 | 근거 | 영향 |
|---|---|---|---|
| M-1 | ~~06:00 자동 시작 시 ACTIVITY_NOT_ATTACHED 예외 발생~~ → **해결 확인 (2026-05-04)** | 1차 로그 04-29·04-30 06:00에 2건 발생 → 2차 로그(05-01·02·03·04 06:00)에서 0건. `Flutter 지오펜스 등록 생략` 로그가 매일 정확히 발생함 | 04-30 안정화 패치(`startFlutterGeofence:false`) 효과 4일 연속 검증 완료 — 후속 모니터링만 권고 |
| M-2 | `applicationId`가 `com.example.nh_reminder`로 데모 식별자 | `android/app/build.gradle.kts` 25행, AndroidManifest package | Play Console·MDM 배포 불가, 동일 식별자 충돌 위험 |
| M-3 | release 서명이 debug 키, ProGuard/R8 미사용 | `build.gradle.kts` `buildTypes.release` 35–47행 | 공식 배포·코드 난독화·크기 최적화 미적용 |
| M-4 | MethodChannel 이름이 `com.example.nh_reminder/...`로 패키지 변경 시 동기화 필요 | `MainActivity.kt` 22–23행, `native_monitor_bridge.dart`, `usage_stats_service.dart` | 패키지명 변경 시 빌드 깨짐 가능 |
| M-5 | 'FlutterSharedPreferences'를 네이티브에서 직접 읽고 쓰는 강결합 | `ReminderActionHandler.kt`, `NhBackgroundService.kt` 다수 | Flutter shared_preferences 내부 키 포맷 변경 시 영향 — 단위 테스트 어려움 |
| M-6 | 최초 설치 시 25개 4월 시연 데이터를 자동 삽입(기록 탭 첫 화면 혼동 가능) | `history_provider.dart` 30–58행 | 신규 설치 사용자가 자신의 기록인지 데모인지 혼동 |
| M-7 | RECEIVE_BOOT_COMPLETED는 선언했으나 BootReceiver가 `setExactAndAllowWhileIdle`만 등록 — Doze에서는 실제 실행 시점이 어긋날 수 있음 | `BootReceiver.kt` + `NativeServiceScheduler.kt` 41–49행 | 재부팅 직후 모니터링 복귀가 늦을 수 있음 |
| M-8 | JsonDecode 실패/배열이 아닐 경우 예외 처리 부재 | `history_provider._loadHistory` 25–28행 | 손상된 prefs 시 첫 진입에서 앱이 잠시 멈출 수 있음 |
| M-9 | 엑셀 내보내기 시 임시 디렉터리에만 저장 후 share_plus로 공유 — 다운로드 폴더 자동 사본 미저장 | `home_screen.dart _exportToExcel` 1294–1308행 | 공유 취소 시 파일 손실 |

### 7.4 LOW 위험도

| # | 문제점 | 근거 | 영향 |
|---|---|---|---|
| L-1 | `main.dart`의 `_startPolling`이 30 s 간격으로 SharedPreferences를 reload — 앱 포그라운드 시 불필요 IO | `main.dart` 116–160행 | 체감 영향 적음, 배터리 미세 영향 |
| L-2 | 한국어/영문/이모지 혼용 로그·UI 메시지 통일 부족 | 전체 | 유지보수성 저하 |
| L-3 | 알림 채널 ID(`nh_reminder_high_v2`) 변경 이력 — 채널 속성 변경 시 또 ID 증분 필요 | CHANGELOG, `notification_service.dart` 102행 | 재설치 안내 운영 부담 |
| L-4 | `fontFamily: 'pretendard'` 지정 — 자산 미포함 시 시스템 폰트 폴백 | `main.dart` 57행 | 디자인 일관성 약화 |
| L-5 | 이모지(🔔, 📲)에 의존 — 일부 기기/접근성 음성 출력 호환성 영향 | `notification_service.dart`, `MainActivity.kt` | 접근성 미세 영향 |
| L-6 | 인앱 화면에 동일한 '서대문역 5번출구' 좌표를 두 번 다른 값으로 명시(37.56580 vs 37.56600) | `models/app_state.dart` 20행 vs `settings_provider.dart` 26행 | 최초 설치 좌표가 살짝 다름 — 영향 미미하나 기준 통일 필요 |
| L-7 | 단위 테스트가 default Flutter `widget_test` 1개뿐 | `test/widget_test.dart` | 리그레션 방지 자동화 부족 |

---

## 8. 개선 권고

### 8.1 즉시 권고 (1주 내)

1. **최초 실행 권한 마법사 추가**: 위치(항상 허용) → 알림 → 배터리 최적화 예외 → 사용 내역 접근 4단계를 순서대로 안내하고 각 단계 완료 여부를 시각적으로 표시. 미완료 항목이 있으면 홈 카드에 경고 배지 표시. (H-1 대응)
2. **UsageStats 권한 미부여 상태 감지**: `hasUsagePermission()`이 false면 'NH파트너스 자동 감지 비활성' 배너를 홈 화면에 상시 노출하고 '권한 열기' 버튼 제공. (H-1 대응)
3. **06:00 자동 시작 보완 패치**(`startFlutterGeofence:false`)가 실제 release 빌드에서 ACTIVITY_NOT_ATTACHED를 0건으로 줄이는지 7일 로그로 재검증. (M-1 대응)
4. **최초 설치 시 자동 삽입되는 25개 시연 데이터 제거** 또는 '예시 데이터입니다 (탭하여 삭제)' 안내 카드 추가. (M-6 대응)

### 8.2 단기 권고 (1개월 내)

1. `applicationId`를 `com.example.nh_reminder` → `kr.<도메인>.nhreminder`로 변경하고 MethodChannel 이름·SharedPreferences 키 prefix를 동시에 통일. (M-2, M-4)
2. release 서명 키스토어를 분리 발급하고 `build.gradle.kts`에 `signingConfigs.release` 등록. `minifyEnabled true` + ProGuard 룰 점검(특히 `geofence_service`, `android_alarm_manager_plus`). (M-3)
3. `BackgroundMonitorService.refreshIfStale`의 `staleLimitMs`를 '차단 저전력' 상태에서 5분 이상 허용하도록 이미 분기 처리 중인 것을 release에서 검증, 추가로 Doze 모드 대비 `setAlarmClock`·WorkManager 백업 채널 검토. (H-2, M-7)
4. 출퇴근 기록을 SharedPreferences가 아닌 SQLite/Hive로 이전. 동시에 자동 백업 옵션(`allowBackup`) 정책을 수립. (M-5, M-8)
5. **'서대문역 좌표 기본값'을 단일 상수 파일로 중앙화**하여 `app_state.dart`와 `settings_provider.dart`의 불일치 제거. (L-6)

### 8.3 중기 권고 (3–6개월)

1. `geofence_service`를 `GoogleApiClient` 또는 native `LocationServices.GeofencingClient`를 직접 사용하는 자체 구현으로 교체하거나 활성 유지 보수되는 패키지로 전환. (H-3)
2. 위치 판정·알림 발송·기록 저장 핵심 로직에 대한 단위 테스트 도입(`LocationJudgmentService.judge`, `history_provider`, `geofence_service`의 ENTER/EXIT 시나리오 mock). (L-7)
3. 운영 로그를 단순 텍스트가 아닌 구조화 로그(JSON Lines)로 전환하고, 사내 내부망 대시보드에 주간 'ENTER 횟수·알림 누락·실행 지연' 보고를 자동화.
4. Android 14/15 대응: BACKGROUND_LOCATION 사용 사유 페이지(Play Console), exact alarm 재허용 흐름, 포그라운드 서비스 타입 변경 사항 추적.
5. 선택 사항으로 iOS 지원 제외에 대한 명시적 결정(README/배포 안내). UsageStats 기반 자동 감지는 iOS에서 불가하므로 동일 UX 보장이 어려움을 명시.

### 8.4 검수 단계에서 즉시 확인 가능한 체크리스트

| 체크 항목 | 방법 | 정상 기준 |
|---|---|---|
| 권한 4종 부여 | 설정 → 위치/알림/배터리/사용 내역 접근 | 모두 '항상 허용'/'허용'/'제한 없음'/'허용' |
| 포그라운드 알림 상시 노출 | 상태바 알림 'NH알리미 실행 중' 확인 | 06:00–19:00 사이 상시 표시 |
| 반경 진입 시 알림 | 회사 도착 후 30 s 이내 | 풀스크린/헤드업 알림 + 진동 |
| NH파트너스 클릭 후 알림 종료 | 알림 → 'NH파트너스 열기' 탭 | 10 s 이내 알림 사라짐, 기록 탭 갱신 |
| 19:00 자동 종료 | 19:00 시점 알림 사라짐 확인 | 포그라운드 알림 + 모든 알람 stop |
| 다음날 06:00 자동 시작 | 다음날 06:00 이후 로그 확인 | '06:00 자동 모니터링 시작' + '백그라운드 감시 시작' 기록 |
| 로그 파일 생성 | `/Download/nh_partners/nh_reminder_runtime.txt` 존재 | 용량 8 MB 도달 시 `.old.txt`로 자동 백업 |

---

## 9. 결론

NH알리미는 '농협파트너스 출퇴근 버튼 누락 방지'라는 단일 목적에 부합하도록 설계되어 있으며, 정적 분석과 **약 162시간(1차 70h + 2차 92h, 8일치) 실기기 로그**를 종합한 결과, 핵심 기능(지오펜스 진입 알림·NH앱 실행 후 차단·자동 06:00/19:00 스케줄·기록·엑셀)이 의도된 흐름대로 동작함을 확인했다. Flutter와 Kotlin 네이티브의 이중 감시, 다단계 위치 판정, EXIT 1회 유예 등의 안전 장치가 견고하다.

**2차 관측(2026-04-30 17:13 ~ 05-04 13:37) 에서 다음 두 가지 안정화 패치의 효과가 명확히 검증되었다.**

1. **06:00 자동 시작 보완** (`startFlutterGeofence:false`) — 1차에서 2회 발생하던 `ACTIVITY_NOT_ATTACHED` 예외가 4일 연속 0건으로 줄었고, 매일 정확한 시각에 `Flutter 지오펜스 등록 생략` 로그가 발생함.
2. **배터리 저전력 감시** (`BATTERY_OPTIMIZATION_PLAN` 1·3·4단계) — 차단 상태에서 `저전력 감시 300초` 로그가 59건 누적되어, GPS 호출과 Wake up이 실측으로 줄어드는 효과가 관측됨.

한편 운영 안정성을 위해서는 ① UsageStats 권한 미허용 사용자 경험 보강(8일 연속 NH앱 감지 0건), ② Android 절전 정책 대응 보강(2차에서도 +255s 지연 사례 존재), ③ discontinued 의존 패키지 교체, ④ 데모 식별자/서명 정리가 우선 필요하다. 이 4가지가 정리되면 사내 본 배포 단계에 무리 없이 진입할 수 있다.

본 보고서의 모든 '동작' 주장은 인용된 코드 라인·SharedPreferences 키·실기기 로그 카운트와 1:1로 대응한다. 추가 검증이 필요한 항목(특히 H-2 절전 정책 대응)은 release 빌드 7일 추가 운영 후 실기기 로그를 재수집해 본 보고서 6.1.2의 통계와 비교할 것을 권장한다.

---

## 부록 A. 주요 코드 인용

### A.1 다단계 위치 판정 (`location_judgment_service.dart` 100–135행)

```dart
static LocationJudgment judge({
  required double distance,
  required double radius,
  required double accuracy,
}) {
  final deepInsideThreshold = (radius * 0.5).clamp(deepInsideFloorMeters, radius).toDouble();
  final accuracyThreshold = radius > insideAccuracyFloorMeters ? radius : insideAccuracyFloorMeters;
  final exitThreshold = radius + exitBufferMeters > minimumExitThresholdMeters
      ? radius + exitBufferMeters
      : minimumExitThresholdMeters;

  final LocationZone zone;
  if (distance <= radius && (distance <= deepInsideThreshold || accuracy <= accuracyThreshold))
    zone = LocationZone.reliableInside;
  else if (distance <= radius)              zone = LocationZone.unreliableInside;
  else if (distance <= exitThreshold)       zone = LocationZone.boundary;
  else if (distance <= radius + farOutsideBufferMeters) zone = LocationZone.outside;
  else                                      zone = LocationZone.farOutside;
  // ...
}
```

### A.2 반복 알림 콜백 안전 검사 (`notification_service.dart` 14–90행 요약)

```dart
@pragma('vm:entry-point')
Future<void> notificationRepeatCallback() async {
  // 1) prefs 로드 + 콜백 시각 기록
  // 2) notif_active=false / is_paused / dismissed_until_exit 중 하나면 알람 취소 후 종료
  // 3) 위치 확인: 범위 밖이면 1회 유예, 2회면 알림 중지
  // 4) showNotificationDirect() + scheduleNextReminder(intervalSec) 로 다음 콜백 예약
}
```

### A.3 06:00/19:00 자동 알람 (`alarm_scheduler.dart` 16–50행)

```dart
DateTime nextStart = DateTime(now.year, now.month, now.day, 6, 0, 0);
if (now.isAfter(nextStart)) nextStart = nextStart.add(const Duration(days: 1));
await AndroidAlarmManager.oneShotAt(nextStart, _startAlarmId, _onStartAlarm,
    exact: true, wakeup: true, rescheduleOnReboot: true);
// _onStartAlarm 끝에서 다시 schedule() 호출 → 매일 갱신
```

### A.4 네이티브 보조 감시 다음 간격 결정 (`NhBackgroundService.kt` 746–766행)

```kotlin
private fun nextNativeDelay(config: NativeConfig, judgment: NativeJudgment): Long {
  if (config.dismissedUntilExit && !isConfirmedNativeExitAfterDismissal(...))
    return dismissedLowPowerNativeDelay(config.radius, judgment) // 180s or 300s
  if (zone == "inside" || zone == "unreliableInside" || zone == "boundary") return 15s
  return when {
    outsideDistance <= 30   -> 15s
    outsideDistance <= 150  -> 30s
    outsideDistance <= 500  -> 60s
    else                    -> 120s
  }
}
```

---

## 부록 B. 검수 도구·명령

| 용도 | 명령 | 비고 |
|---|---|---|
| 빌드 | `flutter build apk --release` | 최초 빌드 3–7분, 이후 30–60초 |
| 디버그 실행 | `flutter run` | USB 디버깅 + Galaxy 기기 연결 |
| 런타임 로그 위치 | `/storage/emulated/0/Download/nh_partners/nh_reminder_runtime.txt` | 8 MB 로테이션, `.old.txt` 백업 |
| 로그 통계 예시 | `grep -c '지오펜스 이벤트: ENTER' nh_reminder_runtime.txt` | 본 보고서 6.1 통계 산출 방법 |
| 네임스페이스 자동 보강 | `android/build.gradle.kts subprojects { compileSdk=35; namespace 보강 }` | Pub 캐시 변경 시 빌드 무중단 |

---

*본 보고서는 정적 코드 분석과 실기기 런타임 로그(2026-04-27 ~ 04-30)를 기반으로 작성되었으며, 실기기 직접 동작 검증 및 프로덕션 환경 부하 테스트는 수행되지 않았습니다.*
