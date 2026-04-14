# benefit.md 구현 계획

## 상태: 1단계 + 2단계 기본 작업 완료 (2026-04-14). 남은 작업: 동의어 사전/이웃 집합/classify() 구현 (비교 로직 고도화)

## 현황 분석

### 스키마 불일치 (핵심 문제)

기존 SQL 파일 6개(`server/seed/benefit/sql/`)가 **구 스키마** 기반으로 작성됨.
현재 `schema.sql`과 백엔드 코드는 **신규 한국형 표준 스키마** 사용 중.

| 항목 | 기존 SQL 파일 | 현재 schema.sql / 백엔드 |
|------|--------------|------------------------|
| 테이블명 | `companies` | `TCOMPANY` |
| 테이블명 | `company_benefits` | `TCOMPANY_BENEFIT` |
| 회사 PK | `id` VARCHAR (예: `'samsung'`) | `COMP_ID` INT AUTO_INCREMENT |
| 복지코드 | `ben_key` | `BENEFIT_CD` |
| 복지명 | `name` | `BENEFIT_NM` |
| 금액 | `val` | `BENEFIT_AMT` |
| 카테고리 | `category` | `BENEFIT_CTGR_CD` |
| 배지 | `badge` | `BADGE_CD` |
| 비고 | `note` | `NOTE_CTNT` |
| 정성적 여부 | `is_qualitative` | `QUAL_YN` |
| 정성적 텍스트 | `qual_text` | `QUAL_DESC_CTNT` |
| 정렬순서 | `sort_order` | `SORT_ORDER_NO` |

### 카테고리 변경 (7종 → 9종)

| # | 신규 코드 | 한글 라벨 | 매핑 원천 (현행 7종) | 가중치 |
|---|----------|----------|---------------------|--------|
| 1 | `compensation` | 보상·금전 | `financial` 중 현금성 (연봉/PS/PI/스톡) | 1.0 |
| 2 | `flexibility` | 근무유연성 | `work_env` 중 유연근무/재택/시차출퇴근 + `time` 일부 | 0.7 |
| 3 | `work_env` | 근무환경 | `work_env` 중 장비/사무공간/기숙사/식당시설 | 0.5 |
| 4 | `time_off` | 시간·휴가 | `time` (범위 확장: 집중휴가/안식월 포함) | 0.7 |
| 5 | `health` | 건강·의료 | `wellness` | 0.6 |
| 6 | `family` | 가족·돌봄 | `family` (육아휴직 포함) | 0.5 |
| 7 | `growth` | 성장·커리어 | `growth` | 0.6 |
| 8 | `leisure` | 여가·라이프 | `life` | 0.3 |
| 9 | `perks` | 경제적 부가혜택 | `financial` 중 식대/통근/복지포인트/자사할인 | 0.8 |

### 신규 테이블 불필요 — 근거

- **동의어 사전 / 이웃 집합**: 프론트엔드 JS 상수로 구현 (비교 로직이 클라이언트 사이드)
- **다중 태깅**: benefit.md §3.6 "주 카테고리에만 금액 귀속, 보조는 표시용" → 기존 `BENEFIT_CTGR_CD` 단일 컬럼 유지
- **카테고리 참조 데이터**: 9개뿐이므로 프론트엔드 상수로 충분 (DB 참조 테이블 불필요)
- **classify() 함수**: 프론트엔드 `compare()` 함수 내에서 구현

---

## 1단계: parse-benefits 스킬 수정

> 목표: 신규 스키마 + 9카테고리 체계에 맞는 SQL을 생성하도록 스킬 업데이트

### 1-1. SQL 템플릿 변경

**변경 전** (구 스키마):
```sql
INSERT IGNORE INTO companies (id, name, type_id, industry, logo, careers_benefit_url)
VALUES ('samsung', '삼성전자', 'large', ...);

DELETE FROM company_benefits WHERE company_id = 'samsung' AND badge = 'est';

INSERT INTO company_benefits
  (company_id, ben_key, name, val, category, badge, note, is_qualitative, qual_text, sort_order)
VALUES
  ('samsung', 'welfare_point', '선택적 복리포인트', 200, 'financial', 'est', ...);
```

**변경 후** (신규 스키마):
```sql
-- 회사 COMP_ID 조회
SET @comp_id = (SELECT COMP_ID FROM TCOMPANY WHERE COMP_ENG_NM = 'samsung');

-- 기존 추정 데이터 삭제 (official 보존)
DELETE FROM TCOMPANY_BENEFIT WHERE COMP_ID = @comp_id AND BADGE_CD = 'est';

-- 복리후생 INSERT
INSERT INTO TCOMPANY_BENEFIT
  (COMP_ID, BENEFIT_CD, BENEFIT_NM, BENEFIT_AMT, BENEFIT_CTGR_CD,
   BADGE_CD, NOTE_CTNT, QUAL_YN, QUAL_DESC_CTNT, SORT_ORDER_NO)
VALUES
  (@comp_id, 'welfare_point', '선택적 복리포인트', 200, 'perks',
   'est', '건강/여행/공연/도서/교육 자율 사용', FALSE, NULL, 1),
  ...
ON DUPLICATE KEY UPDATE
  BENEFIT_NM=VALUES(BENEFIT_NM), BENEFIT_AMT=VALUES(BENEFIT_AMT),
  BENEFIT_CTGR_CD=VALUES(BENEFIT_CTGR_CD), BADGE_CD=VALUES(BADGE_CD),
  NOTE_CTNT=VALUES(NOTE_CTNT), QUAL_YN=VALUES(QUAL_YN),
  QUAL_DESC_CTNT=VALUES(QUAL_DESC_CTNT), SORT_ORDER_NO=VALUES(SORT_ORDER_NO);
```

### 1-2. 카테고리 체계 업데이트

스킬 내 카테고리 목록을 7종 → 9종으로 확장:

```
compensation: 보상/금전 — 연봉, 인센티브, 성과급(PS·PI), 스톡옵션·RSU, 명절상여, 우수사원 포상금
flexibility:  근무유연성 — 포괄/비포괄, 재택, 원격, 시차출퇴근, 유연근무, PC-OFF, 패밀리데이, 거점오피스
work_env:     근무환경 — 사무공간, 장비, 기숙사/사택, 사내식당 시설, 회식문화, 수면실, 라운지
time_off:     시간·휴가 — 법정연차, 하계집중휴가, 리프레시, 안식월, 장기근속휴가, 보건휴가
health:       건강·의료 — 종합검진, 단체보험, 사내의원, 심리상담, 헬스장·운동비
family:       가족·돌봄 — 임신/출산/육아휴직, 어린이집, 자녀학자금, 경조사
growth:       성장·커리어 — 직무교육, 리더십, 어학, MBA, 자기계발비, 도서비, 사내공모
leisure:      여가·라이프 — 휴양시설·콘도, 동호회, 생일기념, 웰컴키트, 사내편의시설
perks:        경제적 부가혜택 — 식대, 통근비, 주차비, 통신비, 복지포인트, 자사·계열 할인
```

### 1-3. sort_order 범위 업데이트

```
compensation  1-9
flexibility   10-19
work_env      20-29
time_off      30-39
health        40-49
family        50-59
growth        60-69
leisure       70-79
perks         80-89
```

### 1-4. KNOWN_IDS 변경

현재 `scrape_benefits.py`의 `KNOWN_IDS`는 VARCHAR id (예: `'samsung'`) 사용.
신규 스키마는 INT PK이므로, SQL에서 `COMP_ENG_NM`으로 `@comp_id` 조회하는 방식으로 변경.
KNOWN_IDS는 `회사명 → COMP_ENG_NM` 매핑으로 변경.

### 1-5. 참조 SQL (gold standard) 갱신

`server/seed/benefit/sql/삼성전자.sql`을 신규 스키마 + 9카테고리로 변환하여 gold standard로 사용.

### 수정 대상 파일

| 파일 | 변경 내용 |
|------|----------|
| `.claude/skills/parse-benefits/SKILL.md` | SQL 템플릿, 카테고리 7→9, sort_order, KNOWN_IDS 참조 방식 |
| `server/seed/benefit/sql/삼성전자.sql` | 신규 스키마로 재작성 (gold standard) |

---

## 2단계: benefit.md 내용 적용을 위한 코드 수정

### 2-1. DB 스키마 수정 (schema.sql)

`TCOMPANY_BENEFIT.BENEFIT_CTGR_CD` COMMENT만 업데이트:

```sql
-- 변경 전
BENEFIT_CTGR_CD VARCHAR(20) NOT NULL COMMENT '복지 카테고리 (financial, work_env, wellness, time, growth, family, life)'

-- 변경 후
BENEFIT_CTGR_CD VARCHAR(20) NOT NULL COMMENT '복지 카테고리 (compensation, flexibility, work_env, time_off, health, family, growth, leisure, perks)'
```

`TBENEFIT_PRESET`도 동일하게 COMMENT 수정.

### 2-2. 백엔드 수정

| 파일 | 변경 내용 |
|------|----------|
| `server/routers/companies.py` | 카테고리 코드 유효성 검증 (있다면) 9종 반영 |
| `server/routers/reference.py` | 캐시 데이터에 새 카테고리 자연 반영 (SELECT이므로 변경 불필요할 가능성 높음) |
| `server/models/company.py` | Pydantic 모델에 카테고리 enum/허용값 업데이트 (있다면) |

> **참고**: 백엔드는 카테고리 코드를 DB에서 그대로 읽어 반환하므로, 카테고리 유효성 검증 코드가 없다면 변경 불필요할 수 있음. 실제 코드 확인 후 판단.

### 2-3. 프론트엔드 수정 (index.html)

#### A. 카테고리 상수 확장

```javascript
// 변경 전 (7종)
const CATEGORIES = {
  financial: { label: '보상/금전', icon: '💰' },
  work_env:  { label: '근무환경', icon: '🏢' },
  wellness:  { label: '건강/의료', icon: '🏥' },
  time:      { label: '시간/휴가', icon: '⏰' },
  growth:    { label: '성장/커리어', icon: '📈' },
  family:    { label: '가족', icon: '👨‍👩‍👧' },
  life:      { label: '라이프스타일', icon: '🎯' }
};

// 변경 후 (9종)
const CATEGORIES = {
  compensation: { label: '보상·금전', icon: '💰', weight: 1.0 },
  flexibility:  { label: '근무유연성', icon: '🔄', weight: 0.7 },
  work_env:     { label: '근무환경', icon: '🏢', weight: 0.5 },
  time_off:     { label: '시간·휴가', icon: '⏰', weight: 0.7 },
  health:       { label: '건강·의료', icon: '🏥', weight: 0.6 },
  family:       { label: '가족·돌봄', icon: '👨‍👩‍👧', weight: 0.5 },
  growth:       { label: '성장·커리어', icon: '📈', weight: 0.6 },
  leisure:      { label: '여가·라이프', icon: '🎯', weight: 0.3 },
  perks:        { label: '경제적 부가혜택', icon: '🎁', weight: 0.8 }
};
```

#### B. 동의어 사전 (benefit.md Phase 2)

```javascript
const SYNONYM_MAP = {
  // meal 도메인
  'meal.full_3meals':     { benKey: 'meal_full',      ctgr: 'perks' },
  'meal.lunch_only':      { benKey: 'meal_lunch',     ctgr: 'perks' },
  'meal.subsidy_money':   { benKey: 'meal_subsidy',   ctgr: 'perks' },
  'meal.snack_bar':       { benKey: 'snack_bar',      ctgr: 'leisure' },
  // commute 도메인
  'commute.shuttle_bus':  { benKey: 'transport',      ctgr: 'perks' },
  'commute.night_taxi':   { benKey: 'night_taxi',     ctgr: 'perks' },
  'commute.parking':      { benKey: 'parking',        ctgr: 'work_env' },
  // ... 50+ 키 전체
};
```

#### C. 이웃 집합 (benefit.md Phase 4)

```javascript
const NEIGHBOR_SETS = [
  // meal
  ['meal_full', 'meal_lunch', 'meal_breakfast', 'meal_cafeteria'],
  ['meal_subsidy', 'meal_cafeteria'],
  // commute
  ['transport', 'commute_subsidy'],
  ['night_taxi', 'transport'],
  // housing
  ['housing_mortgage', 'housing_rent', 'housing_welfare_loan'],
  ['dormitory', 'relocation'],
  // health
  ['health_check', 'health_check_family'],
  ['medical', 'medical_family'],
  ['fitness', 'fitness_subsidy'],
  ['clinic', 'mental'],
  // family
  ['childcare_onsite', 'childcare_subsidy'],
  ['maternity_leave', 'parental_leave', 'fertility_support'],
  // growth
  ['edu_job', 'edu_leader', 'edu_lang'],
  ['mba', 'regional_specialist'],
  ['books', 'self_development'],
  // compensation
  ['profit_sharing', 'personal_incentive'],
  ['stock_option', 'stock_grant'],
  // lifestyle
  ['resort', 'product_discount'],
  ['massage', 'nap_room', 'library_cafe'],
];
```

#### D. classify() 함수 구현

`compare()` 함수 내부 또는 별도 헬퍼로 추가:

```javascript
function classifyBenefit(a, b) {
  if (a.benKey === b.benKey) {
    // 동일 키 — 금액 비교
    if (a.val && b.val) {
      const diff = Math.abs(a.val - b.val) / Math.max(a.val, b.val);
      return diff <= 0.10 ? 'identical' : 'similar';
    }
    if (a.isQual && b.isQual) return 'similar'; // 둘 다 정성적
    return 'similar'; // 한쪽만 금액 있음
  }
  // 이웃 집합 확인
  for (const set of NEIGHBOR_SETS) {
    if (set.includes(a.benKey) && set.includes(b.benKey)) {
      return 'similar';
    }
  }
  return 'unique';
}
```

#### E. 복지 비교 UI 업데이트

`compare()` 내 복지 섹션에서:
- `identical` 항목: "양측 동일" 배지, 차이 없음 표시
- `similar` 항목: 양측 비교 표시, 차이 강조 (금액 차이, 조건 차이)
- `unique` 항목: 한쪽만 표시, "상대 없음" 라벨

### 2-4. 기존 SQL 파일 마이그레이션

`server/seed/benefit/sql/` 하위 6개 파일을 신규 스키마로 변환:

| 파일 | 상태 |
|------|------|
| `삼성전자.sql` | 1단계에서 gold standard로 재작성 |
| `현대모비스.sql` | 마이그레이션 필요 |
| `LG전자.sql` | 마이그레이션 필요 |
| `코웨이.sql` | 마이그레이션 필요 |
| `효성중공업.sql` | 마이그레이션 필요 |
| `KT.sql` | 마이그레이션 필요 |

각 파일에서:
1. 테이블명 → 신규 스키마
2. 컬럼명 → 신규 컬럼명
3. 카테고리 코드 → 9종 체계 매핑
4. VARCHAR company_id → `@comp_id` 변수 방식

### 2-5. 카테고리 매핑 규칙 (기존 데이터 변환 시)

기존 `ben_key` → 신규 카테고리 매핑:

```
# financial → compensation 또는 perks
welfare_point   → perks        (복지포인트는 경제적 부가혜택)
event           → family       (경조사는 가족)
bonus           → compensation (성과급은 보상)
stock           → compensation (스톡은 보상)
discount        → perks        (자사할인은 부가혜택)
housing_loan    → perks        (대출이자지원은 부가혜택)
dormitory       → work_env     (기숙사는 근무환경)

# work_env → work_env 또는 flexibility
meal            → perks        (식대는 부가혜택)
transport       → perks        (통근비는 부가혜택)
work_tools      → work_env     (장비는 근무환경)

# wellness → health
health_check    → health
medical         → health
insurance       → health
mental          → health
fitness         → health
clinic          → health

# time → time_off 또는 flexibility
refresh_leave   → time_off     (리프레시 휴가)
flex_work       → flexibility  (유연근무)
leave_general   → time_off     (일반 휴가)

# growth → growth (변경 없음)
lang            → growth
edu_support     → growth
career          → growth

# family → family (변경 없음)
child_edu       → family
parenting       → family
wedding         → family

# life → leisure (변경 없음)
club            → leisure
library         → leisure
resort          → leisure
```

---

## 실행 순서

```
[1단계] parse-benefits 스킬 수정
 ├─ 1-1. SKILL.md SQL 템플릿 업데이트 (신규 스키마)
 ├─ 1-2. 카테고리 체계 7→9종
 ├─ 1-3. sort_order 범위 재정의
 ├─ 1-4. KNOWN_IDS 참조 방식 변경
 └─ 1-5. 삼성전자.sql gold standard 재작성

[2단계] 코드 수정
 ├─ 2-1. schema.sql COMMENT 업데이트 (BENEFIT_CTGR_CD 9종)
 ├─ 2-2. 백엔드 — 카테고리 관련 코드 확인 및 수정
 ├─ 2-3. 프론트엔드
 │   ├─ A. 카테고리 상수 확장 (9종 + 가중치)
 │   ├─ B. 동의어 사전 상수 추가
 │   ├─ C. 이웃 집합 상수 추가
 │   ├─ D. classify() 함수 구현
 │   └─ E. 복지 비교 UI 업데이트 (identical/similar/unique 배지)
 ├─ 2-4. 기존 SQL 파일 6개 마이그레이션
 └─ 2-5. 기존 ben_key → 신규 카테고리 매핑 적용
```

---

## 체크리스트

- [x] 1-1. SKILL.md SQL 템플릿 (2026-04-14 완료, audit 통과)
- [x] 1-2. 카테고리 9종 (SKILL.md에 반영)
- [x] 1-3. sort_order (SKILL.md에 반영)
- [x] 1-4. KNOWN_IDS → COMP_ENG_NM 조회 방식 변경 (SKILL.md에 반영)
- [x] 1-5. 삼성전자.sql gold standard (DB 실행 검증 완료, 13건)
- [x] 2-1. schema.sql COMMENT + BENEFIT_AMT DEFAULT NULL (DB ALTER 적용 완료)
- [x] 2-2. 백엔드 수정 (admin.py, scrape_benefits.py, test_admin.py)
- [x] 2-3-A. 프론트엔드 카테고리 상수 (CAT_LABELS, BEN_PRESETS, ADM_CAT_OPTS + 관리자 기본값)
- [ ] 2-3-B. 동의어 사전 (2단계 후속 — 비교 로직 고도화 시)
- [ ] 2-3-C. 이웃 집합 (2단계 후속 — 비교 로직 고도화 시)
- [ ] 2-3-D. classify() 함수 (2단계 후속 — 비교 로직 고도화 시)
- [ ] 2-3-E. 복지 비교 UI (2단계 후속 — classify 구현 후)
- [x] 2-4. SQL 파일 마이그레이션 (5개 파일, DB 실행 검증 완료, 66건)
- [x] 2-5. ben_key 카테고리 매핑 (seed.py BEN_PRESETS + COMPANIES)
