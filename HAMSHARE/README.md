# HAMSHARE

Galaxy S23+에서 Windows 10 PC로 파일을 고속 전송하는 로컬 전용 파일 공유 시스템입니다.

## 연결 구조

1. S23+에서 5GHz 모바일 핫스팟을 켭니다.
2. Windows PC를 해당 핫스팟에 연결합니다.
3. Windows 수신기에서 IP, PIN, 인증서 코드를 확인합니다.
4. Android 앱에서 최초 등록 후 파일을 전송합니다.

파일 데이터는 외부 서버나 인터넷을 거치지 않습니다.

## 폴더

- `src/HamShare.Core`: 프로토콜, 인증, 파일 저장 핵심 로직
- `src/HamShare.Receiver`: Windows 10 WPF 수신 프로그램
- `tests/HamShare.Core.Tests`: 외부 테스트 패키지 없는 핵심 테스트 실행기
- `android`: Galaxy S23+용 Kotlin/Compose 앱
- `status`: SVG/웹 구현상황 대시보드
- `docs`: 설계 및 검증 문서

## 현재 상태

브라우저에서 `status/index.html`을 열어 확인합니다.

