# HAMSHARE 1단계 요구사항 및 환경 확정안

작성일: 2026-06-19  
상태: 사용자 승인 대기

## 1. 확정된 사용 환경

- 송신 기기: Samsung Galaxy S23+
- 모바일 운영체제: Android
- 수신 기기: Windows 10 64비트 PC
- Windows 빌드: 10.0.19045
- 무선 장치: TP-Link Wi-Fi 6 + Bluetooth USB 통합 어댑터
- Wi-Fi 드라이버: TP-Link Wireless USB Adapter 5001.19.113.1
- Bluetooth 드라이버: TP-Link/Realtek 1.1071.2406.1700
- 지원 무선 규격: 802.11ax, Wi-Fi Direct, Bluetooth LE
- Windows 개발환경: .NET SDK 8.0.422 설치 확인
- Android 개발환경: Android SDK 및 ADB 설치 확인
- 실기기 연결: 현재 ADB 연결 없음. Android 앱 설치 시험 시 USB 디버깅 연결 필요

## 2. 1차 버전 목표

Galaxy S23+의 5GHz 모바일 핫스팟에 Windows PC가 일반 Wi-Fi 클라이언트로 접속한 상태에서 사진·동영상·문서 파일을 로컬 네트워크로 고속 전송한다.

Google Quick Share에서 실패한 Bluetooth→Wi-Fi 자동 승격과 Windows 임시 SoftAP 생성은 사용하지 않는다.

## 3. 제안하는 기본 동작

1. 사용자가 S23+ 모바일 핫스팟을 켠다.
2. Windows PC가 저장된 S23+ 핫스팟에 접속한다.
3. Windows HAMSHARE 수신기를 실행한다.
4. Android HAMSHARE 앱에서 파일 또는 사진 여러 장을 선택한다.
5. 최초 1회 PC 화면의 PIN을 휴대폰에 입력해 등록한다.
6. 등록 후에는 지정 PC만 표시한다.
7. 사용자가 전송을 누르면 PC에서 파일을 수신한다.
8. 전송 완료 후 SHA-256으로 무결성을 확인한다.

## 4. 1차 버전 요구사항 제안

| 항목 | 제안 기본값 |
|---|---|
| 지원 장치 수 | S23+ 1대, Windows PC 1대 |
| 전송 방향 | 휴대폰 → PC 단방향 |
| 파일 선택 | 단일·다중 파일, Android 공유 메뉴 지원 |
| 목표 용량 | 1회 최소 20GB까지 |
| 파일 개수 | 1회 최소 1,000개까지 |
| 목표 속도 | 5GHz 환경 실효 10MB/s 이상, 목표 20~40MB/s |
| PC 수신 승인 | 등록된 S23+는 자동 수신 |
| 최초 등록 | PC에 표시된 6자리 일회용 PIN |
| 기본 수신 폴더 | `D:\codding\HAMSHARE\Received` |
| 중복 파일명 | 덮어쓰지 않고 `(1)`, `(2)` 자동 부여 |
| 불완전 파일 | `.partial` 확장자로 저장 후 성공 시 최종 변경 |
| 전송 재개 | 1차 MVP에서는 동일 세션 재시도, 이후 체크포인트 재개 확장 |
| 암호화 | 로컬 HTTPS/TLS 또는 페어링 키 기반 암호화 채널 |
| 무결성 | SHA-256 |
| 인터넷 사용 | 없음. 핫스팟 내부 로컬 통신만 사용 |
| 외부 서버 | 사용하지 않음 |
| 자동 시작 | 1차 버전에서는 비활성화 |
| 삭제 정책 | 수신 파일 자동 삭제 없음 |

## 5. 기술 방향

### Windows 수신기

- C# / .NET 8
- Windows 10용 WPF UI
- ASP.NET Core Kestrel 기반 로컬 수신 서버
- 스트리밍 파일 저장으로 메모리 전체 적재 방지
- 네트워크 인터페이스와 수신 IP 표시
- PIN, 수신 폴더, 전송 기록 UI

### Android 송신 앱

- Kotlin
- Jetpack Compose
- Storage Access Framework
- `ACTION_SEND`, `ACTION_SEND_MULTIPLE` 공유 메뉴 연동
- Foreground Service로 화면 꺼짐 중 전송 유지
- Coroutine 기반 스트리밍 업로드

### 장치 검색

- 1차 MVP: PC 화면에 표시된 IP 주소와 PIN으로 최초 연결
- 2차 개선: Android NSD/mDNS로 PC 자동 검색
- Bluetooth 검색은 초기 MVP에서 제외하여 드라이버 의존성과 구현 복잡도를 줄임

## 6. 검증 기준

- 100장, 약 800MB 사진 묶음을 정상 전송한다.
- 800MB 기준 목표 완료 시간은 40초~2분이다.
- 전송 전후 파일 개수, 크기, SHA-256이 일치한다.
- 기존 파일을 덮어쓰지 않는다.
- 전송 취소 시 완성 파일로 노출되지 않는다.
- 모바일 데이터 사용량이 파일 크기만큼 증가하지 않는다.
- PC와 휴대폰이 핫스팟에서 분리되면 명확한 오류를 표시한다.

## 7. 확인된 위험

- Android SDK는 설치되어 있지만 Java 실행 경로와 Gradle 환경은 프로젝트 생성 시 명시적으로 연결해야 한다.
- S23+는 아직 ADB로 연결되지 않아 APK 실기기 설치·검증은 바로 수행할 수 없다.
- Windows 방화벽은 최초 수신 서버 실행 시 네트워크 허용 확인이 필요할 수 있다.
- Google Quick Share 제거는 관리자 권한 오류 1730으로 자동 처리되지 않았으며 사용자가 Windows 앱 설정에서 직접 제거해야 한다.

## 8. 사용자 승인 항목

아래 항목을 승인하면 2~4단계의 상세 설계를 확정한 뒤 Windows 수신기와 Android 송신 앱 MVP 코딩에 착수한다.

- 기본 수신 폴더: `D:\codding\HAMSHARE\Received`
- 등록된 S23+의 자동 수신
- 중복 파일 자동 이름 변경
- 1차 버전은 휴대폰→PC 단방향
- 최초 MVP는 IP+PIN 연결, 이후 자동 검색 추가
- 목표 전송 속도 10MB/s 이상

승인 문구 예시:

> 1단계 확정안을 승인하고 HAMSHARE MVP 코딩을 시작해.

