# Google Cloud Run 배포 가이드

이 가이드는 AI 구독 관리 앱을 Google Cloud Run에 배포하는 방법을 설명합니다.

## 사전 준비

### 1. Google Cloud CLI 설치

Windows에서 다음 명령어로 설치:

```powershell
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
& $env:Temp\GoogleCloudSDKInstaller.exe
```

### 2. gcloud CLI 초기화

```powershell
gcloud init
gcloud auth login
```

### 3. 프로젝트 설정

```powershell
# 현재 프로젝트 확인
gcloud config get-value project

# 프로젝트 설정 (필요시)
gcloud config set project gen-lang-client-0539239198
```

### 4. 필요한 API 활성화

```powershell
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

## 배포 방법

### 방법 1: 자동 배포 (권장)

```powershell
cd "C:\Users\hamcoding\Desktop\codding\ai manager"

# 빌드 및 배포 (한 번에)
gcloud run deploy ai-subscription-manager `
  --source . `
  --region asia-northeast3 `
  --platform managed `
  --allow-unauthenticated `
  --memory 512Mi `
  --cpu 1 `
  --timeout 300 `
  --min-instances 0 `
  --max-instances 10 `
  --set-env-vars "GEMINI_API_KEY=YOUR_API_KEY_HERE"
```

**중요**: `YOUR_API_KEY_HERE`를 실제 Gemini API 키로 교체하세요.

### 방법 2: 수동 빌드 후 배포

```powershell
cd "C:\Users\hamcoding\Desktop\codding\ai manager"

# 1. Docker 이미지 빌드
gcloud builds submit --tag gcr.io/gen-lang-client-0539239198/ai-subscription-manager

# 2. Cloud Run에 배포
gcloud run deploy ai-subscription-manager `
  --image gcr.io/gen-lang-client-0539239198/ai-subscription-manager `
  --region asia-northeast3 `
  --platform managed `
  --allow-unauthenticated `
  --memory 512Mi `
  --cpu 1 `
  --set-env-vars "GEMINI_API_KEY=YOUR_API_KEY_HERE"
```

## 환경 변수 업데이트

배포 후 환경 변수를 업데이트하려면:

```powershell
gcloud run services update ai-subscription-manager `
  --region asia-northeast3 `
  --update-env-vars "GEMINI_API_KEY=YOUR_NEW_API_KEY"
```

## 배포 확인

배포가 완료되면 다음과 같은 URL이 제공됩니다:

```
https://ai-subscription-manager-xxxxx-an.a.run.app
```

브라우저에서 해당 URL에 접속하여 앱이 정상 작동하는지 확인하세요.

## 로컬 테스트

배포 전 로컬에서 Docker로 테스트:

```powershell
# Docker 이미지 빌드
docker build -t ai-subscription-manager .

# 로컬 실행
docker run -p 8080:8080 -e PORT=8080 -e GEMINI_API_KEY=YOUR_API_KEY ai-subscription-manager

# 브라우저에서 확인
# http://localhost:8080
```

## 트러블슈팅

### 배포 실패 시

1. **로그 확인**

   ```powershell
   gcloud run services logs read ai-subscription-manager --region asia-northeast3
   ```

2. **서비스 상태 확인**

   ```powershell
   gcloud run services describe ai-subscription-manager --region asia-northeast3
   ```

3. **빌드 로그 확인**

   ```powershell
   gcloud builds list --limit 5
   gcloud builds log [BUILD_ID]
   ```

### 일반적인 문제

- **API 키 오류**: 환경 변수가 올바르게 설정되었는지 확인
- **타임아웃**: `--timeout` 값을 늘려보세요
- **메모리 부족**: `--memory` 값을 증가시켜보세요

## 비용 관리

- **최소 인스턴스 0**: 트래픽이 없을 때 비용 절감
- **무료 할당량**: 월 2백만 요청까지 무료
- **비용 확인**: <https://console.cloud.google.com/billing>

## 유용한 명령어

```powershell
# 서비스 목록 확인
gcloud run services list

# 서비스 삭제
gcloud run services delete ai-subscription-manager --region asia-northeast3

# 트래픽 분할 (새 버전 배포 시)
gcloud run services update-traffic ai-subscription-manager --region asia-northeast3 --to-latest

# 리전 변경
# 도쿄: asia-northeast1
# 서울: asia-northeast3
# 오사카: asia-northeast2
```
