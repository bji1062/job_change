-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 코웨이 복리후생 데이터
-- 출처: AI 파싱 (2026-03-31)
-- URL: https://www.coway.com/recruit
-- badge: 'est' (추정치 — 공식 확인 시 'official'로 변경)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- 1) 회사 등록 (없는 경우)
INSERT IGNORE INTO TCOMPANY (COMP_ENG_NM, COMP_NM, COMP_TP_ID, INDUSTRY_NM, LOGO_NM, CAREERS_BENEFIT_URL)
VALUES ('coway', '코웨이',
        (SELECT COMP_TP_ID FROM TCOMPANY_TYPE WHERE COMP_TP_CD = 'large'),
        '생활가전/렌탈', 'C', 'https://www.coway.com/recruit');

-- 2) COMP_ID 조회
SET @comp_id = (SELECT COMP_ID FROM TCOMPANY WHERE COMP_ENG_NM = 'coway');

-- 3) 기존 추정 데이터 삭제 (official 보존)
DELETE FROM TCOMPANY_BENEFIT WHERE COMP_ID = @comp_id AND BADGE_CD = 'est';

-- 4) 복리후생 INSERT
INSERT INTO TCOMPANY_BENEFIT
  (COMP_ID, BENEFIT_CD, BENEFIT_NM, BENEFIT_AMT, BENEFIT_CTGR_CD,
   BADGE_CD, NOTE_CTNT, QUAL_YN, QUAL_DESC_CTNT, SORT_ORDER_NO)
VALUES
  -- ── 근무유연성 (flexibility) ──

  -- ── 근무환경 (work_env) ──

  -- ── 시간·휴가 (time_off) ──
  (@comp_id, 'refresh_leave', '리프레시 휴가', NULL, 'time_off',
   'est', NULL, TRUE, 'Refresh 휴가 지원', 30),

  -- ── 건강·의료 (health) ──
  (@comp_id, 'health_check', '건강검진', 100, 'health',
   'est', '(추정)', FALSE, NULL, 40),
  (@comp_id, 'insurance', '전직원 상해보험', 50, 'health',
   'est', '(추정)', FALSE, NULL, 41),
  (@comp_id, 'fitness', '헬스케어', NULL, 'health',
   'est', NULL, TRUE, '헬스케어 프로그램 운영', 42),
  (@comp_id, 'mental', '심리 상담실', NULL, 'health',
   'est', NULL, TRUE, '사내 심리 상담실 운영', 43),

  -- ── 가족·돌봄 (family) ──
  (@comp_id, 'child_edu', '자녀 학자금', NULL, 'family',
   'est', NULL, TRUE, '자녀 학자금 지원', 50),
  (@comp_id, 'parenting', '출산/육아 지원', NULL, 'family',
   'est', NULL, TRUE, '자녀 입학 휴가, 난임 휴직, 배우자 출산 휴가, 남녀 구분 없는 육아휴직 제도 (여성가족부 가족친화인증 2012년~현재)', 51),
  (@comp_id, 'event', '경조사 지원', 100, 'family',
   'est', '(추정)', FALSE, NULL, 52),

  -- ── 성장·커리어 (growth) ──
  (@comp_id, 'edu_support', '교육/자격증 지원', NULL, 'growth',
   'est', NULL, TRUE, '자격증 지원, 직무 전문가 육성, 신입/경력 입사자 온보딩 과정, 리더십 교육, 직무 전문 교육, 이러닝 과정', 60),
  (@comp_id, 'lang', '어학 교육', NULL, 'growth',
   'est', NULL, TRUE, '어학 교육 지원', 61),

  -- ── 여가·라이프 (leisure) ──
  (@comp_id, 'resort', '휴양지 숙소', 100, 'leisure',
   'est', '(추정)', FALSE, NULL, 70),

  -- ── 경제적 부가혜택 (perks) ──
  (@comp_id, 'welfare_point', '복지포인트', 200, 'perks',
   'est', '(추정)', FALSE, NULL, 80),
  (@comp_id, 'holiday_gift', '기념일 선물', 30, 'perks',
   'est', '창립기념일/설날/추석 (추정)', FALSE, NULL, 81),
  (@comp_id, 'housing_loan', '주택자금 이자 지원', NULL, 'perks',
   'est', NULL, TRUE, '주택자금 대출 이자 지원', 82)
ON DUPLICATE KEY UPDATE
  BENEFIT_NM=VALUES(BENEFIT_NM), BENEFIT_AMT=VALUES(BENEFIT_AMT),
  BENEFIT_CTGR_CD=VALUES(BENEFIT_CTGR_CD), BADGE_CD=VALUES(BADGE_CD),
  NOTE_CTNT=VALUES(NOTE_CTNT), QUAL_YN=VALUES(QUAL_YN),
  QUAL_DESC_CTNT=VALUES(QUAL_DESC_CTNT), SORT_ORDER_NO=VALUES(SORT_ORDER_NO);
