---
name: team-status
description: 프로젝트 전체 현황 파악 및 다음 작업 추천
user-invocable: true
---

# /team-status — 프로젝트 현황 리포트

사용자가 `/team-status` 를 실행하면 아래 단계를 수행합니다.

## 실행 단계

### 1단계: 데이터 수집 (병렬)

다음 명령을 **병렬**로 실행합니다:

1. `Bash "git log --oneline -10"` → 최근 변경 이력
2. `Bash "cd /home/user/job_change/server && python tests/test_all.py 2>&1 | tail -5"` → 테스트 현황
3. `Glob "server/seed/benefit/*.sql"` → 복지 데이터 커버리지
4. `Grep "TODO|FIXME|HACK" --glob "*.py" --glob "*.html"` → 미해결 항목

### 2단계: 영역별 현황 분석

각 영역의 완성도를 판단합니다:

| 영역 | 판단 기준 |
|------|----------|
| FE | `index.html` 내 빈 함수, placeholder, TODO 주석 수 |
| BE | `server/routers/` 엔드포인트 수 vs 모델 커버리지 |
| 데이터 | `.sql` 파일 수 / KNOWN_IDS 전체 수 |
| 테스트 | 통과 수 / 전체 수, 미커버 영역 |
| 인프라 | `infra/*.tf` 존재 여부, `server/deploy/` 완성도 |

### 3단계: 리포트 출력

```
## 프로젝트 현황 (YYYY-MM-DD)

### 최근 활동
- {해시} {메시지} ({날짜})
- {해시} {메시지} ({날짜})
- ...

### 영역별 상태
| 영역 | 상태 | 핵심 지표 |
|------|------|----------|
| FE (index.html) | 🟡 90% | renderOTCalc() 미구현 |
| BE (FastAPI) | 🟢 95% | 23 엔드포인트 가동 |
| 데이터 | 🔴 N% | N/200 회사 복지 파싱 |
| 테스트 | 🟡 N% | N/M 통과 |
| 인프라 | 🟡 85% | Terraform 정의됨, CI/CD 없음 |

### 미해결 항목
- TODO: {내용} ({파일}:{행})
- ...

### 추천 다음 작업 (우선순위)
1. `/batch-benefits` — 데이터 커버리지 확대 (현재 N/200)
2. `/test {영역}` — 테스트 커버리지 확대
3. `/fe {작업}` 또는 `/be {작업}` — 기능 완성
```

---

## 상태 아이콘 기준

| 아이콘 | 의미 | 기준 |
|--------|------|------|
| 🟢 | 양호 | 90%+ 완성, 블로커 없음 |
| 🟡 | 진행중 | 50-89%, 개선 필요 |
| 🔴 | 주의 | 50% 미만, 핵심 갭 |
