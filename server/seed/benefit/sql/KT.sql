-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- KT 복리후생 데이터
-- 출처: AI 파싱 (2026-03-31)
-- URL: https://recruit.kt.com
-- badge: 'est' (추정치 — 공식 확인 시 'official'로 변경)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- 1) 회사 등록 (없는 경우)
INSERT IGNORE INTO TCOMPANY (COMP_ENG_NM, COMP_NM, COMP_TP_ID, INDUSTRY_NM, LOGO_NM, CAREERS_BENEFIT_URL)
VALUES ('kt', 'KT',
        (SELECT COMP_TP_ID FROM TCOMPANY_TYPE WHERE COMP_TP_CD = 'large'),
        '통신', 'K', 'https://recruit.kt.com');

-- 2) COMP_ID 조회
SET @comp_id = (SELECT COMP_ID FROM TCOMPANY WHERE COMP_ENG_NM = 'kt');

-- 3) 기존 추정 데이터 삭제 (official 보존)
DELETE FROM TCOMPANY_BENEFIT WHERE COMP_ID = @comp_id AND BADGE_CD = 'est';

-- 4) 복리후생 INSERT
INSERT INTO TCOMPANY_BENEFIT
  (COMP_ID, BENEFIT_CD, BENEFIT_NM, BENEFIT_AMT, BENEFIT_CTGR_CD,
   BADGE_CD, NOTE_CTNT, QUAL_YN, QUAL_DESC_CTNT, SORT_ORDER_NO)
VALUES
  -- ── 근무유연성 (flexibility) ──
  (@comp_id, 'flex_work', '유연근무제/재택근무', NULL, 'flexibility',
   'est', NULL, TRUE, '탄력적 유연근무제와 재택근무 운영', 10),

  -- ── 근무환경 (work_env) ──

  -- ── 시간·휴가 (time_off) ──
  (@comp_id, 'refresh_leave', '장기근속 포상', NULL, 'time_off',
   'est', NULL, TRUE, '장기근속 시 포상과 휴가 지원', 30),

  -- ── 건강·의료 (health) ──
  (@comp_id, 'health_check', '건강검진', 100, 'health',
   'est', '본인+가족1인 매년 (추정)', FALSE, NULL, 40),
  (@comp_id, 'insurance', '의료/상해 보험', 50, 'health',
   'est', '의료실비·상해보험 (추정)', FALSE, NULL, 41),

  -- ── 가족·돌봄 (family) ──
  (@comp_id, 'child_edu', '자녀 교육비/학자금', NULL, 'family',
   'est', NULL, TRUE, '연령별 맞춤 자녀 교육비 및 학자금 지원', 50),
  (@comp_id, 'parenting', '출산/육아 지원', NULL, 'family',
   'est', NULL, TRUE, '출산휴가 및 육아휴직 지원', 51),
  (@comp_id, 'event', '경조사 지원', 100, 'family',
   'est', '결혼/환갑/칠순 축하금·위로금 (추정)', FALSE, NULL, 52),

  -- ── 성장·커리어 (growth) ──

  -- ── 여가·라이프 (leisure) ──
  (@comp_id, 'resort', '휴양시설', 100, 'leisure',
   'est', '전국 휴양시설 (추정)', FALSE, NULL, 70),

  -- ── 경제적 부가혜택 (perks) ──
  (@comp_id, 'welfare_point', '복지포인트/자기계발비', 200, 'perks',
   'est', '높은 수준 (추정)', FALSE, NULL, 80),
  (@comp_id, 'discount', '통신비/단말기 지원', 120, 'perks',
   'est', '휴대폰 통신비 및 단말기 (추정)', FALSE, NULL, 81),
  (@comp_id, 'housing_loan', '주택자금 대출', NULL, 'perks',
   'est', NULL, TRUE, '저금리 주택자금 대출 지원', 82)
ON DUPLICATE KEY UPDATE
  BENEFIT_NM=VALUES(BENEFIT_NM), BENEFIT_AMT=VALUES(BENEFIT_AMT),
  BENEFIT_CTGR_CD=VALUES(BENEFIT_CTGR_CD), BADGE_CD=VALUES(BADGE_CD),
  NOTE_CTNT=VALUES(NOTE_CTNT), QUAL_YN=VALUES(QUAL_YN),
  QUAL_DESC_CTNT=VALUES(QUAL_DESC_CTNT), SORT_ORDER_NO=VALUES(SORT_ORDER_NO);
