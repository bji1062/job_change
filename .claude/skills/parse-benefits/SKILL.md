---
name: parse-benefits
description: 스크래핑된 복지 텍스트(.txt)를 AI 파싱으로 SQL 파일 변환
user-invocable: true
---

# /parse-benefits — 복지 텍스트 AI 파싱 → SQL 생성

사용자가 `/parse-benefits {회사명}` 을 실행하면 아래 단계를 수행합니다.

선택적 인자: `--id {company_id}` `--type {large|startup|mid|foreign|public}` `--industry {업종}` `--url {채용페이지URL}`

## 실행 단계

### 1단계: 입력 파일 읽기

`server/seed/benefit/{회사명}.txt` 파일을 Read 도구로 읽습니다.

파일이 없으면 사용자에게 안내합니다:
```
.txt 파일이 없습니다. 먼저 스크래핑을 실행하세요:
server/tools/.venv/bin/python server/tools/scrape_benefits.py "{회사명}" --url "{URL}" --raw-only
```

### 2단계: 참조 파일 읽기

다음 파일들을 **병렬**로 읽습니다:
- `server/seed/benefit/삼성전자.sql` — SQL 출력 포맷 참조 (gold standard)
- `server/tools/scrape_benefits.py` 26-228행 — `KNOWN_IDS` (회사명→id 매핑, KOSPI/KOSDAQ 200개사 포함)
- `server/tools/scrape_benefits.py` 234-272행 — `BENEFIT_KEYWORDS` (ben_key 목록)

`company_id`는 다음 우선순위로 결정:
1. `--id` 인자가 있으면 사용
2. `KNOWN_IDS`에 회사명이 있으면 사용
3. 없으면 AskUserQuestion으로 사용자에게 질문

`company_type`과 `industry`도 `--type`, `--industry` 인자 또는 AskUserQuestion으로 확인합니다.

### 3단계: AI 파싱 — 복지 항목 구조화 추출

raw text를 읽고 **모든 복지 항목**을 추출합니다. 정규식이 아닌 문맥 이해로 파싱합니다.

#### 카테고리 (7개)

| 코드 | 라벨 | 포함 항목 |
|------|------|----------|
| `financial` | 보상/금전 | 복지포인트, 성과급, 경조사, 자사주, 할인, 주택대출, 기숙사 |
| `work_env` | 근무환경 | 식대/구내식당, 교통/통근, 업무기기, 휴게공간 |
| `wellness` | 건강/의료 | 건강검진, 의료비, 보험, 심리상담, 피트니스, 사내의원 |
| `time` | 시간/휴가 | 유연근무, 재택, 리프레시휴가, 연차, 휴직 |
| `growth` | 성장/커리어 | 어학, 교육지원, 사내공모, 컨퍼런스 |
| `family` | 가족 | 자녀학자금, 출산/육아, 어린이집, 결혼 |
| `life` | 라이프스타일 | 동호회, 도서, 여행/휴양소 |

#### 기존 ben_key 목록 (우선 사용)

```
financial: welfare_point, event, bonus, stock, discount, housing_loan, dormitory
work_env:  meal, transport, work_tools
wellness:  health_check, medical, insurance, mental, fitness, clinic
time:      refresh_leave, flex_work, leave_general
growth:    lang, edu_support, career
family:    child_edu, parenting, wedding
life:      club, library, resort
```

기존 key에 맞지 않는 회사 고유 복지는 **snake_case 영문**으로 새 key를 생성합니다.
예: `remote_office` (거점오피스), `vehicle_discount` (차량할인), `family_trip` (가족여행지원)

#### 각 항목 추출 규칙

| 필드 | 규칙 |
|------|------|
| `ben_key` | 기존 key 우선, 없으면 snake_case 신규 생성 |
| `name` | 짧은 한국어 명칭 (100자 이내). "구내식당", "선택적 근로시간제" 등 |
| `val` | 연간 환산 금액 (만원). 업계 지식으로 추정. 기준: 식대 ~432(일1.8만×240일), 통근 ~120, 복지포인트 ~200, 건강검진 ~100 |
| `category` | 7개 중 하나 |
| `badge` | 항상 `'est'` |
| `note` | 금액 산출 근거 또는 부가 설명. 예: "일 18,000원 × 240일 환산" |
| `is_qualitative` | 금액 환산 불가 → `TRUE` (유연근무, 자율휴가, 사내의원 등) |
| `qual_text` | 원문에서 발췌한 **실제 복지 설명**. 마케팅 문구 절대 사용 금지. 500자 이내 |
| `sort_order` | 카테고리별 그룹: financial 1-9, wellness 10-19, work_env 20-29, life 30-39, family 40-49, time 50-59, growth 60-69 |

#### 주의사항

- 마케팅/홍보 문구 제외: "우리와 함께하는 당신의 시간이..." 같은 슬로건은 복지 항목이 아님
- 네비게이션/푸터 제외: "Jobs", "Culture", "FAQs", "개인정보 처리방침" 등
- 하나의 복지가 여러 세부 내용을 포함하면 대표 항목으로 통합하되 qual_text에 상세 기재
  - 예: 출산휴가(90일) + 육아휴직(2년) + 어린이집 + 난임휴가 → `parenting` 하나로 통합, qual_text에 모두 기재
- 금액이 원문에 명시된 경우 그대로 사용, 없으면 업계 평균으로 추정하고 note에 "(추정)" 표기

### 4단계: 사용자 확인

파싱 결과를 테이블로 보여줍니다:

```
## {회사명} 복지 파싱 결과 (badge=est)

| # | 카테고리 | ben_key | 항목명 | 연간(만원) | 정성적 | 비고 |
|---|---------|---------|--------|-----------|--------|------|
| 1 | financial | welfare_point | 여가생활 포인트 | 200 | - | 여행/문화/건강/자기계발 사용 |
| 2 | work_env | meal | 구내식당 | 432 | - | 일 18,000원 × 240일 |
...

금전적 합계: 약 {총액}만원/연
정성적 항목: {N}개
```

AskUserQuestion으로 확인:
- "이 결과를 SQL로 생성하시겠습니까?"
- 수정이 필요한 항목이 있으면 사용자가 지정

### 5단계: SQL 생성 및 저장

`삼성전자.sql`의 포맷을 **정확히** 따릅니다:

```sql
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- {회사명} 복리후생 데이터
-- 출처: AI 파싱 ({오늘 날짜})
-- URL: {url 또는 '수동 입력'}
-- badge: 'est' (추정치 — 공식 확인 시 'official'로 변경)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- 1) 회사 등록 (없는 경우)
INSERT IGNORE INTO companies (id, name, type_id, industry, logo, careers_benefit_url)
VALUES ('{id}', '{회사명}', '{type}', '{industry}', '{첫글자}', '{url}');

-- 2) 기존 추정 데이터 삭제 (official 보존)
DELETE FROM company_benefits WHERE company_id = '{id}' AND badge = 'est';

-- 3) 복리후생 INSERT
INSERT INTO company_benefits
  (company_id, ben_key, name, val, category, badge, note, is_qualitative, qual_text, sort_order)
VALUES
  -- ── 보상·금전 (financial) ──
  ('{id}', 'welfare_point', '여가생활 포인트', 200, 'financial', 'est', '여행/문화/건강/자기계발', FALSE, NULL, 1),
  ...
  -- ── 건강·의료 (wellness) ──
  ...
  -- ── 시간·휴가 (time) ──
  ...;
```

**SQL 규칙:**
- 문자열 내 작은따옴표(`'`)는 `\'`로 이스케이프
- NULL 값은 따옴표 없이 `NULL`
- 카테고리별 `-- ──` 주석으로 구분
- 마지막 VALUES 행은 `,` 대신 `;`로 종결

Write 도구로 `server/seed/benefit/{회사명}.sql`에 저장합니다.

### 완료 메시지

```
SQL 파일 생성 완료: server/seed/benefit/{회사명}.sql
적용: mysql jobchoice < server/seed/benefit/{회사명}.sql
```
