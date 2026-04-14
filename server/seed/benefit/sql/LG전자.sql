-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- LG전자 복리후생 데이터
-- 출처: AI 파싱 (2026-03-31)
-- URL: https://www.lge.co.kr/company/recruit
-- badge: 'est' (추정치 — 공식 확인 시 'official'로 변경)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- 1) 회사 등록 (없는 경우)
INSERT IGNORE INTO TCOMPANY (COMP_ENG_NM, COMP_NM, COMP_TP_ID, INDUSTRY_NM, LOGO_NM, CAREERS_BENEFIT_URL)
VALUES ('lg_elec', 'LG전자',
        (SELECT COMP_TP_ID FROM TCOMPANY_TYPE WHERE COMP_TP_CD = 'large'),
        '전자/가전', 'L', 'https://www.lge.co.kr/company/recruit');

-- 2) COMP_ID 조회
SET @comp_id = (SELECT COMP_ID FROM TCOMPANY WHERE COMP_ENG_NM = 'lg_elec');

-- 3) 기존 추정 데이터 삭제 (official 보존)
DELETE FROM TCOMPANY_BENEFIT WHERE COMP_ID = @comp_id AND BADGE_CD = 'est';

-- 4) 복리후생 INSERT
INSERT INTO TCOMPANY_BENEFIT
  (COMP_ID, BENEFIT_CD, BENEFIT_NM, BENEFIT_AMT, BENEFIT_CTGR_CD,
   BADGE_CD, NOTE_CTNT, QUAL_YN, QUAL_DESC_CTNT, SORT_ORDER_NO)
VALUES
  -- ── 보상·금전 (compensation) ──
  (@comp_id, 'bonus', '인센티브/성과급', NULL, 'compensation',
   'est', NULL, TRUE, '조직·개인 성과 기반 인센티브 + 회사 경영성과에 따른 성과급', 1),

  -- ── 근무유연성 (flexibility) ──
  (@comp_id, 'flex_work', '출퇴근 유연제도', NULL, 'flexibility',
   'est', NULL, TRUE, '출퇴근 유연제도 운영', 10),

  -- ── 근무환경 (work_env) ──

  -- ── 시간·휴가 (time_off) ──
  (@comp_id, 'refresh_leave', '장기근속 포상', NULL, 'time_off',
   'est', NULL, TRUE, '10년 이상 장기근속자에게 5년마다 포상금과 휴가 지급, 20년/30년 근속 시 배우자 동반 해외여행 제공', 30),
  (@comp_id, 'leave_general', '휴가제도', NULL, 'time_off',
   'est', NULL, TRUE, '휴가제도 운영', 31),

  -- ── 건강·의료 (health) ──
  (@comp_id, 'health_check', '건강검진', 100, 'health',
   'est', '(추정)', FALSE, NULL, 40),
  (@comp_id, 'medical', '의료비 지원', 100, 'health',
   'est', '(추정)', FALSE, NULL, 41),
  (@comp_id, 'insurance', '단체 보험', 50, 'health',
   'est', '(추정)', FALSE, NULL, 42),

  -- ── 가족·돌봄 (family) ──
  (@comp_id, 'event', '경조금 지원', 100, 'family',
   'est', '(추정)', FALSE, NULL, 50),

  -- ── 성장·커리어 (growth) ──

  -- ── 여가·라이프 (leisure) ──
  (@comp_id, 'resort', '콘도 지원', 100, 'leisure',
   'est', '(추정)', FALSE, NULL, 70),
  (@comp_id, 'club', '동호회', 30, 'leisure',
   'est', '레저/문화/스포츠/음악/봉사 (추정)', FALSE, NULL, 71),
  (@comp_id, 'sports_ticket', '스포츠 티켓', 30, 'leisure',
   'est', '(추정)', FALSE, NULL, 72),

  -- ── 경제적 부가혜택 (perks) ──
  (@comp_id, 'welfare_point', '선택적 복리후생 포인트', 100, 'perks',
   'est', '연 100만원 (원문 명시), 생활/건강/교육/레저/패션/제품', FALSE, NULL, 80),
  (@comp_id, 'housing_loan', '주택자금 지원', NULL, 'perks',
   'est', NULL, TRUE, '주택자금 지원', 81),
  (@comp_id, 'meal', '사내식당', 432, 'perks',
   'est', '일 18,000원 × 240일 환산 (추정)', FALSE, NULL, 82),
  (@comp_id, 'transport', '출퇴근 버스', 120, 'perks',
   'est', '사업장별 통근버스 (추정)', FALSE, NULL, 83)
ON DUPLICATE KEY UPDATE
  BENEFIT_NM=VALUES(BENEFIT_NM), BENEFIT_AMT=VALUES(BENEFIT_AMT),
  BENEFIT_CTGR_CD=VALUES(BENEFIT_CTGR_CD), BADGE_CD=VALUES(BADGE_CD),
  NOTE_CTNT=VALUES(NOTE_CTNT), QUAL_YN=VALUES(QUAL_YN),
  QUAL_DESC_CTNT=VALUES(QUAL_DESC_CTNT), SORT_ORDER_NO=VALUES(SORT_ORDER_NO);
