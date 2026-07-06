# NH 리마인더 프로젝트 — 세션 로그 및 자료 저장
> 작성일: 2026-04-21 | 작업자: 현식

---

## 1. 프로젝트 개요

**앱 이름:** NH 리마인더 (`nh_reminder`)  
**목적:** 농협파트너스 앱(com.vus.nhpthrm)에서 출퇴근 버튼 클릭을 잊지 않도록, 지정 위치(서대문역 5번 출구 반경 30m) 진입 시 긴급 알림을 발송하는 Android 앱  
**플랫폼:** Flutter (Android 전용)  
**상태 관리:** flutter_riverpod (StateNotifier)

---

## 2. 프로젝트 폴더 구조

```
nh_reminder/
├── pubspec.yaml
├── lib/
│   ├── main.dart
│   ├── models/
│   │   └── app_state.dart
│   ├── providers/
│   │   └── settings_provider.dart
│   ├── screens/
│   │   └── home_screen.dart
│   └── services/
│       ├── geofence_service.dart
│       ├── notification_service.dart
│       └── usage_stats_service.dart
```

---

## 3. 핵심 파일 요약

### `pubspec.yaml` — 주요 의존성
| 패키지 | 용도 |
|---|---|
| flutter_riverpod | 상태 관리 |
| geofence_service | 지오펜싱 (FusedLocationProvider) |
| geolocator | 현재 위치 가져오기 |
| permission_handler | 권한 요청 |
| flutter_local_notifications | 긴급 알림 채널 |
| flutter_background_service | 백그라운드 실행 유지 |
| shared_preferences | 설정값 영구 저장 |
| usage_stats | NH앱 포그라운드 감지 |
| url_launcher | NH파트너스 앱 실행 |

---

### `models/app_state.dart` — AppSettings
```dart
AppSettings {
  isPaused: false,
  geofenceLat: 37.56580,   // 서대문역 5번 출구 기본값
  geofenceLng: 126.96640,
  geofenceRadius: 30.0,    // 반경 30m
  repeatIntervalSec: 60,   // 1분 반복 알림
}
```

---

### `services/geofence_service.dart` — NhGeofenceService
- `GeofenceService.instance.setup(interval:5000, accuracy:100)`
- ENTER 이벤트 → `NotificationService.startReminder()`
- 10초마다 `UsageStatsService.isNhAppInForeground()` 폴링
- NH앱 감지 시 → `NotificationService.stopReminder()`

---

### `services/notification_service.dart` — NotificationService
- 채널 ID: `nh_reminder_urgent` (IMPORTANCE_MAX)
- `fullScreenIntent: true` — 잠금화면 팝업
- `category: AndroidNotificationCategory.alarm` — 방해금지 무시
- 진동 패턴: `[0, 700, 200, 700, 200, 700]`
- 액션 버튼: `✅ 확인함` / `📲 NH파트너스 열기`
- 1분 간격 `Timer.periodic` 반복

---

### `services/usage_stats_service.dart` — UsageStatsService
- MethodChannel: `com.example.nh_reminder/usage_stats`
- `isNhAppInForeground()` → Android UsageStatsManager 조회
- `hasPermission()` → PACKAGE_USAGE_STATS 권한 확인
- `openPermissionSettings()` → 권한 설정 화면 이동

---

### `providers/settings_provider.dart` — SettingsNotifier
- SharedPreferences 키: `is_paused`, `geofence_lat`, `geofence_lng`, `geofence_radius`, `repeat_interval_sec`
- 메서드: `togglePause()`, `updateGeofenceLocation()`, `updateRadius()`, `updateRepeatInterval()`

---

### `screens/home_screen.dart` — HomeScreen UI
| 컴포넌트 | 설명 |
|---|---|
| 상태 카드 | 모니터링 활성/중지 표시, 반경 정보 |
| 일시정지 배너 | 일시정지 시 상단 노란 배너 표시 |
| 재개/정지 버튼 | 토글 버튼, 지오펜스 서비스 재시작/중지 |
| 위치 보정 버튼 | 현재 GPS 위치로 지오펜스 중심 재설정 |
| NH앱 바로가기 | Intent scheme으로 NH파트너스 실행 |
| 설정 바텀시트 | 반경(20~200m), 반복간격(30~300초) 슬라이더 |

---

## 4. UI 프로토타입 (HTML Artifact)

### 4-1. NH 리마인더 앱 프로토타입 (`nh-reminder-prototype`)
- **프레임:** 360px (소형폰 최적화)
- **디자인:** 다크 메탈릭, 파스텔톤 포인트 컬러
- **탭 구성:**
  - 🏠 홈: 지오펜스 상태, 펄스 애니메이션, 빠른 액션 카드
  - 📋 기록: 출퇴근 기록 히스토리 카드
  - ⚙️ 설정: 반경/반복간격 슬라이더, 권한 관리
- **인터랙션:** 메탈 shimmer + ripple 클릭 애니메이션

### 4-2. NH 알림 프로토타입 (`nh-notification-prototype`)
- **씬 1 — 잠금화면 풀스크린 팝업:**
  - 배경: 별이 있는 다크 잠금화면
  - 알림 카드 (fs-card): `✅ 확인함` / `📲 NH파트너스 열기` 버튼
  - 가로 슬라이드 dismiss: 왼쪽 스와이프 → 초록(확인), 오른쪽 스와이프 → 빨강(닫기)
  - threshold: 70px

- **씬 2 — Heads-up 배너:**
  - 앱 사용 중 상단 배너 (hu-banner) 슬라이드 다운 애니메이션
  - 버튼 탭 → 확인 완료 카드(hu-step2)로 전환
  - 두 카드 모두 가로 슬라이드 dismiss 지원
  - 재사용 함수: `makeHorizDrag(el, dlEl, drEl, onDismiss)`
  - threshold: 65px

- **씬 3 — 알림창:**
  - 알림 드로어 UI (노티피케이션 센터)
  - 왼쪽 스와이프 삭제
  - 아이콘 최소화: 좌측 3px 컬러 바(nc-bar)로 대체
  - threshold: 58px

---

## 5. CSS 핵심 패턴 (프로토타입)

### 폰 프레임 flex 레이아웃 (클리핑 방지)
```css
.phone {
  display: flex;
  flex-direction: column;
  width: 360px;
}
.tab-content.active {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}
.scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}
```

### 메탈 버튼 효과
```css
.mbtn::before { background: var(--metal); }
.mbtn::after  { shimmer sweep animation; }
/* click: ripple span 동적 생성 */
```

### 가로 슬라이드 dismiss
```css
/* translateX(dx) + rotate(dx*0.02deg) */
/* 왼쪽 = teal 배경(확인), 오른쪽 = red 배경(닫기) */
/* threshold 초과 시 → translateX(±400px) 후 요소 제거 */
```

---

## 6. 작업 이력

| # | 작업 내용 |
|---|---|
| 1 | 프로젝트 파일 분석 및 학습 |
| 2 | 앱 UI 프로토타입 초안 생성 (HTML) |
| 3 | 메탈 클릭 애니메이션 추가, 3탭 구현 |
| 4 | 빠른 액션 섹션 아이콘 클리핑 버그 수정 (flex 레이아웃 전환) |
| 5 | 알림 프로토타입 생성 (잠금화면/Heads-up/알림창 3씬) |
| 6 | 씬1 잠금화면 슬라이드 dismiss 추가 |
| 7 | 씬2 Heads-up 버튼 탭 후 확인 카드 슬라이드 dismiss 추가 |
| 8 | 씬3 아이콘 정리 (컬러 바 인디케이터 적용) |
| 9 | 폰 프레임 크기 축소: 393px → 360px (소형폰 최적화) |
| 10 | 씬1, 씬2 슬라이드 방향 변경: 세로(위) → 가로(좌우) |

---

## 7. 다음 단계 (예정)

- [ ] HTML 프로토타입 → Flutter `home_screen.dart` 코드 변환
- [ ] Android Native (Kotlin): UsageStatsManager MethodChannel 구현
- [ ] 실기기 테스트: 지오펜스 정확도 검증
- [ ] 백그라운드 서비스 연동 최종 확인
- [ ] Play Store 배포 준비

---

_저장일: 2026-04-21_
