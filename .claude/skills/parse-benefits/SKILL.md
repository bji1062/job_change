---
name: parse-benefits
description: 스크래핑된 복지 텍스트(.txt)를 AI 파싱으로 SQL 파일 변환 (신규 스키마 TCOMPANY_BENEFIT + 9카테고리)
user-invocable: true
---

# /parse-benefits — 복지 텍스트 AI 파싱 → SQL 생성

사용자가 `/parse-benefits {회사명}` 을 실행하면 아래 단계를 수행합니다.

선택적 인자: `--eng {COMP_ENG_NM}` `--type {large|startup|mid|foreign|public}` `--industry {업종}` `--url {채용페이지URL}`

## 실행 단계

### 1단계: 입력 파일 읽기 (v3 → v2 → flat 폴백) + 출처 메타 확인

다음 순서로 Read 시도. 파일이 존재하고 크기가 **200 bytes 이상**이면 해당 파일을 채택:

1. `server/seed/benefit/txt_v3/{safe_name(회사명)}.txt` — 공식 페이지 기반 (신뢰도↑, discover_and_scrape.py 출력)
2. `server/seed/benefit/txt_v2/{회사명}.txt` — bokziri 집계 기반 폴백 (기존 수집분)
3. `server/seed/benefit/{회사명}.txt` — 레거시 flat 위치

**메타 헤더 (v3 파일 전용)**:
txt_v3 파일은 선행 몇 줄에 `# KEY: VALUE` 형태의 메타 헤더 후 빈 줄로 본문과 분리됩니다. 읽을 때:

1. 파일을 줄 단위로 읽어 선두 연속 `#` 으로 시작하는 줄은 **메타**로 분리
2. 첫 빈 줄 이후가 실제 본문 (파싱 대상)
3. 메타에서 `SOURCE` 값을 추출 — `official` 이면 공식 페이지, `bokziri_fallback` 이면 bokziri 집계 폴백
4. SQL 생성 시 상단 주석에 `-- 출처: {SOURCE} (SCRAPED_AT={...})` 기재

예시:
```
# SOURCE: official
# COMPANY: 네이버
# URL: https://recruit.navercorp.com/cnts/benefits
# QUERY_INDEX: 0
# SCRAPED_AT: 2026-04-22T01:37:00+00:00
# TEXT_LEN: 4618
# KW_COUNT: 22

<본문 시작>
```

txt_v2 / flat 레거시 파일은 헤더 없음 — 본문 전체를 파싱 대상으로 사용하고 SQL 주석에 `-- 출처: bokziri_legacy` 로 기재.

`safe_name` 규칙 (공백 + 특수문자 → 파일명 안전):
- `LG U+` → `LG_U_plus`
- `SK C&C` → `SK_C_and_C`
- `동원F&B` → `동원F_and_B`
- `CJ ENM` → `CJ_ENM`
- 공백/슬래시/콜론 → `_`

세 위치 모두 없거나 모두 <200 bytes 인 경우 사용자에게 안내:
```
.txt 파일이 없습니다. 둘 중 하나를 실행하세요:
  # 공식 페이지 자동 발견 (추천)
  server/tools/.venv/bin/python server/tools/discover_and_scrape.py --force "{회사명}"
  # 또는 특정 URL 수동 스크래핑
  server/tools/.venv/bin/python server/tools/scrape_benefits.py "{회사명}" --url "{URL}" --raw-only
```

### 2단계: 참조 파일 읽기

다음 파일들을 **병렬**로 읽습니다:
- `server/seed/benefit/sql/삼성전자.sql` — SQL 출력 포맷 참조 (gold standard)
- DB에서 회사 존재 여부 확인 (Bash로 mysql 쿼리)

`COMP_ENG_NM`은 다음 우선순위로 결정:
1. `--eng` 인자가 있으면 사용
2. DB에서 `SELECT COMP_ENG_NM FROM TCOMPANY WHERE COMP_NM = '{회사명}'`으로 조회
3. 없으면 AskUserQuestion으로 사용자에게 질문 (snake_case 영문 식별명)

`company_type`과 `industry`도 `--type`, `--industry` 인자 또는 AskUserQuestion으로 확인합니다.

### 3단계: AI 파싱 — 복지 항목 구조화 추출

raw text를 읽고 **모든 복지 항목**을 추출합니다. 정규식이 아닌 문맥 이해로 파싱합니다.

#### 카테고리 (9개)

| 코드 | 라벨 | 포함 항목 |
|------|------|----------|
| `compensation` | 보상·금전 | 성과급(PS/PI), 인센티브, 스톡옵션, RSU, 명절상여, 우수사원 포상금, **장기근속 포상(포상금·기념품·포상휴가 전체)** |
| `flexibility` | 근무유연성 | 포괄/비포괄, 재택, 원격, 시차출퇴근, 유연근무, PC-OFF, 패밀리데이, 거점오피스 |
| `work_env` | 근무환경 | 사무공간, 장비(맥북/허먼밀러), 기숙사/사택, 사내식당 시설, 회식문화, 수면실, 라운지 |
| `time_off` | 시간·휴가 | 법정연차, 하계집중휴가, 리프레시, 안식월, 보건휴가, 가족돌봄휴가 |
| `health` | 건강·의료 | 종합검진, 단체보험, 사내의원, 심리상담, 헬스장, 운동비, 독감접종 |
| `family` | 가족·돌봄 | 임신/출산/육아휴직, 어린이집, 자녀학자금, 가족 의료비/건강검진 |
| `growth` | 성장·커리어 | 직무교육, 리더십, 어학, MBA/석박사 파견, 도서비, 사내공모, 컨퍼런스 |
| `leisure` | 여가·라이프 | 휴양시설/콘도, 동호회, 웰컴키트, 사내편의시설(안마/북카페) |
| `perks` | 경제적 부가혜택 | 식대, 통근비, 주차비, 통신비, 복지포인트, 자사/계열 할인, 사내대출 이자지원, **생일/기념일 선물·축하금**, **경조사(경조금·경조휴가·화환)**, **카페/스낵바(무료 식음)**, **자기계발비/복지카드**, **대출/주거비(사택·기숙사 제외)** |

#### 기존 BENEFIT_CD 목록 (우선 사용)

```
compensation: bonus, stock_option, stock_grant, profit_sharing, incentive, holiday_gift, excellence_award, long_service_award
flexibility:  flex_work, remote_work, pc_off, family_day, satellite_office
work_env:     work_tools, dormitory, lounge, nap_room, parking
time_off:     refresh_leave, summer_leave, leave_general, birthday_leave
health:       health_check, medical, insurance, mental, fitness, clinic
family:       child_edu, parenting, childcare, fertility_support
growth:       lang, edu_support, career, books, conference, mba
leisure:      club, library, resort, welcome_kit, massage
perks:        welfare_point, meal, transport, telecom, discount, housing_loan, snack_bar, commute_subsidy, self_development, wedding, event, birthday_gift
```

기존 key에 맞지 않는 회사 고유 복지는 **snake_case 영문**으로 새 key를 생성합니다.
예: `vehicle_discount` (차량할인), `family_trip` (가족여행지원), `referral_bonus` (사내추천 보상)

#### 각 항목 추출 규칙

| 필드 | DB 컬럼 | 규칙 |
|------|---------|------|
| `BENEFIT_CD` | BENEFIT_CD | 기존 key 우선, 없으면 snake_case 신규 생성 |
| `BENEFIT_NM` | BENEFIT_NM | 짧은 한국어 명칭 (100자 이내). "구내식당", "선택적 근로시간제" 등 |
| `BENEFIT_AMT` | BENEFIT_AMT | 연간 환산 금액 (만원). 업계 지식으로 추정. 기준: 식대 ~432(일1.8만x240일), 통근 ~120, 복지포인트 ~200, 건강검진 ~100 |
| `BENEFIT_CTGR_CD` | BENEFIT_CTGR_CD | 9개 중 하나 |
| `BADGE_CD` | BADGE_CD | 항상 `'est'` |
| `NOTE_CTNT` | NOTE_CTNT | 금액 산출 근거 또는 부가 설명 (200자 이내). 예: "일 18,000원 x 240일 환산" |
| `QUAL_YN` | QUAL_YN | 금액 환산 불가 → `TRUE` (유연근무, 자율휴가, 사내의원 등) |
| `QUAL_DESC_CTNT` | QUAL_DESC_CTNT | 원문에서 발췌한 **실제 복지 설명**. 마케팅 문구 절대 사용 금지. 500자 이내 |
| `SORT_ORDER_NO` | SORT_ORDER_NO | 카테고리별 그룹 (아래 참조) |

#### SORT_ORDER_NO 범위

```
compensation   1-9
flexibility   10-19
work_env      20-29
time_off      30-39
health        40-49
family        50-59
growth        60-69
leisure       70-79
perks         80-89
```

#### 주의사항

- 마케팅/홍보 문구 제외: "우리와 함께하는 당신의 시간이..." 같은 슬로건은 복지 항목이 아님
- 네비게이션/푸터 제외: "Jobs", "Culture", "FAQs", "개인정보 처리방침" 등
- 하나의 복지가 여러 세부 내용을 포함하면 대표 항목으로 통합하되 QUAL_DESC_CTNT에 상세 기재
  - 예: 출산휴가(90일) + 육아휴직(2년) + 어린이집 + 난임휴가 → `parenting` 하나로 통합, QUAL_DESC_CTNT에 모두 기재
- 금액이 원문에 명시된 경우 그대로 사용, 없으면 업계 평균으로 추정하고 NOTE_CTNT에 "(추정)" 표기
- 카테고리 분류 시 benefit.md의 권장안 B(9분류) 기준을 따르며, 경계 모호 항목은 아래 확정 규칙(2026-04-21)을 최우선 적용:
  - 식대/통근/복지포인트/자사할인 → `perks` (경제적 부가혜택)
  - 유연근무/재택/시차출퇴근 → `flexibility` (근무유연성)
  - 성과급/스톡/인센티브 → `compensation` (보상·금전)
  - **생일/기념일 → `perks`** (선물·축하금의 현금등가)
  - **대출/주거비 → `perks`** (사택·기숙사는 제외, `work_env`)
  - **카페/스낵바 → `perks`** (무료 식음의 현금등가)
  - **자기계발/복지카드 → `perks`** (복지포인트·자기계발비 통합)
  - **장기근속포상 → `compensation`** (포상금·기념품·포상휴가 전체)
  - **경조사지원 → `perks`** (경조금·경조휴가·화환 전체, 가족축 아님)

### 4단계: 사용자 확인

파싱 결과를 테이블로 보여줍니다:

```
## {회사명} 복지 파싱 결과 (badge=est)

| # | 카테고리 | BENEFIT_CD | 항목명 | 연간(만원) | 정성적 | 비고 |
|---|---------|------------|--------|-----------|--------|------|
| 1 | perks | welfare_point | 여가생활 포인트 | 200 | - | 여행/문화/건강/자기계발 사용 |
| 2 | perks | meal | 구내식당 | 432 | - | 일 18,000원 x 240일 |
...

금전적 합계: 약 {총액}만원/연
정성적 항목: {N}개
```

AskUserQuestion으로 확인:
- "이 결과를 SQL로 생성하시겠습니까?"
- 수정이 필요한 항목이 있으면 사용자가 지정

### 5단계: SQL 생성 및 저장

`server/seed/benefit/sql/삼성전자.sql`의 포맷을 **정확히** 따릅니다:

```sql
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- {회사명} 복리후생 데이터
-- 출처: {SOURCE}        ← 메타 헤더의 SOURCE 값 (official / bokziri_fallback / bokziri_legacy)
-- SCRAPED_AT: {값}      ← 메타 헤더의 SCRAPED_AT 값 (없으면 '-')
-- URL: {URL 값 또는 '수동 입력'}
-- 파싱: AI ({오늘 날짜})
-- badge: 'est' (추정치 — 공식 확인 시 'official'로 변경)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- 0) 세션 변수 — 메타 헤더에서 추출 (badge=est 운영 전략 Phase 1)
SET @badge_src_cd = '{BADGE_SRC_CD}';   -- SOURCE 매핑: official→scrape_official, bokziri_fallback→scrape_fallback, 헤더없음→ai_parse
SET @badge_src_url = {BADGE_SRC_URL};   -- URL 값 또는 NULL (수동입력 시)
SET @scraped_at = {SCRAPED_AT};          -- '2026-04-22 01:37:00' 또는 NULL

-- 1) 회사 등록 (없는 경우)
INSERT IGNORE INTO TCOMPANY (COMP_ENG_NM, COMP_NM, COMP_TP_ID, INDUSTRY_NM, LOGO_NM, CAREERS_BENEFIT_URL)
VALUES ('{eng}', '{회사명}',
        (SELECT COMP_TP_ID FROM TCOMPANY_TYPE WHERE COMP_TP_CD = '{type}'),
        '{industry}', '{로고}', '{url}');

-- 2) COMP_ID 조회
SET @comp_id = (SELECT COMP_ID FROM TCOMPANY WHERE COMP_ENG_NM = '{eng}');

-- 3) 기존 추정 데이터 삭제 (official 보존)
DELETE FROM TCOMPANY_BENEFIT WHERE COMP_ID = @comp_id AND BADGE_CD = 'est';

-- 4) 복리후생 INSERT
INSERT INTO TCOMPANY_BENEFIT
  (COMP_ID, BENEFIT_CD, BENEFIT_NM, BENEFIT_AMT, BENEFIT_CTGR_CD,
   BADGE_CD, BADGE_SRC_CD, BADGE_SRC_URL_CTNT, VERIFIED_DTM,
   NOTE_CTNT, QUAL_YN, QUAL_DESC_CTNT, SORT_ORDER_NO)
VALUES
  -- ── 보상·금전 (compensation) ──
  (@comp_id, 'bonus', '성과급', 500, 'compensation',
   'est', @badge_src_cd, @badge_src_url, @scraped_at,
   'OPI+TAI 기준 (추정)', FALSE, NULL, 1),

  -- ── 근무유연성 (flexibility) ──
  (@comp_id, 'flex_work', '유연근무제', NULL, 'flexibility',
   'est', @badge_src_cd, @badge_src_url, @scraped_at,
   NULL, TRUE, '시차출퇴근제 운영', 10),

  -- ── 근무환경 (work_env) ──
  ...

  -- ── 시간·휴가 (time_off) ──
  ...

  -- ── 건강·의료 (health) ──
  ...

  -- ── 가족·돌봄 (family) ──
  ...

  -- ── 성장·커리어 (growth) ──
  ...

  -- ── 여가·라이프 (leisure) ──
  ...

  -- ── 경제적 부가혜택 (perks) ──
  (@comp_id, 'meal', '구내식당', 432, 'perks',
   'est', @badge_src_cd, @badge_src_url, @scraped_at,
   '일 18,000원 x 240일 환산', FALSE, NULL, 80)
ON DUPLICATE KEY UPDATE
  BENEFIT_NM=VALUES(BENEFIT_NM), BENEFIT_AMT=VALUES(BENEFIT_AMT),
  BENEFIT_CTGR_CD=VALUES(BENEFIT_CTGR_CD), BADGE_CD=VALUES(BADGE_CD),
  BADGE_SRC_CD=VALUES(BADGE_SRC_CD), BADGE_SRC_URL_CTNT=VALUES(BADGE_SRC_URL_CTNT),
  VERIFIED_DTM=VALUES(VERIFIED_DTM),
  NOTE_CTNT=VALUES(NOTE_CTNT), QUAL_YN=VALUES(QUAL_YN),
  QUAL_DESC_CTNT=VALUES(QUAL_DESC_CTNT), SORT_ORDER_NO=VALUES(SORT_ORDER_NO);
```

**SOURCE → BADGE_SRC_CD 매핑 (필수):**

| txt_v3 헤더 `SOURCE` | SQL `@badge_src_cd` |
|---|---|
| `official` | `'scrape_official'` |
| `bokziri_fallback` | `'scrape_fallback'` |
| (헤더 없음 — v2/flat 레거시) | `'ai_parse'` |
| 사용자가 수동 입력 | `'manual'` |

**세션 변수 값 치환:**
- `{BADGE_SRC_URL}`: URL이 있으면 `'https://...'` (작은따옴표 포함), 없으면 `NULL`
- `{SCRAPED_AT}`: 메타의 `SCRAPED_AT` ISO8601을 `'2026-04-22 01:37:00'` 형태로 변환, 없으면 `NULL`

**SQL 규칙:**
- 문자열 내 작은따옴표(`'`)는 `''`로 이스케이프 (MySQL 표준)
- NULL 값은 따옴표 없이 `NULL`
- 카테고리별 `-- ──` 주석으로 구분 (9카테고리 순서)
- 마지막 VALUES 행은 `,` 대신 `)` 로 종결 (ON DUPLICATE KEY UPDATE가 이어지므로)
- COMP_TP_ID는 서브쿼리로 조회: `(SELECT COMP_TP_ID FROM TCOMPANY_TYPE WHERE COMP_TP_CD = '{type}')`
- COMP_ID는 `@comp_id` 변수로 참조
- **badge_src_cd / badge_src_url / verified_dtm 은 모든 행에 동일 값이므로 세션 변수로 일괄 주입**

Write 도구로 `server/seed/benefit/sql/{회사명}.sql`에 저장합니다.

### 완료 메시지

```
SQL 파일 생성 완료: server/seed/benefit/sql/{회사명}.sql
적용: mysql -u jobapp -pjobapp jobchoice < server/seed/benefit/sql/{회사명}.sql
```
