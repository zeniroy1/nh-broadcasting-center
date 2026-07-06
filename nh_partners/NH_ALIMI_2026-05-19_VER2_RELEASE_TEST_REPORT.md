# NH알리미 2026-05-19 Ver2 배포 테스트 기록

## 1. 버전 분기

- Ver1: `NH_Alimi_V2.5.apk`
  - 배터리 개선을 반영해 처음 사용자 배포한 기준 APK.
- Ver2: 2026-05-19 생성 배포용 APK
  - Ver1 이후 실기 테스트와 사용자 로그 분석을 반영한 후속 배포 후보.
  - 생성 경로: `D:\codding\nh_partners\nh_reminder_v2_source_candidate_20260511\build\app\outputs\flutter-apk\app-release.apk`
  - 빌드 결과: `flutter build apk --release` 성공, APK 크기 약 51.6MB.
  - 배포용 APK에서는 개발자 로그 버튼이 노출되지 않고 사용자 핵심 로그만 다운로드 가능.

## 2. 오늘 적용된 핵심 수정

### 2.1 알림과 위치 감시 분리 강화

- 반복 알림은 사용자가 NH파트너스 확인을 완료할 때까지 30초 간격 유지.
- 알림 활성 상태 또는 출퇴근 확인 차단 상태에서는 위치/GPS 재확인을 300초로 완화.
- 로그 기준:
  - `위치감시 절전 — 알림은 30초 반복 유지, GPS 재확인만 300초로 완화`
  - `다음 백그라운드 감시 예약 → 300초 후`

### 2.2 앱 실행 상태 로그 추가

앱 상태를 다음 3단계로 구분해 로그에 남기도록 정리했다.

- `foreground`: 앱 화면이 실제로 보이는 상태.
- `background_recent`: 앱 화면은 보이지 않지만 최근 앱 또는 Flutter Activity가 살아 있는 상태.
- `service_only`: 앱 Activity가 종료되고 서비스만 남은 상태.

확인된 실제 로그:

```text
[NH알리미] 앱 실행상태 스냅샷 — mode:foreground ...
[NH알리미] 앱 실행상태 스냅샷 — mode:background_recent ...
[NH알리미] 앱 실행상태 스냅샷 — mode:service_only, source:activity, lifecycle:paused, activityVisible:false, activityAlive:false, serviceActive:true ...
```

### 2.3 사용자 핵심 로그와 개발자 로그 정리

- 사용자 핵심 로그는 1개 파일로 다운로드되도록 정리.
- 개발자 로그도 1개 파일로 다운로드되도록 정리.
- 배포용 release APK에서는 개발자 로그 버튼 숨김.
- `service_only` 상태는 사용자 핵심 로그에도 기록되는 것을 확인했다.

사용자 핵심 로그 확인 예:

```text
[NH알리미] 앱 실행상태 스냅샷 — mode:service_only, source:activity, lifecycle:paused, activityVisible:false, activityAlive:false, serviceActive:true ...
```

## 3. 오늘 실기 테스트에서 확인한 내용

### 3.1 상태 전환 기록

앱을 내리고 다시 올리는 과정에서 다음 흐름이 확인됐다.

```text
background_recent, state:inactive
background_recent, state:hidden
background_recent, state:paused
service_only, source:activity, reason:activity_destroy
```

즉 앱 화면이 완전히 떨어지는 조건에서는 `service_only`가 정상 기록된다.

### 3.2 알림 반복 동작

알림 활성 상태에서 30초 반복 알림은 유지된다.

```text
팝업 알림 발송 완료 — 기존 알림 취소 후 재표시
반복 알림 발송 (alarm callback)
다음 반복 알림 예약 → 30초 후
```

### 3.3 위치 감시 절전 동작

알림 활성 상태 또는 출퇴근 확인 차단 상태에서는 위치 감시가 완화된다.

```text
백그라운드 감시 — 범위 안 보류 ..., 출퇴근 확인 차단 저전력 감시 300초
다음 백그라운드 감시 예약 → 300초 후
네이티브 보조 감시 ..., 다음:300초
```

## 4. 배터리 사용량 관찰

2026-05-19 약 15:00 기준 배터리 화면에서 확인한 값:

- 총 사용시간: 7시간 22분
- 실제 실행: 15분
- 백그라운드: 7시간 7분
- Wake up: 324회
- Wake lock: 16분
- CPU: 13분
- GPS: 2시간 27분
- 모바일 데이터/Wi-Fi 패킷: 0개

판단:

- Wake lock 16분, CPU 13분은 테스트 상황 기준으로 큰 문제는 없어 보인다.
- Wake up 324회는 30초 반복 알림과 실기 테스트가 섞인 상황이라 관찰 대상이다.
- GPS 2시간 27분은 높은 편이다. 오늘은 반복 테스트, 앱 상태 전환, 지오펜스 경계 테스트가 많았으므로 Ver2 APK로 일반 사용 흐름에서 다시 확인이 필요하다.

## 5. 현재 Ver2 APK 테스트 기준

오늘은 추가 패치 없이 현재 생성된 Ver2 배포용 APK로 실사용 테스트를 진행한다.

확인할 항목:

- 출근/퇴근 지오펜스 진입 시 첫 알림이 정상 발생하는지.
- 사용자가 NH파트너스 확인 전까지 30초 반복 알림이 끊기지 않는지.
- 확인 완료 후 출퇴근 확인 차단 상태에서 새 알림이 다시 뜨지 않는지.
- 알림 활성 또는 차단 상태에서 GPS 재확인이 300초로 완화되는지.
- 사용자 핵심 로그에 `foreground`, `background_recent`, `service_only`가 기록되는지.
- 배터리 화면에서 GPS 사용 시간이 이전보다 줄어드는지.

## 6. 향후 업데이트 후보

GPS 사용량이 Ver2 실사용 테스트에서도 높게 유지되면 다음 패치를 검토한다.

### 6.1 반복 알림 콜백에서 GPS 완전 제거

30초 반복 알림 콜백은 위치 확인 없이 알림만 재표시하도록 제한한다.

목표:

```text
반복 알림 30초 유지
GPS 요청 없음
현재 위치 검증 없음
```

### 6.2 알림 활성 상태에서 지오펜스 이벤트 검증 최소화

`notifActive=true` 상태에서는 `ENTER`, `DWELL` 이벤트가 와도 새 위치 요청을 하지 않는다.

목표:

```text
notifActive=true + ENTER/DWELL
→ 위치 재검증 생략
→ 알림 이미 활성 중 처리만 수행
```

`EXIT`도 즉시 GPS를 새로 잡기보다 `lastKnown`으로 먼저 판단하고, 이탈 기준을 확실히 넘을 때만 위치 요청한다.

### 6.3 출퇴근 확인 차단 상태 저전력 강화

`dismissedUntilExit=true` 상태에서는 GPS 새 요청을 최소화하고 `lastKnown` 중심으로 판단한다.

권장 후보:

```text
dismissedUntilExit=true
→ lastKnown 우선
→ GPS 새 요청 최소화
→ 감시 주기 300초 또는 600초
```

### 6.4 service_only 상태 절전 강화

서비스만 실행 중이면 위치 재확인을 더 늦춰도 된다.

권장 후보:

```text
foreground: 60~300초
background_recent: 300초
service_only: 600초
notifActive=true: 300초 이상
dismissedUntilExit=true: 300~600초
```

### 6.5 GPS 요청 예산 제한

일정 시간 안에 GPS 새 요청이 과도하면 강제로 `lastKnown only` 모드로 전환한다.

예시:

```text
10분 내 GPS 요청 3회 초과
→ 10분간 lastKnown only
→ 로그: GPS 요청 예산 초과 — 저전력 모드
```

## 7. 다음 로그 분석 기준

사용자에게 받을 로그에서 우선 확인할 키워드:

```text
앱 실행상태 스냅샷
mode:foreground
mode:background_recent
mode:service_only
반복 알림 발송
다음 반복 알림 예약 → 30초 후
위치감시 절전
GPS 재확인:300초
다음 백그라운드 감시 예약 → 300초 후
네이티브 보조 감시
source:lastKnown
source:위치 요청
```

배터리 화면에서 함께 확인할 항목:

- Wake up 횟수
- Wake lock 시간
- CPU 시간
- GPS 시간
- 실제 실행 시간
- 백그라운드 시간

## 8. 사용자 배터리 데이터 추가 분석

2026-05-19 사용자 배터리 화면 자료를 추가 확인했다. 해당 사용자는 아직 Ver2가 아닌 기존 배포 버전 `NH_Alimi_V2.5.apk` 사용 상태로 추정된다.

확인된 배터리 화면 수치:

- 총 사용시간: 6시간 36분
- 실제 실행: 1분 미만
- 백그라운드: 6시간 35분
- Wake up: 712회
- Wake lock: 1시간 37분
- CPU: 18분
- GPS: 4시간 33분
- 모바일 데이터/Wi-Fi 패킷: 0개

해석:

- 실제 실행이 1분 미만인데 GPS가 4시간 33분으로 잡힌 것은 정상적인 가벼운 백그라운드 동작으로 보기 어렵다.
- Wake up 712회는 약 33초마다 1회 수준이며, 30초 알림 또는 30초 감시 루프와 유사한 패턴이다.
- Wake lock 1시간 37분은 전체 사용시간의 약 24.5% 수준이다.
- GPS 4시간 33분은 전체 사용시간의 약 69% 수준으로 과도하다.

가설:

```text
사용자 기기에서 앱이 service_only로 빨리 전환되지 않고 background_recent 상태로 장시간 유지
→ Flutter/Activity/지오펜스/네이티브 보조 감시가 함께 살아 있음
→ 포그라운드에 가까운 위치 감시 비용 발생
→ GPS 장시간 사용, Wake up/Wake lock 증가
```

사용자별 차이가 발생할 수 있는 조건:

- 앱을 최근앱에서 닫지 않고 홈으로만 내려 장시간 유지.
- 삼성 OS가 Activity/Flutter 엔진을 오래 유지.
- 지오펜스 경계 근처 또는 GPS 정확도 낮은 환경.
- ENTER/EXIT/DWELL 경계 흔들림 반복.
- 출퇴근 확인 차단 상태 또는 알림 활성 상태에서 기존 버전이 충분히 저전력화되지 않음.

Ver2에서 기대하는 개선:

- 알림 활성 상태에서 GPS 재확인 300초 완화.
- 출퇴근 확인 차단 상태에서 저전력 감시 적용.
- lastKnown 우선 사용 증가.
- background_recent/service_only 상태를 사용자 핵심 로그에서 확인 가능.
- 네이티브 보조 감시도 알림 활성 상태에서 300초 완화.

내일 사용자 로그 확인 포인트:

```text
mode:background_recent 이 장시간 유지되는지
mode:service_only 로 전환되는지
notifActive:true 상태에서 GPS 재확인:300초 로그가 찍히는지
dismissedUntilExit:true 상태에서 출퇴근 확인 차단 저전력 로그가 찍히는지
위치요청 대비 lastKnown 비율이 증가하는지
반복 알림은 30초 유지되지만 위치요청은 증가하지 않는지
```

만약 Ver2에서도 background_recent 상태에서 GPS 사용량이 과도하게 유지되면 다음 업데이트는 `background_recent 장기 유지`를 service_only에 준하는 저전력 상태로 취급하는 방향으로 진행한다.

## 9. 오늘 결론

Ver2 APK는 빌드와 기본 동작 확인이 완료됐다. 오늘은 추가 최적화 패치를 바로 넣지 않고, 현재 APK로 실사용 테스트를 진행한다. 핵심 관찰 대상은 GPS 사용 시간이 실제 사용자 환경에서 줄어드는지 여부다. 만약 GPS 시간이 여전히 높으면, 다음 업데이트는 반복 알림 콜백의 GPS 제거, 알림 활성 상태의 지오펜스 검증 최소화, `service_only` 600초 절전, GPS 요청 예산 제한을 중심으로 진행한다.
