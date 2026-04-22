# 직장 선택 OS — 구조 설계 분석 리포트

**작성일**: 2026-04-22
**대상 브랜치**: `claude/oracle-server-setup-c1LNU`
**분석 범위**: 백엔드(FastAPI + aiomysql) / 프론트엔드(index.html 단일 SPA)
**분석 방식**: architect 에이전트(Opus, 읽기 전용) 2개 병렬 + 교차 관찰

---

## 요약 — TOP 개선 포인트

### 백엔드 TOP 3

| # | 개선 포인트 | 임팩트 | 핵심 근거 |
|---|---|---|---|
| 1 | 스케일아웃 전 in-process 상태를 DB/외부 저장소로 이전 | 매우 큼 | `routers/oauth.py:23`(state), `middleware/rate_limiter.py:15`(buckets), `services/cache.py`(reference 캐시), `routers/landing.py:11` — 워커 수를 2로 올리는 즉시 OAuth 로그인 실패 + rate limit 2배 완화 + stale 캐시 1시간 |
| 2 | `_ensure_tables()` 제거 → `seed/schema.sql` 단일 DDL 소스 + `Literal`/`CHECK`로 코드성 컬럼 고정 | 큼 | `database.py:26-84` vs `seed/schema.sql:271-320` — 이미 drift 발생(COMMENT 유무). `BENEFIT_CTGR_CD`/`BADGE_CD`/`ROLE_CD`가 VARCHAR+COMMENT뿐이라 오타 방어 없음 |
| 3 | services 레이어 확장 + 구조화 로깅 + `/ready` 헬스체크 | 큼 | `routers/comparisons.py:11-89`가 5단계 부수효과를 개별 try/except로 삼켜 조용한 데이터 누락. `print()` 10건, DB 확인 없는 `/health` |

### 프론트엔드 TOP 3

| # | 개선 포인트 | 임팩트 | 핵심 근거 |
|---|---|---|---|
| 1 | XSS — API/DB 유래 문자열에 `esc()` 일괄 적용 | 매우 큼(보안) | `index.html:1459`(nA/nB), `:1277`(pfQ), `:1299`(pfResult), landing 카드들 — 관리자 입력 + `saveComparison`의 `comp_a_nm` 사용자 입력이 있는데 escape 누락 |
| 2 | 오프라인 fallback 실제 복구 — `Q_BASE` shape 불일치 | 큼(기능) | `:1020` 하드코드 `q.a.title` vs `:1277` 렌더 `q.option_a.option_a_title_nm` — API 실패 시 프로파일러 `undefined` 에러로 깨짐. "progressive enhancement" 설계 의도 파손 |
| 3 | 상태/사이드이펙트 누락 방지 — 통합 setter + `matched` 정규화 | 큼(유지보수) | `setWS`/`togBen`/`setRate`/`selComp` 각자 `calc()+saveDraft()` 호출, 누락 위험. `matched[s]` shape가 프리셋/API 2갈래라 `b.qual_yn` 분기 동작 |

### 교차 관찰 (BE/FE 공통)

- **`badge=est` 운영 전략 부재**: DB엔 `BADGE_UPDATE_DTM`/`BADGE_SRC_CTNT` 없음, 프론트엔 신뢰도 UI 없음
- **코드성 컬럼 허용값 드리프트**: 9-카테고리를 BE Pydantic `Literal`로 박고 FE는 `/reference/all` 기반으로 통일 필요
- **테스트 공백**: BE services 추출 + FE `compare()` 계산부 `computeVerdict()` 분리 시 단위 테스트 가능

---

## 백엔드 상세 분석

### 구조 맵

```
                         ┌──────────────────────┐
                         │     FastAPI app      │
                         │  (main.py, lifespan) │
                         └──────────┬───────────┘
                                    │
          ┌───────────────┬─────────┼──────────┬──────────────┐
          │               │         │          │              │
   RateLimitMW      CORSMW     8 Routers   (no global    (no logging
  (in-proc dict)  (whitelist)              exception       setup)
                                            handler)
                                    │
       ┌──────────────┬───────────────┬───────────────┬──────────┐
       │              │               │               │          │
     auth        companies        reference       comparisons   admin
                                                                oauth
                                                                landing
                                    │
                              services/
                       auth_service / cache(dict)
                                    │
                              database.py
                  ┌──────────────────────────────────┐
                  │ aiomysql pool (2-10, autocommit) │
                  │ fetch_all / fetch_one / execute  │
                  │ transaction() ctx manager        │
                  │ _ensure_tables() at boot         │
                  └──────────────────────────────────┘
                                    │
                                    ▼
                               MySQL 8 (T-prefix)
```

### 1. 레이어 분리
- **현재**: `routers/ → services/ → database/` 의도는 있으나 services는 `auth_service.py`+`cache.py`만 존재. 비즈니스 로직 대부분 라우터에 박힘.
- **약점**:
  - `routers/comparisons.py:11-89`가 INSERT 4개 + 캐시 무효화 5개를 한 엔드포인트에서 수행
  - JSON 직렬화/역직렬화 로직이 `reference.py`, `companies.py`, `comparisons.py`, `profiler.py` 4곳에 중복
  - 관리자 upsert 코드가 `routers/companies.py:65-101` vs `routers/admin.py:235-256` 거의 동일 (drift 위험)
  - `_ensure_tables()`를 `database.py`에 둔 것은 경계 침범 — DDL이 `schema.sql`과 두 곳에 존재
- **개선**: [H] services 확장, [H] DDL 단일 소스, [M] JSON helper, [L] 라우터 분할

### 2. 데이터 접근
- **강점**: SQL 인젝션 방어 견고(모든 동적 부분이 서버 내부 상수), `transaction()` 컨텍스트 매니저, `_convert_row` Decimal 변환
- **약점**:
  - `comparisons.py:11-89`는 4개 INSERT를 자동커밋 개별 실행 — 중간 실패 시 inconsistent 상태
  - 커넥션 풀 2-10이 타이트: `reference.py:15-166` 단일 요청에서 9회 `fetch_all` 호출
  - N+1 쿼리 잔존: `profiler.py:9-24, 62-87`
  - `lastrowid` 반환이 UPDATE/DELETE에서도 의미 없이 사용됨
- **개선**: [H] `comparisons.py`를 `transaction()`으로 래핑, [M] profiler N+1 제거, [M] 풀 사이즈 재산정

### 3. 스키마 설계 (T-prefix, 9-카테고리, badge)
- **강점**: 한국형 규약(T-prefix, 분류어 종결, 감사 4종, ENUM 금지) 일관성 매우 높음
- **약점**:
  - **ENUM 금지의 이면** — `BENEFIT_CTGR_CD`, `BADGE_CD`, `ROLE_CD`, `LOGIN_PROVIDER_CD`, `METRIC_TYPE_CD` 등이 VARCHAR+COMMENT뿐, 런타임 검증 없음
  - `VRFC_COMP_ID`에 FK 제약 없음 (`schema.sql:185`) — IDOR 방어의 DB 근거 부재
  - `TCOMPARISON.COMP_A_NM/COMP_B_NM` 문자열만, FK 없음 → 회사명 변경/통합 시 통계 꼬임
  - **`badge=est` 운영 전략 부재** — 단순 기본값, 승격/만료/재검증 정책 없음
  - `QUAL_YN + BENEFIT_AMT` 배타성 CHECK 없음
- **개선**: [H] `Literal`/`CHECK`로 허용값 고정, [H] `VRFC_COMP_ID` FK 추가, [M] `COMP_A_ID`/`COMP_B_ID` FK 컬럼, [M] badge 메타 컬럼 추가

### 4. 캐시 전략
- **강점**: 심플한 API, 무효화 포인트 식별 양호, `Cache-Control` 헤더 병행
- **약점**:
  - **다중 프로세스에서 일관성 붕괴**: 관리자 PUT → 해당 워커만 `cache.delete`, 다른 워커는 최대 1시간 stale
  - `_active_visitors`, `_oauth_states`, rate_limiter 전부 프로세스 로컬 — 워커 2개면 OAuth callback이 state 없음으로 400 실패
  - 캐시 stampede 방어 없음
- **개선**: [H] 스케일아웃 전 외부 저장소 이전 (DB 테이블 or Redis), [H] Cache-Control 완화

### 5. 인증/권한
- **강점**: IDOR 방어(bool 거부 삼중 가드) 탄탄, OAuth state 일회성 사용, admin 권한 즉시 차단
- **약점**:
  - 로그아웃/revoke 불가 — 24h JWT 유효, 비밀번호 변경 후에도 이전 토큰 살아있음
  - `role_cd` JWT 박제 — 관리자 승격 후 재로그인 전 권한 없음
  - refresh token 없음
  - localStorage 저장 — XSS 리스크
  - JWT_SECRET 로테이션 경로 없음
  - OAuth callback에서 `cev=0/1` URL 쿼리 노출 (로그/리퍼러)
- **개선**: [M] `TOKEN_VERSION_NO`로 즉시 무효화, [M] refresh token, [M] HttpOnly 쿠키 이전

### 6. 스크래핑 툴 경계
- **강점**: 런타임 의존성 분리 (server vs tools 별도 venv), lazy-import 주석 명시, SQL 파일 산출 방식
- **약점**: 같은 트리 공존의 혼동 위험, Python path 경합, 산출물(`txt_v3_failures.jsonl` 364KB)과 코드 섞임
- **개선**: [M] `scripts/` 최상위 분리 고려, [M] tools/README.md 추가, [L] output/ 하위 몰기

### 7. 에러 처리·관측성
- **강점**: 개별 try/except로 부작용 격리, Pydantic 기본 핸들러
- **약점**:
  - `print()` 기반 로깅 (`comparisons.py`에 9회, `database.py` 1회)
  - **예외 삼키기 패턴** — `comparisons.py`가 except로 광범위 포획 후 print만 하고 "성공" 처리
  - 헬스체크가 DB 확인 안 함 — `main.py:35-37` 항상 ok
  - request id / tracing 없음
- **개선**: [H] 구조화 로깅 + request-id, [H] `/live` + `/ready` 분리, [M] except 좁히기

### 8. 테스트 가능성
- **강점**: `database.*`가 모듈 함수라 patch 용이, `auth_service` 순수 함수
- **약점**: 라우터에 로직 박혀 있어 통합 테스트만 가능, 전역 상태 테스트간 누수, 스키마 drift 감지 부재
- **개선**: [M] services 추출 시 자연 해결, [M] `conftest.py` autouse fixture, [L] schema.sql diff 테스트

---

## 프론트엔드 상세 분석

### 섹션 맵

```
LANDING (s-landing, index.html:657-698)
  │  loadLanding() → /landing/popular|feed|stats
  ▼
PROFILER (s-profiler)
  │  pfJob → Q_BASE + Q_DESC[scenario] → pfAnswers[]
  │  pfFinish(): cosine similarity → PROFILES → pfResult
  │  pfToCompare(): curPri, curSacrifice → go('s-input')
  ▼
INPUT (s-input, index.html:705-797)
  ├ 연봉 + rateChips (selectedRate)
  ├ SEARCH: doSearch(s) → selComp(s,id) → matched[s]
  │   └ onTypeChange(s) → BEN_PRESETS[tp_cd]
  ├ WORK STYLE: setWS(s,field,val) → wsState[s]
  ├ BENEFITS: renderBenCompare() butterfly
  └ PRIORITY: setPri/setSacrifice → curPri/curSacrifice
  [compare() 클릭]
  ▼
REPORT (s-report)
  compare() ~300줄에서 html 문자열 빌드
  → document.getElementById('report').innerHTML
  → saveComparison() → POST /comparisons
```

**전역 상태**: `matched{a,b}`, `benS{a,b}`, `wsState{a,b}`, `curPri`, `curSacrifice`, `selectedRate`, `pfResult`, `pfJob`, `AUTH_TOKEN`, `AUTH_USER`
**드래프트 지속성**: `jc_draft` (7일 TTL, 300ms 디바운스)

### 1. 단일 파일 SPA 설계
- **현재**: 2,461줄 단일 파일 (CSS ~800 + HTML ~180 + JS ~1,620)
- **강점**: 빌드 의존성 0, Progressive enhancement 동일 런타임에서 결정, 탐색 비용 낮음
- **약점**: 중간 규모 도달, CSS/JS 간격 커서 커서 점프 비용, HTTP/1.1 초기 ~230KB blocking
- **개선**: [H] 최소 분리(`app.js`+`styles.css`)로 `index.html` 1,000줄 미만 축소

### 2. ASCII 헤더 섹션 구분
- **강점**: Grep 친화적, 3레이어 동일 마커
- **약점**: `saveDraft()` 같은 섹션 경계 모호, 한글/영어 제목 혼재, 함수 순서 기준 없음
- **개선**: [M] 헤더 컨벤션 문서화, [L] 섹션 JSDoc 추가

### 3. 전역 상태 관리
- **강점**: DevTools 디버깅 쉬움, 이름 일관성
- **약점**:
  - 파생 상태 없음, 호출자 계산식 반복
  - **일관성 불변식 미강제** — `onTypeChange(s)`에서 `matched[s]`와 `tA`의 `comp_tp_cd` 불일치 가능
  - `saveDraft()` 호출 분산 → 누락 위험
  - `pfLock` try/finally 없음
  - **`matched[s]` shape 2갈래** — API(`qual_yn` 포함) vs 프리셋(필드 없음), `compare()`에서 분기 동작
- **개선**: [H] `update(patch)` 헬퍼 도입, [H] `normalizeCompany(raw)` 정규화, [M] `pfLock` try/finally

### 4. side 패턴 (`s = 'a' | 'b'`)
- **강점**: 극도로 간결, DOM id 규칙 기계적
- **약점**:
  - `salA`만 있고 `salB` 없음 — 대칭성 파손, 주석 없음
  - HTML 섹션 `s='a'`/`s='b'` 복제 + 대소문자 suffix만 다름 — 새 ws field 추가 시 HTML 2군데 + 함수 3개 + preset 6개 회사유형 수정
  - 세 번째 side 확장 시 `['a','b']` 하드코드 연쇄 수정
- **개선**: [M] `sides = ['a','b']` 상수 + forEach 렌더

### 5. 오프라인 fallback & DB 상수
- **현재**: `const DB=[]` 빈 배열 (dead fallback), 레퍼런스는 런타임 덮어쓰기
- **강점**: `JOB_GROUPS`, `Q_BASE`, `Q_DESC`, `PROFILES` 기본값 존재
- **약점**:
  - **`Q_BASE`(`{a,b}`)와 `buildQuestions`가 읽는 API shape(`option_a.option_a_title_nm`) 불일치** — **API 실패 시 프로파일러 실제 렌더가 깨짐**. 오프라인 fallback 사실상 미동작
  - `const DB=[]` 이름만 남고 의미 없음
  - `loadRefData()` await 안 함 — race condition
- **개선**: [H] shape 통일 (hardcode ↔ API), [H] `loadRefData()` await, [M] `DB` 제거 또는 최소 대표 회사

### 6. `innerHTML` + 인라인 `onclick` 렌더링
- **강점**: `esc()` OWASP 5문자 치환, 18곳 사용
- **약점 — XSS 누락 의심 지점**:
  - `renderBenCompare()` `${nA}`/`${nB}` innerHTML 주입 (`:1459`, `:1462`)
  - `pfResult` 렌더 `${best.profile_nm}`, `${profile_job_fits.fit}`, `${best.profile_desc_ctnt}` esc 없음 (`:1299`)
  - `pfQ` 렌더 `q.option_a.option_a_title_nm` 등 esc 없음 (`:1277`)
  - 인라인 onclick 정수 기대 자리에 문자열 가능성 (`comp_id`)
- **개선**: [H] 모든 API-derived `*_nm`/`*_ctnt`에 `esc()` 일괄, [H] 정수 자리 Number 변환, [M] CSP `script-src 'self'` 경로

### 7. CSS 설계
- **강점**: 토큰 시스템 의미적 계층, `-d` dim variant 일관
- **약점**: `--border` 정의 미확인, 인라인 style 다량 (pfResult/report 영역), 브레이크포인트 2개만
- **개선**: [M] 토큰 블록 정비, [M] inline style → CSS 클래스 이관, [L] 1024px 추가

### 8. API 통합 (`apiFetch`)
- **강점**: JWT 관리 일관, 401 자동 핸들링 + `_saveRetry`
- **약점**:
  - **모든 오류가 `null`로 평탄화** — 네트워크/5xx/CORS 구분 불가
  - 타임아웃 없음 — AbortController 미부착
  - 로딩 상태 비일관 — 더블 클릭 취약
  - 에러 토스트 없음
  - **`saveComparison`이 401 이중 경로** — raw fetch 직접 호출 우회
- **개선**: [H] `{ok, data, error, status}` 반환, [H] AbortController 타임아웃, [M] 401 단일 경로

### 9. SPA 네비게이션 (`go`)
- **강점**: 뒤로가기 작동, admin 권한 체크, OAuth 토큰 URL 숨김
- **약점**: 딥링크 불가(pathname 항상 `/`), popstate 재진입 시 리포트 캐시 stale, 스크롤 위치 미보존
- **개선**: [M] `location.hash` 도입, [L] scroll 저장

### 10. 테스트 가능성
- **강점**: 순수 함수 요소 존재 (`pfDot`, `pfMag`, `shuffle`, `esc`)
- **약점**: `compare()`에 계산+렌더 혼재, `getSalRange` 등 DOM 의존
- **개선**: [M] `computeVerdict()` 추출 + `tests.html` smoke, [L] Playwright e2e

---

## 교차 관찰 — `badge=est` 운영 전략 상세

### 현 상태
- `TCOMPANY_BENEFIT.BADGE_CD VARCHAR(10) DEFAULT 'est'` 한 칼럼 (`schema.sql:60`)
- 데이터 생성은 항상 `est`, 승격 경로 코드에 없음
- 프론트 `badge_cd` 기반 신뢰도 UI 없음
- 스크래핑 메타(`SOURCE`, `SCRAPED_AT`, `URL`)는 `txt_v3` 헤더에만 있고 SQL 변환 시 소실

### 5개 축의 갭

**1. 출처(Provenance)**: `scrape_official | scrape_fallback | ai_parse | manual | user_report` 구분 없음 → 배치 롤백/URL 추적/사용자 응답 불가

**2. 신선도(Freshness)**: `INS_DTM`/`MOD_DTM`은 감사용, "실제 재확인" 시점 없음 → 1년 묵은 `official`이 여전히 "공식"으로 표시

**3. 상태전이(Lifecycle)**: 실제 운영은 `est → official → stale_official → conflict` 4+ 단계 필요

**4. 카테고리별 TTL**: `flexibility`(6개월) vs `health`(2년) 주기 다른데 동일 기준 적용 중

**5. UX 가시화**: DB에 컬럼만 추가하고 UI에 노출 안 하면 무의미

### 권장 단계별 실행

| 단계 | 작업 | 효과 |
|---|---|---|
| 1 | `BADGE_SRC_CD`, `BADGE_SRC_URL_CTNT`, `VERIFIED_DTM` 컬럼 추가 + parse-benefits 스킬에서 기록 | 이미 수집 중인 메타데이터를 DB에 보존 |
| 2 | `EXPIRES_DTM` + 카테고리별 TTL + 프론트 `badgeChip()` | 신뢰도 가시화 |
| 3 | `TCOMPANY_BENEFIT_BADGE_LOG` + 관리자 검수 UI | 승격 이력 감사 |
| 4 | 만료 cron + 신뢰도 요약 리포트 섹션 | 자동 수명 관리 |
| 5 | 사용자 제보 루프 (`TBENEFIT_REPORT`) | 크라우드 검증 |

### 구체 스키마 추가

```sql
ALTER TABLE TCOMPANY_BENEFIT
  ADD COLUMN BADGE_SRC_CD VARCHAR(20) NULL
    COMMENT '데이터 출처 (scrape_official, scrape_fallback, ai_parse, manual, user_report)',
  ADD COLUMN BADGE_SRC_URL_CTNT VARCHAR(500) NULL
    COMMENT '출처 URL (공식 페이지 스크래핑 시)',
  ADD COLUMN VERIFIED_DTM DATETIME NULL
    COMMENT '마지막 출처 재확인 시점 (INS/MOD_DTM과 별개, 재검증용)',
  ADD COLUMN VERIFIED_BY_ID INT NULL
    COMMENT '검증자 FK (tmember.mbr_id)',
  ADD COLUMN EXPIRES_DTM DATETIME NULL
    COMMENT '유효 만료 시점 (VERIFIED_DTM + category별 TTL)';
```

---

## 실행 로드맵

### Phase 1 — 보안·긴급 수정 (1~2일)
- FE #1: XSS `esc()` 일괄 적용
- BE scrape 버그: `scrape_benefits.py` double-close
- BE 카테고리 드리프트: `BENEFIT_KEYWORDS` 9-cat 정렬

### Phase 2 — 운영 기반 (3~5일)
- badge=est Phase 1: 출처/검증 컬럼 추가 + parse-benefits 스킬 수정
- BE #3: 구조화 로깅 + `/ready` 헬스체크
- BE #2: `_ensure_tables()` 제거 + `Literal` 허용값 고정

### Phase 3 — 데이터 정합성 (3~5일)
- BE: `VRFC_COMP_ID` FK 추가, `comparisons.py` 트랜잭션 래핑
- FE #2: `Q_BASE` shape 불일치 복구, `loadRefData` await
- FE #3: `normalizeCompany()` + `update(patch)` 헬퍼

### Phase 4 — 확장성 (5~7일)
- BE #1: in-process 상태 DB/외부 이전 (OAuth state, rate limiter)
- BE: services 레이어 확장 (`comparison_service`, `benefit_service`)
- badge=est Phase 2~3: 프론트 badgeChip + 관리자 검수 UI

### Phase 5 — 품질 향상 (장기)
- FE: 단일 파일 분리 (app.js + styles.css)
- FE: `apiFetch` 반환 객체화 + AbortController
- badge=est Phase 4~5: 만료 cron + 사용자 제보
- 테스트 인프라 구축

---

## 파일:라인 근거

### 백엔드 핵심
- `server/main.py:9-37` — 앱 구성, 미들웨어, 헬스체크
- `server/database.py:17-23` — 풀 2-10 autocommit
- `server/database.py:26-84` — `_ensure_tables()` DDL drift 근원
- `server/database.py:112-148` — transaction() 컨텍스트
- `server/services/auth_service.py:22-36` — JWT cev bool 방어
- `server/services/cache.py:1-19` — 프로세스 로컬 dict 캐시
- `server/middleware/auth_middleware.py:13-32` — IDOR 삼중 가드
- `server/middleware/rate_limiter.py:15` — 프로세스 로컬 버킷
- `server/routers/oauth.py:23, 130-132, 173-180` — OAuth state, redirect
- `server/routers/comparisons.py:11-89` — 5단계 부수효과 + 예외 삼킴
- `server/routers/reference.py:15-178` — 9 배치 쿼리 + 1h 캐시
- `server/routers/profiler.py:9-24, 62-87` — N+1 쿼리
- `server/seed/schema.sql:27-38, 53-71, 175-191` — 핵심 테이블

### 프론트엔드 핵심
- `index.html:843` — `esc()` 정의
- `index.html:865-875` — `apiFetch` + null 평탄화
- `index.html:934-973` — `saveComparison` 401 이중 경로
- `index.html:1020` vs `:1277` — `Q_BASE` shape 불일치
- `index.html:1180` — 빈 `const DB=[]`
- `index.html:1182-1188` — 전역 상태
- `index.html:1259, 1277, 1299` — profiler XSS 후보
- `index.html:1429-1471` — `renderBenCompare` nA/nB
- `index.html:1648-1957` — `compare()` 300줄
- `index.html:2318-2319` — `go()` + popstate
- `index.html:2443-2458` — init 순서(await 없음)
