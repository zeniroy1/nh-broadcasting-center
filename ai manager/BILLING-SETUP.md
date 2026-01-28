# ⚠️ 결제 계정 설정 필요

Cloud Run 배포를 위해서는 Google Cloud 프로젝트에 **결제 계정(Billing Account)**을 연결해야 합니다.

## 🔥 빠른 해결 방법

### 1. Google Cloud Console에서 결제 계정 설정

1. **Google Cloud Console 열기**
   - 브라우저에서 <https://console.cloud.google.com> 접속

2. **프로젝트 선택**
   - 상단에서 프로젝트 `gen-lang-client-0539239198` 선택

3. **결제 설정**
   - 왼쪽 메뉴에서 **"결제"** (Billing) 클릭
   - 또는 직접 링크: <https://console.cloud.google.com/billing>

4. **결제 계정 연결**
   - "결제 계정 연결" 버튼 클릭
   - 기존 결제 계정이 있다면 선택
   - 없다면 "결제 계정 생성" 클릭하여 새로 생성

5. **신용카드 정보 입력**
   - 무료 체험판(Free Tier)을 사용하더라도 신용카드 정보가 필요합니다
   - Google Cloud는 새 사용자에게 $300 크레딧을 제공합니다 (90일간)

### 2. 결제 계정 생성 시 참고사항

✅ **무료 할당량**

- Cloud Run: 월 2백만 요청까지 무료
- Cloud Build: 월 120분 빌드 시간 무료
- Artifact Registry: 월 0.5GB 저장 용량 무료

✅ **신규 사용자 혜택**

- $300 무료 크레딧 (90일간)
- 무료 할당량 초과분만 과금

⚠️ **주의사항**

- 무료 할당량을 초과하면 과금이 시작됩니다
- 트래픽이 많지 않다면 대부분 무료 범위 내에서 사용 가능

## 📋 결제 설정 완료 후 할 일

결제 계정 설정이 완료되면 다음 명령어를 실행하세요:

\`\`\`powershell
cd "C:\\Users\\hamcoding\\Desktop\\codding\\ai manager"

# API 활성화 재시도

gcloud services enable cloudbuild.googleapis.com run.googleapis.com artifactregistry.googleapis.com

# 배포 진행 (YOUR_API_KEY를 실제 Gemini API 키로 교체)

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
\`\`\`

## 🔗 직접 링크

- **결제 설정 페이지**: <https://console.cloud.google.com/billing>
- **프로젝트 대시보드**: <https://console.cloud.google.com/home/dashboard?project=gen-lang-client-0539239198>
- **Cloud Run 콘솔**: <https://console.cloud.google.com/run?project=gen-lang-client-0539239198>

---

**💡 팁**: 결제 계정 설정은 1-2분이면 완료됩니다. 설정 완료 후 알려주시면 바로 배포를 진행하겠습니다!
