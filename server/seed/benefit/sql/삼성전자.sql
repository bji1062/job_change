-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 삼성전자 복리후생 데이터
-- 출처: AI 파싱 (2026-04-14)
-- URL: https://www.samsung-dxrecruit.com/benefit
-- badge: 'est' (추정치 — 공식 확인 시 'official'로 변경)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- 1) 회사 등록 (없는 경우)
INSERT IGNORE INTO TCOMPANY (COMP_ENG_NM, COMP_NM, COMP_TP_ID, INDUSTRY_NM, LOGO_NM, CAREERS_BENEFIT_URL)
VALUES ('samsung_elec', '삼성전자',
        (SELECT COMP_TP_ID FROM TCOMPANY_TYPE WHERE COMP_TP_CD = 'large'),
        '전자/반도체', 'S', 'https://www.samsung-dxrecruit.com/benefit');

-- 2) COMP_ID 조회
SET @comp_id = (SELECT COMP_ID FROM TCOMPANY WHERE COMP_ENG_NM = 'samsung_elec');

-- 3) 기존 추정 데이터 삭제 (official 보존)
DELETE FROM TCOMPANY_BENEFIT WHERE COMP_ID = @comp_id AND BADGE_CD = 'est';

-- 4) 복리후생 INSERT
INSERT INTO TCOMPANY_BENEFIT
  (COMP_ID, BENEFIT_CD, BENEFIT_NM, BENEFIT_AMT, BENEFIT_CTGR_CD,
   BADGE_CD, NOTE_CTNT, QUAL_YN, QUAL_DESC_CTNT, SORT_ORDER_NO)
VALUES
  -- ── 보상·금전 (compensation) ──

  -- ── 근무유연성 (flexibility) ──
  (@comp_id, 'flex_work', 'Work Smart 자율출퇴근', NULL, 'flexibility',
   'est', NULL, TRUE, '월 총 근무시간 내 출퇴근/일일 근무시간 자율 결정, 자율근무존(카페형/도서관형/독서실형) + 사외 거점오피스', 10),

  -- ── 근무환경 (work_env) ──

  -- ── 시간·휴가 (time_off) ──
  (@comp_id, 'refresh_leave', '리프레시 휴가', NULL, 'time_off',
   'est', NULL, TRUE, '연 3일 추가 유급휴가 + Development Day 월중 휴무제도', 30),

  -- ── 건강·의료 (health) ──
  (@comp_id, 'health_check', '건강검진 (본인+가족)', 100, 'health',
   'est', '(추정)', FALSE, NULL, 40),
  (@comp_id, 'medical', '의료비 지원 (본인+가족)', 100, 'health',
   'est', '(추정)', FALSE, NULL, 41),
  (@comp_id, 'clinic', '사내 부속의원', NULL, 'health',
   'est', NULL, TRUE, '내과/치과/한의원/약국/근골격센터 전문 진료 무료 운영 (디지털시티 기준)', 42),
  (@comp_id, 'mental', '심리상담센터', NULL, 'health',
   'est', NULL, TRUE, '전문 심리상담 무료 제공', 43),
  (@comp_id, 'fitness', '피트니스센터', NULL, 'health',
   'est', NULL, TRUE, '호텔급 대형 피트니스센터, 수영장/스쿼시/실내클라이밍/축구장/농구장/테니스장/배드민턴장/야구장', 44),

  -- ── 가족·돌봄 (family) ──

  -- ── 성장·커리어 (growth) ──

  -- ── 여가·라이프 (leisure) ──
  (@comp_id, 'resort', '워터파크/테마파크/휴양소', 100, 'leisure',
   'est', '워터파크 무료, 테마파크 할인, 호텔/휴양지 숙박 지원', FALSE, NULL, 70),
  (@comp_id, 'library', '사내 북카페/구독형 도서관', NULL, 'leisure',
   'est', NULL, TRUE, '대출·반납 가능 사내 북카페/라이브러리, 온라인 구독형 도서관 운영', 71),

  -- ── 경제적 부가혜택 (perks) ──
  (@comp_id, 'welfare_point', '선택적 복리포인트', 200, 'perks',
   'est', '건강/여행/공연/도서/교육 자율 사용', FALSE, NULL, 80),
  (@comp_id, 'discount', '자사 제품 임직원가 구매', 100, 'perks',
   'est', '가전/모바일 할인 (추정)', FALSE, NULL, 81),
  (@comp_id, 'meal', '구내식당 삼시세끼 무료', 432, 'perks',
   'est', '일 18,000원 x 240일 환산', FALSE, NULL, 82),
  (@comp_id, 'transport', '통근버스', 120, 'perks',
   'est', '수도권 150여 노선, 일 약 800회 운행', FALSE, NULL, 83)
ON DUPLICATE KEY UPDATE
  BENEFIT_NM=VALUES(BENEFIT_NM), BENEFIT_AMT=VALUES(BENEFIT_AMT),
  BENEFIT_CTGR_CD=VALUES(BENEFIT_CTGR_CD), BADGE_CD=VALUES(BADGE_CD),
  NOTE_CTNT=VALUES(NOTE_CTNT), QUAL_YN=VALUES(QUAL_YN),
  QUAL_DESC_CTNT=VALUES(QUAL_DESC_CTNT), SORT_ORDER_NO=VALUES(SORT_ORDER_NO);
