# OpenClaw 트러블슈팅 & 설정 가이드

> 작성일: 2026-04-27  
> 서버: `setec_sever` (Synology NAS)  
> 게이트웨이 URL: `https://setec2.synology.me:18443`

---

## 📌 시스템 구성

| 항목 | 내용 |
|------|------|
| 컨테이너 이름 | `openclaw-gateway` |
| 이미지 | `ghcr.io/openclaw/openclaw:latest` |
| 포트 | `18789`, `18790` |
| 설정 파일 경로 | `/volume2/ssd/docker/openclaw/config/openclaw.json` |
| compose 파일 경로 | `/volume2/ssd/docker/openclaw/compose.yaml` |
| 컨테이너 내부 경로 | `/home/node/.openclaw/openclaw.json` |

---

## ⚠️ 발생한 문제

### 문제 1 — Gateway 502 에러
```
Gateway error: Expected HTTP 101 response but was '502 Bad Gateway'
```
- **원인**: `openclaw-gateway` 컨테이너가 설정 오류로 인해 크래시/종료된 상태

### 문제 2 — Config Invalid (bindings 오류)
```
bindings.0: Invalid input (allowed: "route", "acp")
```
- **원인**: 2번 에이전트를 텔레그램에 바인딩하는 과정에서 잘못된 필드명 사용

#### 시도했던 잘못된 형식들
```json
// ❌ 잘못된 형식 1
{ "type": "route", "channel": "telegram/advisor", "agent": "2" }

// ❌ 잘못된 형식 2
{ "type": "route", "channel": "telegram/advisor", "agentId": "2" }

// ❌ 잘못된 형식 3
{ "type": "route", "channel": "telegram/advisor", "agents": ["2"] }
```

#### 올바른 형식 (WebUI 자동 저장 결과)
```json
// ✅ 올바른 형식
{
  "type": "route",
  "agentId": "2",
  "match": {
    "channel": "telegram",
    "accountId": "advisor"
  }
}
```

> **핵심**: `channel`을 슬래시(/)로 합치는 게 아니라 `match` 객체로 분리해야 함

---

## 🔧 해결 과정

### Step 1 — 컨테이너 상태 확인
```bash
docker ps -a
# → openclaw-gateway 가 Exited 상태 확인
```

### Step 2 — 설정 파일 실제 경로 찾기
```bash
# compose.yaml 확인으로 실제 볼륨 경로 파악
# 잘못 알았던 경로: /volume1/@docker/volumes/openclaw_openclaw_config/_data/
# 실제 경로: /volume2/ssd/docker/openclaw/config/
```

### Step 3 — 설정 파일 수정 (bindings 제거)
```bash
cat > /volume2/ssd/docker/openclaw/config/openclaw.json << 'EOF'
{ ... "bindings": [] ... }
EOF
```

### Step 4 — 파일 권한 수정 및 컨테이너 재시작
```bash
chown 1000:1000 /volume2/ssd/docker/openclaw/config/openclaw.json
docker restart openclaw-gateway
```

### Step 5 — 텔레그램 페어링
```bash
# 컨테이너 내부에서 페어링 승인
docker exec -it openclaw-gateway node dist/index.js pairing approve telegram [코드]
```

### Step 6 — WebUI에서 바인딩 설정
- `https://setec2.synology.me:18443` 접속
- Settings → Bindings 에서 advisor 봇 → 2번 에이전트 연결
- 자동으로 올바른 형식으로 저장됨

---

## ✅ 최종 상태

| 항목 | 상태 |
|------|------|
| 게이트웨이 | ✅ 정상 실행 |
| `@hyeunsic_bot` (default) | ✅ 1번 에이전트(main) 연결 |
| `@hyeunsic_2_bot` (advisor) | ✅ 2번 에이전트 연결 |
| 페어링 | ✅ 완료 (sender: 8797397490) |

---

## 📋 현재 openclaw.json 바인딩 설정

```json
"bindings": [
  {
    "type": "route",
    "agentId": "2",
    "match": {
      "channel": "telegram",
      "accountId": "advisor"
    }
  }
]
```

---

## 📌 에이전트 추가 시 수정 가이드

> **권장**: 가능하면 WebUI에서 설정 (자동으로 올바른 형식 저장)  
> **수동 편집 시**: 아래 순서 반드시 준수

### 1. 텔레그램 봇 추가
`channels.telegram.accounts`에 추가:
```json
"agent3": { "botToken": "새봇토큰" }
```

### 2. 에이전트 추가
`agents.list`에 추가:
```json
{
  "id": "3",
  "name": "3번",
  "workspace": "/home/node/.openclaw/agents/3번",
  "agentDir": "/home/node/.openclaw/agents/3/agent",
  "model": "openai/gpt-4o-mini"
}
```

### 3. 바인딩 추가
`bindings`에 추가:
```json
{
  "type": "route",
  "agentId": "3",
  "match": {
    "channel": "telegram",
    "accountId": "agent3"
  }
}
```

### 4. 파일 저장 후 필수 작업
```bash
chown 1000:1000 /volume2/ssd/docker/openclaw/config/openclaw.json
docker restart openclaw-gateway
sleep 15 && docker logs --since 10s openclaw-gateway
```

---

## 🔑 주요 명령어 모음

```bash
# 컨테이너 상태 확인
docker ps | grep openclaw

# 로그 확인
docker logs --tail 30 openclaw-gateway

# 새 로그만 확인
docker logs --since 10s openclaw-gateway

# 컨테이너 재시작
docker restart openclaw-gateway

# 설정 파일 확인
cat /volume2/ssd/docker/openclaw/config/openclaw.json

# 바인딩 확인
cat /volume2/ssd/docker/openclaw/config/openclaw.json | grep -A 10 '"bindings"'

# 파일 권한 수정
chown 1000:1000 /volume2/ssd/docker/openclaw/config/openclaw.json

# 컨테이너 내부 접속
docker exec -it openclaw-gateway /bin/sh

# 페어링 승인
docker exec -it openclaw-gateway node dist/index.js pairing approve telegram [코드]
```

---

## ⚠️ 트러블슈팅 시 주의사항

1. **설정 파일 경로 혼동 주의**
   - ❌ `/volume1/@docker/volumes/openclaw_openclaw_config/_data/` (Docker 내부 볼륨, 사용 X)
   - ✅ `/volume2/ssd/docker/openclaw/config/` (실제 마운트 경로)

2. **docker cp 사용 금지**
   - `docker cp`로 파일 복사 시 컨테이너 overlay에 기록되어 볼륨 파일과 충돌 발생
   - 반드시 실제 경로(`/volume2/ssd/docker/openclaw/config/`)에서 직접 수정

3. **파일 수정 후 권한 설정 필수**
   - root로 파일 수정 시 컨테이너(uid 1000)가 읽기 불가
   - 항상 `chown 1000:1000` 실행 후 재시작
