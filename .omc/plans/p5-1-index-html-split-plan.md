# P5-1 — index.html 분리 + Nginx 캐싱 설정 (RALPLAN-DR, DELIBERATE)

**Mode**: DELIBERATE consensus planning
**Date**: 2026-04-23
**Owner**: Planner → Architect → Critic
**Target file**: `/home/ubuntu/job_change/index.html` (2,730 lines)
**Deploy surface**: `/home/ubuntu/job_change/server/deploy/nginx.conf` (30 lines)

---

## 1. Principles (3–5개)

1. **Zero-regression first** — 분리 자체가 목적이 아니라, 동일한 사용자 경험과 동일한 전역 스코프 동작을 유지하는 것이 1순위. 기능/기능 회귀 0건이 통과 조건.
2. **No build step, no framework creep** — CLAUDE.md의 "Vanilla JS + No build" 원칙 유지. webpack/Vite/bundler 도입 금지. 브라우저가 바로 로드 가능한 순수 정적 파일 3개로 분리.
3. **Preserve global scope contract** — 72개 inline `onclick` 핸들러(`go()`, `openAuth()`, `submitAuth()`, `compare()` 등)가 `window` 전역에서 호출되어야 하므로, ES modules(`type="module"`) 사용 금지. 평문 `<script src>` 로드.
4. **Cache correctness over cleverness** — Cache-Control은 "변경 시 무효화 보장"을 최우선으로. 애매한 ETag 의존 대신, 파일명 해시(content hash)로 영원히 안전한 `immutable` 캐시.
5. **Reversible in one commit** — 분리 결과가 문제 시 `git revert` 1회로 원복 가능해야 함. Nginx 설정 변경도 `nginx.conf.bak` 보존.

## 2. Decision Drivers (Top 3)

1. **Regression risk** — 2,730줄 단일 파일을 3파일로 쪼개는 과정에서 CSS cascade 순서, JS 실행 순서(IIFE `handleOAuthReturn()` 즉시 실행 vs DOM 준비), inline handler 바인딩이 깨질 가능성. 모든 분리 전략은 이 리스크 대비 완화책이 있어야 함.
2. **Cache invalidation correctness** — 사용자는 배포 직후에도 항상 최신 `app.js`/`styles.css`를 받아야 하고, 이후에는 CDN/브라우저가 영구 캐시해야 함. "가끔 구버전 UI가 남는" 버그는 직장 선택 OS처럼 서서히 개선되는 서비스에 치명적.
3. **Deploy simplicity on single-host ARM** — OCI Always Free 단일 인스턴스에 CI/CD 없이 `rsync`/`git pull` + `systemctl reload nginx` 로 배포. 빌드 도구 없이 파일명 해시를 만들어야 하므로 쉘 스크립트 수준의 자동화가 현실적 한계.

**부가 제약 (Must-preserve)**: `index.html:871` 의 `const API_BASE=(location.protocol==='file:')?'':location.origin;` 분기는 **`file://` 직접 열기(오프라인 모드) 지원이 명시적 설계 요구사항**이다. 따라서 모든 정적 자산 참조는 **상대경로** 로 작성되어야 하며(절대경로 `/app.js` 금지), QA 테이블(§5.2)에 `file://` 직접 열기 케이스를 포함해야 한다.

## 3. Viable Options

### A. 분리 전략 (파일 경계)

#### Option A1 — **Straight extract (단순 추출, defer 없음, HTML-last 위치 유지)** [RECOMMENDED]
- `<style>` 블록(줄 9–676) → `styles.css` 그대로 복사
- `<script>` 블록(줄 866–2729) → `app.js` 그대로 복사
- `index.html` 은 `<link rel="stylesheet" href="styles.css?v={hash}">` + `<script src="app.js?v={hash}"></script>` 로 대체 (상대경로)
- **`defer` 속성 사용 금지** — 원본 `<script>`는 `</body>` 직전 최하단 위치로 이미 DOM 파싱 후 실행 보장(§4 Scenario 4 근거). `defer` 추가 시 `handleOAuthReturn()` IIFE 실행 타이밍이 `DOMContentLoaded` 이후로 밀려 OAuth `?token=` URL 노출창 발생. 따라서 `<script src="app.js?v=...">` 를 **원본과 동일하게 `</body>` 직전**에 유지 (바이트 단위 유사).
- 섹션 구분 주석(`// ━━ UTILS ━━`) 유지
- **Pros**: 회귀 리스크 최소, diff 명확, 5분 안에 롤백 가능, CLAUDE.md의 프론트엔드 섹션 구조 그대로 보존, OAuth IIFE 실행 순서 보존
- **Cons**: 모듈 격리/트리쉐이킹 없음 → 번들 크기 개선 0, 향후 분할 여지는 열려있음

#### Option A2 — **Sectional split (섹션별 다중 파일)**
- CSS를 `styles/base.css` + `styles/landing.css` + `styles/compare.css` + `styles/admin.css` 로 분리
- JS를 `js/api.js` + `js/state.js` + `js/compare.js` + `js/admin.js` 로 분리
- **Pros**: 장기 유지보수성, 관심사 분리
- **Cons**: HTTP 요청 증가(HTTP/2에서도 파일당 parse 비용), 의존성 순서 관리 필요, inline handler와 전역 함수 배치에 실수 여지 증가, **회귀 리스크 높음**
- **Invalidation rationale**: "Zero-regression first" 원칙과 충돌. P5-1 목표(분리 + 캐싱)에 비해 작업량 4배. 향후 필요 시 별도 P5-1b로 후속.

#### Option A3 — **Inline-preserving (부분 분리)**
- CSS만 분리, JS는 `index.html` 내부 유지
- **Pros**: JS 회귀 리스크 0
- **Cons**: JS 1,863줄(69KB)이 HTML과 같이 전송 → 캐시 효과 절반. "이직 vs 잔류" 비교 화면 반복 방문 시 불필요한 다운로드.
- **Invalidation rationale**: 목표(`app.js` 분리)를 만족하지 못함. resume-2026-04-23.md의 산출물 정의 위반.

**→ Option A1 선택.** "Straight extract" + 섹션 주석 보존.

### B. 캐시 버스팅 전략

#### Option B1 — **쿼리스트링 해시 `?v={sha1-8}`** [RECOMMENDED]
- 빌드 스크립트: `sha1sum app.js | cut -c1-8` 로 해시 산출
- `index.html` 내 `<link href="styles.css?v=abc12345">` 주입 (`sed` 치환, 상대경로 — `file://` 지원)
- Nginx: `location ~* \.(css|js)$ { expires 1y; add_header Cache-Control "public, immutable"; gzip_static on; }`
- `index.html` 자체는 `Cache-Control: no-cache` (ETag/If-None-Match로 짧은 재검증)
- **Pros**: 파일명 변경 없음 → `git diff` 깔끔, `rsync` 동기화 단순, Nginx `gzip_static` 동작(`app.js.gz` 대응)
- **Cons**: 일부 CDN/프록시가 쿼리스트링 포함 URL을 캐시 안 하는 역사적 이슈 존재(Cloudflare 등 최신은 해결). OCI 단일 호스트 직접 서빙이므로 해당 없음.

#### Option B2 — **파일명 해시 `app.abc12345.js`**
- 파일 이름 자체에 해시 포함
- **Pros**: 모든 CDN/프록시와 100% 호환, "물리적으로 다른 파일"이므로 캐시 오염 불가
- **Cons**: 빌드 스크립트가 `app.js → app.{hash}.js` 리네임 + `index.html` 치환 + 구버전 청소(디스크 용량) 필요. `server/deploy/` 하에 롤백용 2버전만 유지하는 GC 로직 추가.
- **Trade-off**: B1 대비 스크립트 복잡도 +30%, 실익은 OCI 단일 호스트에서 한계효용 적음.

#### Option B3 — **ETag 의존 (해시 없음)**
- Nginx 기본 ETag, `Cache-Control: public, max-age=0, must-revalidate`
- **Pros**: 빌드 스크립트 불필요
- **Cons**: 매 요청 조건부 GET(304 왕복) → 모바일 LTE에서 체감 지연. `immutable` 이점 상실.
- **Invalidation rationale**: resume-2026-04-23.md의 `Cache-Control immutable` 산출물 요구와 불일치.

**→ Option B1 선택.** 쿼리스트링 해시 + `immutable`. OCI 단일 호스트 환경에서 충분. 필요 시 향후 B2로 무중단 이관 가능(경로 호환).

### C. 정적 파일 서빙 경로

#### Option C1 — **루트 동일 디렉토리 (상대경로 `styles.css`, `app.js`)** [RECOMMENDED]
- Nginx `root /home/ubuntu/job_change;` 유지, 파일만 추가
- HTML 내 참조는 **상대경로**: `href="styles.css?v=..."`, `src="app.js?v=..."` — `file://` 오프라인 지원(§1 Principles, §2 Drivers 참조) 유지 필수
- **Pros**: 최소 변경, try_files 동작 그대로, `file://` 직접 열기 시 JS/CSS 로드 성공
- **Cons**: 프로젝트 루트에 정적 자산이 섞임

#### Option C2 — **`/static/` prefix (`/static/app.js`)**
- `/home/ubuntu/job_change/static/` 디렉토리 생성, Nginx `location /static/` 별도 블록
- **Pros**: 정적/동적 구분, 향후 `/static/img/` 확장 용이
- **Cons**: 현재 자산 2개를 위해 디렉토리 구조 변경 과다. 향후 필요 시 P5-2에서 재고려.

**→ Option C1 선택.** 루트 직접. 미래 확장 필요 시 리다이렉트로 이관.

## 4. Pre-mortem (DELIBERATE)

### Scenario 1: "전역 스코프 누락으로 inline onclick이 `ReferenceError`"
- **실패 양상**: `app.js`로 옮긴 후 `openAuth()`, `go()`, `compare()` 등 72개 inline handler가 `Uncaught ReferenceError: openAuth is not defined` 로 전 페이지 마비.
- **근본 원인**: `<script type="module">` 실수 추가, 또는 `'use strict'` 추가 + IIFE 감쌈으로 전역 누출 차단.
- **완화책**:
  1. `<script src="app.js?v={hash}"></script>` (상대경로, `defer` 없음, `</body>` 직전) — `type="module"` 속성 절대 추가 금지 (plan의 Step 2 체크리스트에 명시).
  2. `app.js` 최상단에 `'use strict'` 추가하지 않음 (원본 `<script>` 블록에도 없음 — 그대로 유지).
  3. 로컬 검증 시 `file://` + `http://localhost` 양쪽에서 `grep -rE "onclick=\"[a-z]+\("` 로 추출한 함수명 전수 콘솔 호출 테스트.
  4. Git pre-commit 훅 대신 수동 체크: 새 `app.js`에서 `grep -c "^function "` 결과가 원본 `index.html`의 해당 라인 범위와 일치.

### Scenario 2: "배포 중 캐시 미스매치 — `index.html`은 새 해시, `.css`/`.js`는 구버전 파일"
- **실패 양상**: `rsync` 도중 `index.html`만 먼저 도착 → 사용자 브라우저가 `app.js?v=newhash` 요청 → Nginx가 아직 도착 안 한 `app.js`(구버전) 반환 → JS 에러 + "비교 시작" 버튼 먹통.
- **근본 원인**: 배포 순서 불명확 + atomic swap 없음.
- **완화책**:
  1. 배포 순서 고정: **① `app.js`/`styles.css` 업로드 → ② `sha1sum` 산출 → ③ `index.html` 해시 치환 후 업로드 → ④ `nginx -s reload`**. HTML은 항상 마지막.
  2. 배포 스크립트 `server/deploy/release-frontend.sh` 작성 (rsync 단계별 분리).
  3. `index.html`은 `Cache-Control: no-cache` — 브라우저가 매번 재검증 → 이전 HTML이 새 해시를 참조할 창 없음.
  4. 배포 직후 5분간 `nginx -T` + `curl -I https://yourdomain.com/app.js?v={hash}` 로 200 확인.

### Scenario 4: "OAuth 리턴 `?token=` URL이 브라우저 주소창에 노출"
- **실패 양상**: 사용자 OAuth 리다이렉트로 `https://<host>/?token=<JWT>&mbr_id=...` 진입 → 주소창에 토큰이 노출되어 브라우저 히스토리/Referer 헤더로 유출.
- **근본 원인**: 원본 `<script>` 블록은 `</body>` 직전 최하단에서 **즉시 실행**되어 IIFE `handleOAuthReturn()` 이 `history.replaceState` 로 URL을 즉시 정리한다. 만약 분리 시 `<script src="app.js" defer>` 를 `<head>` 에 배치하면 `defer` 속성이 실행을 `DOMContentLoaded` 전까지 지연 → 렌더러가 토큰 포함 URL 을 먼저 주소창에 렌더 → 토큰 노출.
- **완화책 (권장)**:
  1. **`defer` 속성 사용 금지.** `<script src="app.js?v={hash}"></script>` (평문) 형태로 유지.
  2. 배치 위치는 **원본과 동일하게 `</body>` 직전 최하단**. 이로써 DOM 파싱 완료 후 즉시 실행 + `history.replaceState` 가 최초 페인트 전에 완료 (또는 최소 지연).
  3. §3 Option A1 이 이 조건을 강제. §7.1 Acceptance에 `grep '<script src="app.js' index.html` 결과가 `</body>` 직전 라인에 있는지 수동 확인.
  4. 배포 후 `curl` 테스트: `?token=X` 부착한 URL로 접근 → 브라우저 주소창에 `?token=` 잔존 여부 수동 검증.

### Scenario 3: "CSS cascade 순서 차이로 특정 화면 레이아웃 붕괴"
- **실패 양상**: 원본은 `<style>` 블록이 `<head>` 내부에서 DOM 앞에 파싱됐지만, 외부 `styles.css`는 네트워크 지연으로 FOUC 발생 + 관리자 화면 `.adm-tbl` 같은 mobile media query가 특정 순서에서 재정렬되어 버튼 겹침.
- **근본 원인**: CSS 파일 내 규칙 순서가 원본과 다르거나, media query가 중간에서 잘려서 순서 꼬임.
- **완화책**:
  1. 추출 시 **바이트 단위 복사** — `sed -n '10,675p' index.html > styles.css` (첫 `<style>` 제거, 마지막 `</style>` 제거). 수작업 편집 금지.
  2. 추출 후 `diff <(extract_style_from_original) styles.css` 로 0 bytes diff 검증.
  3. `<link rel="stylesheet" href="styles.css?v={hash}">` 을 `<head>` 상단 폰트 `<link>` 바로 뒤에 배치(원래 `<style>` 위치 유사, 상대경로).
  4. 수동 QA 체크리스트에 "모바일 @480px, 관리자 @768px, 데스크톱 @1200px 3종 폭 스크린샷 전/후 비교" 포함.

## 5. Test Plan (DELIBERATE)

### 5.1 Unit-level (파일 추출 검증)
- [ ] `wc -l styles.css` ≈ 667 (±5줄 허용: `<style>` 태그 제거분)
- [ ] `wc -l app.js` ≈ 1,863 (±5줄 허용: `<script>` 태그 제거분)
- [ ] `wc -l index.html` — **목표(goal) ~500줄, strict 상한 아님**. 실제 측정 결과를 기록(리포트에 남김). 700줄을 넘어가면 구조 점검 신호.
- [ ] `grep -c "onclick=" index.html` == 72 (불변)
- [ ] `grep -cE "^function " app.js` 와 원본 매칭
- [ ] `node --check app.js` — 구문 검사 전용(실행 안 함). 0-exit 확인. 이후 Chrome DevTools 콘솔 로드 에러 0 재확인.

### 5.2 Integration (전 화면 수동 QA)
로컬 `uvicorn main:app --reload` + `python -m http.server 5173` 동시 기동 후:

| # | 화면 / 플로우 | 검증 항목 |
|---|--------------|-----------|
| 1 | 랜딩 (`s-landing`) | 로고 표시, "비교 시작"/"커리어 가치관" 버튼 클릭, `openAuth()` 동작, `filterPop()` 토글 |
| 2 | 회원가입/로그인 (`openAuth`) | `submitAuth()` 성공 시 토큰 저장, `localStorage.jc_token` 확인, `logout()` 동작 |
| 3 | OAuth 리턴 핸들링 | `?token=...&mbr_id=...` URL 수동 테스트 — IIFE 즉시실행 확인 |
| 4 | 프로파일러 (`s-profiler`) | 질문 진행, 결과 저장 `POST /profiler/results` |
| 5 | 검색/선택 (`s-input`) | `doSearch('a')`/`selComp('b', id)` 현직/이직처 양쪽 |
| 6 | 복지 설정 | `renderBen('a')`/`renderBen('b')`, 토글, `val`/`checked` 상태 |
| 7 | 워크스타일 | `setWS('a','overtime','inclusive')`, `getOTPay()` 계산 |
| 8 | 우선순위 | 드래그 앤 드롭, `curPri`/`curSacrifice` 업데이트 |
| 9 | 비교 리포트 (`compare()`) | Verdict 카드, 연봉, 시급가치, WLB, 3년 전망, Bottom line — 숫자 동일 |
| 10 | 관리자 (`admin.*`) | 검수, 회사/복지/사용자/통계 탭 모두 렌더 |
| 11 | Draft 복원 | 페이지 새로고침 후 `restoreDraft()` 상태 유지 |
| 12 | 반응형 | @480/@768/@1200 — 버튼 겹침/오버플로우 없음 |
| 13 | **`file://` 직접 열기 (오프라인 모드)** | 브라우저에서 `file:///home/ubuntu/job_change/index.html` 직접 열기 → (a) `styles.css` 스타일 적용 확인 (상대경로 로드 성공), (b) `app.js` 로드 후 `API_BASE===''` 분기 진입 확인 (`typeof AUTH_TOKEN` / DevTools에서 `API_BASE` 값 `''`), (c) DB hardcoded fallback 검색 동작 (API 없이 회사명 검색 시 로컬 데이터 반환) |

### 5.3 E2E (프로덕션 smoke test, 배포 직후)
- [ ] `curl -I https://<domain>/` → `Cache-Control: no-cache` on `index.html`
- [ ] `curl -I https://<domain>/app.js?v={hash}` → `200`, `Cache-Control: public, max-age=31536000, immutable`, `Content-Encoding: gzip` (gzip_static)
- [ ] `curl -I https://<domain>/styles.css?v={hash}` → 동일
- [ ] `curl -I https://<domain>/app.js` (해시 없음) → `200` (호환 fallback) 또는 계획적 `404`
- [ ] Chrome DevTools → Network → Disable cache 해제 후 2회 로드 → 2번째는 304 또는 (memory cache)
- [ ] Lighthouse 성능 > 이전 대비 동등 또는 개선

### 5.4 Observability
- Nginx access log: `GET /app.js?v={hash} HTTP/2.0" 200` 패턴 존재 확인
- systemd: `systemctl status nginx` active
- 에러 로그 tail: `journalctl -u nginx -f --since "5 min ago"` → 5분간 4xx/5xx 0건

### 5.5 Rollback drill (배포 전 리허설)
- 로컬에서 `git revert HEAD` 후 `index.html` 원상 복구 확인
- `cp nginx.conf.bak nginx.conf && nginx -s reload` 시뮬레이션

## 6. Task Breakdown

1~2시간 단위 블록. 각 블록은 독립 커밋 가능.

### Step 1 — 준비 및 baseline 캡처 (30분)
- `/home/ubuntu/job_change/index.html` 의 줄 번호 경계 확정 (`<style>` 9-676, `<script>` 866-2729)
- 로컬에 브라우저에서 전 화면 스크린샷 12종 + `file://` 직접 열기 1종 캡처 (`/tmp/p5-1-baseline/`)
- **레포 템플릿 백업**: `cp server/deploy/nginx.conf server/deploy/nginx.conf.bak`
- **운영 서버 실제 설정 백업** (서버에서, 운영 nginx는 `/etc/nginx/sites-available/jobchoice` 경로를 사용):
  `sudo cp /etc/nginx/sites-available/jobchoice /etc/nginx/sites-available/jobchoice.bak`
- `git status` clean 확인

### Step 2 — CSS/JS 추출 (1시간)
- `sed -n '10,675p' index.html > styles.css` (첫/끝 `<style>` 제거)
- `sed -n '867,2728p' index.html > app.js` (첫/끝 `<script>` 제거)
- `diff` 검증 (원본 바이트 == 추출본 바이트)
- `index.html` 편집:
  - `<style>...</style>` 블록 → `<link rel="stylesheet" href="styles.css?v=PLACEHOLDER">` 치환 (**상대경로**, 폰트 `<link>` 바로 뒤 `<head>` 내부)
  - `<script>...</script>` 블록 → `<script src="app.js?v=PLACEHOLDER"></script>` 치환 (**상대경로, `defer` 속성 없음, `</body>` 직전 최하단 위치 유지** — §4 Scenario 4 참조)
- 파일 크기 확인: `index.html` ~500줄 근처 (목표), `styles.css` ~667줄, `app.js` ~1,863줄

### Step 3 — 해시 산출 + 치환 스크립트 (45분)
- `server/deploy/release-frontend.sh` 작성 (**로컬 개발자가 실행**, CI 아님 — §10 결정사항 참조):
  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  CSS_HASH=$(sha1sum styles.css | cut -c1-8)
  JS_HASH=$(sha1sum app.js | cut -c1-8)
  # 상대경로 기준 치환. 정규식은 PLACEHOLDER(대문자) + 기존 해시 모두 매칭.
  sed -i.bak -E "s|styles\\.css\\?v=[A-Za-z0-9]+|styles.css?v=${CSS_HASH}|" index.html
  sed -i.bak -E "s|app\\.js\\?v=[A-Za-z0-9]+|app.js?v=${JS_HASH}|" index.html
  # gzip pre-compress for gzip_static
  gzip -9kf styles.css app.js
  # 주입 실패 가드 — PLACEHOLDER 잔존 시 즉시 실패
  if grep -q '?v=PLACEHOLDER' index.html; then
      echo "해시 주입 실패: index.html 에 'v=PLACEHOLDER' 잔존"
      exit 1
  fi
  echo "CSS=${CSS_HASH} JS=${JS_HASH}"
  ```
- chmod +x, 로컬 실행 → `index.html` diff 확인
- **실행 흐름**: (1) 로컬에서 이 스크립트 실행 → (2) 해시 주입된 `index.html` 을 **git에 commit** → (3) 서버로 rsync → (4) `sudo systemctl reload nginx` (§6 Step 6 참조).

### Step 4 — Nginx 설정 변경 (45분)
- `server/deploy/nginx.conf` 수정:
  ```nginx
  server {
      listen 80;
      server_name yourdomain.com;
      return 301 https://$host$request_uri;
  }
  server {
      listen 443 ssl http2;
      server_name yourdomain.com;
      ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
      ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

      root /home/ubuntu/job_change;
      index index.html;

      # Security headers (모든 응답에 일괄 적용)
      add_header X-Content-Type-Options "nosniff" always;
      add_header X-Frame-Options "DENY" always;
      add_header Referrer-Policy "strict-origin-when-cross-origin" always;
      add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

      # gzip
      gzip on;
      gzip_static on;
      gzip_types text/css application/javascript text/html application/json;
      gzip_vary on;
      gzip_min_length 512;

      # HTML: always revalidate
      location = /index.html {
          add_header Cache-Control "no-cache, must-revalidate" always;
      }
      location = / {
          add_header Cache-Control "no-cache, must-revalidate" always;
          try_files /index.html =404;
      }

      # Hashed static assets: immutable 1 year
      location ~* \.(css|js)$ {
          expires 1y;
          add_header Cache-Control "public, max-age=31536000, immutable" always;
          access_log off;
      }

      # SPA fallback
      location / {
          try_files $uri $uri/ /index.html;
      }

      # API proxy
      location /api/ {
          proxy_pass http://127.0.0.1:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
      }
  }
  ```
- `nginx -t -c <이 파일>` 문법 검증

### Step 5 — 로컬 검증 (1시간)
- `python -m http.server 5173 --directory /home/ubuntu/job_change` 로 정적 서빙
- `uvicorn main:app --reload --port 8000` 백엔드
- 5.2 수동 QA 체크리스트 12개 전부 수행
- 브라우저 DevTools Network 탭: `app.js?v=...` 200, CSS/JS 파싱 에러 0
- 전/후 스크린샷 `diff` 비교

### Step 6 — 프로덕션 배포 + smoke test (45분)

**실행 주체**: 로컬 개발자. CI 없음(§10 결정사항).

1. **로컬에서 `release-frontend.sh` 실행** → `styles.css`/`app.js` 해시 산출 + `index.html` 에 해시 주입 + `styles.css.gz`/`app.js.gz` 생성.
2. **로컬에서 git commit**: 해시 주입된 `index.html` + `styles.css` + `app.js` + `server/deploy/nginx.conf` + `server/deploy/release-frontend.sh` 를 commit (`.gz` 산출물은 `.gitignore`).
3. **서버로 rsync (순서 고정, HTML은 항상 마지막)**: `styles.css` → `app.js` → `styles.css.gz` → `app.js.gz` → `index.html`.
4. **nginx 설정 파일 운영 경로 복사 (별도 단계)**:
   `sudo cp server/deploy/nginx.conf /etc/nginx/sites-available/jobchoice`
   (운영 서버의 nginx가 참조하는 경로는 `/etc/nginx/sites-available/jobchoice` — repo의 `server/deploy/nginx.conf` 는 템플릿이므로 복사 없이는 변경이 반영되지 않음)
5. **문법 검증 + reload**: `sudo nginx -t && sudo systemctl reload nginx`
6. 5.3 E2E smoke test 수행 (curl 헤더 확인 포함 — 보안 헤더 4종 + `Cache-Control`)
7. 5분간 `journalctl -u nginx -f` 모니터링

### Step 7 — 문서화 + 마무리 (30분)
- `CLAUDE.md` 업데이트: "All frontend code stays in `index.html`" → "Frontend = `index.html` + `styles.css` + `app.js`, 섹션 구조는 `app.js` 내 `// ━━` 주석으로 유지. 배포는 `server/deploy/release-frontend.sh`."
- `resume-2026-04-23.md` P5-1 완료 마크
- ADR 섹션(이 계획의 §9) 을 `.omc/plans/adr-p5-1.md` 로 이관
- Conventional commit: `refactor(frontend): split index.html into app.js + styles.css with hashed cache (P5-1)`

**총 예상 시간**: 5시간 15분 (단일 개발자 집중).

## 7. Acceptance Criteria

### 7.1 코드 검증
- [ ] `wc -l index.html` — **목표(goal) ~500줄**. strict 상한이 아니므로 결과를 기록만 함 (§5.1 동일 기준).
- [ ] `styles.css`, `app.js` 신규 파일 존재
- [ ] `grep -c "<style>\|<script>" index.html` == 1 (`<script src=...>` 태그만)
- [ ] `grep "type=\"module\"" index.html` → 결과 0줄 (모듈 사용 금지 원칙)
- [ ] `grep -c 'v=PLACEHOLDER' index.html` == 0 (release 스크립트 해시 주입 확인)
- [ ] `grep 'href="styles.css' index.html` (절대경로 `/styles.css` 금지 — `file://` 지원)
- [ ] `grep 'src="app.js' index.html` (절대경로 `/app.js` 금지)
- [ ] `grep 'defer' index.html` 에서 `app.js` 라인에 `defer` 속성 없음 확인 (§4 Scenario 4)
- [ ] `server/deploy/nginx.conf` 에 `gzip_static on;`, `immutable`, `no-cache` 3개 키워드 모두 존재
- [ ] `server/deploy/nginx.conf` 에 보안 헤더 4종(`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Strict-Transport-Security`) 모두 존재
- [ ] `server/deploy/release-frontend.sh` 존재 + `chmod +x`
- [ ] `server/deploy/nginx.conf.bak` 존재 (롤백용)
- [ ] 서버: `/etc/nginx/sites-available/jobchoice.bak` 존재 (운영 롤백용)

### 7.2 브라우저 검증
- [ ] DevTools Console: 에러/경고 0개 (랜딩 로드 시)
- [ ] `window.openAuth`, `window.go`, `window.compare`, `window.apiFetch` 모두 `typeof === 'function'`
- [ ] 수동 QA 체크리스트 5.2 전 12항목 통과
- [ ] 반응형 @480/@768/@1200 레이아웃 baseline 스크린샷과 시각적 동일
- [ ] 페이지 새로고침 시 FOUC(styled-content flash) 육안 감지 불가

### 7.3 Nginx/배포 검증
- [ ] `nginx -t` 통과
- [ ] `curl -I https://<host>/app.js?v={hash}` → `Cache-Control: public, max-age=31536000, immutable`
- [ ] `curl -I https://<host>/` 또는 `/index.html` → `Cache-Control: no-cache, must-revalidate`
- [ ] `curl -H "Accept-Encoding: gzip" -I https://<host>/app.js?v={hash}` → `Content-Encoding: gzip`
- [ ] 보안 헤더 4종 응답 확인: `curl -I https://<host>/ | grep -iE 'x-frame-options|x-content-type-options|referrer-policy|strict-transport-security'` → 4줄 반환
- [ ] 배포 후 5분간 Nginx error log 0건
- [ ] 배포 후 5분간 사용자 제보 기능 버그 0건

### 7.4 회귀 방지
- [ ] `compare()` 실행 결과 수치(연봉, WLB 점수, 3년 전망)가 분리 전 동일 입력 대비 일치
- [ ] `localStorage.jc_token` / `jc_user` / draft 상태 분리 전후 호환 (업그레이드 사용자 로그아웃 발생 금지)

## 8. Rollback Plan

### 8.1 발동 조건 (아래 중 하나라도 해당 시 즉시 롤백)
- 배포 후 Chrome DevTools Console에서 `ReferenceError` 또는 `Uncaught` 에러 1건 이상
- "비교 시작"/"로그인" 버튼 무응답
- 수동 QA 12개 항목 중 3개 이상 실패
- 5분간 Nginx 5xx > 0.1%

### 8.2 롤백 절차 (목표 RTO: 3분)
1. `cd /home/ubuntu/job_change && git log --oneline -5` 로 P5-1 커밋 SHA 확인
2. `git revert <sha> --no-edit` (새 커밋으로 원복 — amend 금지)
3. 레포 템플릿 원복: `cp server/deploy/nginx.conf.bak server/deploy/nginx.conf`
4. **운영 서버 원복 (2단계 명시)**:
   (a) 레포 템플릿을 운영 경로로 복사: `sudo cp server/deploy/nginx.conf /etc/nginx/sites-available/jobchoice`
   (b) 문법 검증 + reload: `sudo nginx -t && sudo systemctl reload nginx`
   (실패 시 대안: `sudo cp /etc/nginx/sites-available/jobchoice.bak /etc/nginx/sites-available/jobchoice && sudo nginx -t && sudo systemctl reload nginx`)
5. `rm -f styles.css app.js styles.css.gz app.js.gz` (잔존 정적 파일 청소)
6. Smoke test: 랜딩 + 로그인 + 비교 1건
7. Slack/Notion에 롤백 사실 기록 + 다음 시도 차단 시간 지정

### 8.3 부분 롤백 (Nginx만)
- 분리 자체는 정상이지만 `gzip_static` 또는 `immutable` 설정 문제 시: Nginx 설정만 원복 (`immutable` 제거, `max-age=0`). 파일 분리는 유지 가능.

## 9. ADR Draft (P5-1)

### Decision
`index.html` 단일 파일을 `index.html` + `styles.css` + `app.js` 3파일로 분리하고, Nginx에 `gzip_static` + 쿼리스트링 해시 기반 `immutable` 캐싱을 적용한다. 빌드 도구 없이 `sha1sum` + `sed` 쉘 스크립트로 해시 주입한다.

### Decision Drivers
1. Regression risk 최소화 — 2,730줄 전면 리팩터링 리스크 대비 실익 확보 필요
2. Cache invalidation correctness — 배포 직후 구버전 자산이 남는 치명적 버그 방지
3. Deploy simplicity — OCI Always Free 단일 호스트 + CI 없음, 쉘 수준 자동화가 상한

### Alternatives Considered
- **A2 Sectional split**: CSS/JS를 관심사별 다중 파일로. 회귀 리스크 커서 탈락, 후속 태스크로 보류.
- **A3 Inline-preserving**: JS는 HTML에 유지. 목표(`app.js` 분리) 미달로 탈락.
- **B2 파일명 해시**: 모든 CDN 호환이지만 단일 호스트 환경에서 스크립트 복잡도만 증가. 후속 확장 경로로 유지.
- **B3 ETag 의존**: 산출물 요구(`immutable`) 불충족으로 탈락.
- **C2 `/static/` prefix**: 자산 2개로는 과잉 구조화.
- **Phased rollout — 5-1a nginx-only + 5-1b 파일 분리**:
  - 5-1a: nginx gzip + ETag + 보안 헤더 4종만 선반영 (파일 분리 없이)
  - 5-1b: `index.html` → `styles.css` + `app.js` 분리 + `immutable` 해시 캐싱
  - **Pros**: 배포 1회당 변경 범위 축소, 파일 분리 회귀 리스크를 nginx 변경과 분리
  - **Cons**: 단일 개발자 단일 호스트에서 2회 배포 + 2회 smoke test + 2회 롤백 리허설 오버헤드. `immutable` 이 파일 분리와 짝을 이루므로 5-1a 단독으로는 "산출물 요구(immutable + 분리 동시)" 충족 불가.
  - **결정**: **거부.** 5시간 15분 단일 배포 범위가 충분히 관리 가능 수준. 5-1a/b 분리는 이중 운영비만 발생. 단, 배포 당일 Step 1~5 (로컬)를 오전에 마치고 Step 6 (운영 배포)만 저녁 저트래픽 시간대로 분리하는 **시간 기반 분할**은 허용.

### Related Infra Changes (이 ADR에 포함)
- Nginx `listen 443 ssl http2;` — HTTP/2 명시적 활성화 (기존 설정에서 이미 켜져 있으면 변경 없음, 아니면 본 배포에서 추가)

### Why Chosen
**Option A1 + B1 + C1 조합**은 (a) "Zero-regression first" 원칙을 최대 존중하며, (b) `immutable` 캐시 요구를 만족하고, (c) 빌드 도구 없이 10줄 쉘 스크립트로 자동화 가능하다. OCI 단일 호스트라는 현 단계 인프라 제약과 정확히 맞는 복잡도.

### Consequences
**Positive**
- `app.js`/`styles.css` 1년 `immutable` 캐시 → 재방문 사용자 체감 속도 개선
- HTML 파싱 블로킹 최소화 — `<script>` 태그를 `</body>` 직전 최하단에 배치 (원본과 동일, `defer` 없이도 DOM 파싱 후 실행 보장)
- 프로덕션 CSR 화면별 스타일 수정 시 `styles.css` 단일 diff
- 향후 스크래핑/관리자 기능 증설 시 `app.js` 섹션 증가만으로 흡수 가능

**Negative**
- CLAUDE.md 원칙 "All frontend code stays in index.html" 완화 필요 → 문서 업데이트 필수
- 배포 절차가 "파일 2개 → HTML 1개" 순서 지키기로 약간 복잡
- 파일명 해시가 아니므로 일부 엣지 CDN에서 캐시 효율 하락 가능성(현재 해당 없음)

**Neutral**
- 섹션 구조 주석 `// ━━` 그대로 유지 → 기존 개발자 탐색 경험 동일

### Follow-ups
- **P5-1b (선택적)**: 사용자가 1만 명 이상 도달 시 Option B2(파일명 해시)로 이관 + Cloudflare 같은 엣지 CDN 도입 검토
- **P5-2 (사용자 세션 이벤트)**: `app.js` 분리된 현 구조에서 이벤트 트래킹 모듈 `js/tracking.js` 추가
- **Frontend lint**: `eslint` 없이 유지한 현 정책 유지. 필요 시 `eslint-plugin-no-inline-handler` 도입 검토 (향후)
- **Admin 분리**: 관리자 화면 JS/CSS만 `admin.js`/`admin.css` 로 더 쪼개기(비로그인 사용자 부담 ↓). 트래픽 패턴 데이터 수집 후 결정.
  - **비용 경고**: 현 단일 `app.js` 구조에서는 관리자 관련 코드 1줄 수정도 `app.js` 해시 전체를 무효화 → 모든 사용자 재다운로드 발생. 관리자 배포 빈도가 일반 사용자용 UI 배포보다 높아지면 분리 실익 증가. 이벤트 수집(P5-2) 이후 정량 판단.

---

## 10. Resolved Decisions (iteration 2 확정)

아래 항목은 iteration 1 Open Questions 에서 결정으로 승격.

- **`release-frontend.sh` 실행 주체**: **로컬 개발자가 로컬 머신에서 실행**. CI/GitHub Actions/systemd path unit 모두 사용 안 함.
- **해시 주입된 `index.html` 의 git commit 정책**: **git에 commit 한다.** (로컬 실행 → commit → rsync 순서로 고정). `.gz` 산출물은 `.gitignore` 로 제외.
- **배포 순서**: 로컬 `release-frontend.sh` 실행 → git commit → 서버 rsync (css/js/gz → html 마지막) → `sudo cp` 로 nginx 설정 운영 경로 동기화 → `sudo nginx -t && sudo systemctl reload nginx`.
- **나머지 결정 근거**: 산출물 정의(index.html ~500줄 + styles.css + app.js + nginx gzip_static/immutable/파일명 해시)는 `/home/ubuntu/job_change/resume-2026-04-23.md` 의 "Phase 5 — 품질 향상 > P5-1" 섹션을 근거로 한다.

## Open Questions
- [ ] 프로덕션 `server_name` 실제 도메인 확정 여부 (`nginx.conf` 의 `yourdomain.com` 플레이스홀더)
- [ ] `app.js`/`styles.css` 향후 별도 CDN(Cloudflare R2/OCI Object Storage) 이관 시점 기준 — 트래픽 임계값 미정
- [ ] 관리자 화면 분리(`admin.js`) 를 P5-1b로 후속 처리할지 P5-2에 합류시킬지

---

**계획 상태**: DRAFT (iteration 2 revised, 14 Critic 지시 + 5 Architect Must-Fix 전부 반영) → Architect re-review → Critic re-review → 최종 `.omc/plans/p5-1-index-html-split.md`
