-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 효성중공업 복리후생 데이터
-- 출처: AI 파싱 (2026-03-31)
-- URL: 효성중공업 채용페이지 (수동 입력)
-- badge: 'est' (추정치 — 공식 확인 시 'official'로 변경)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- 1) 회사 등록 (없는 경우)
INSERT IGNORE INTO TCOMPANY (COMP_ENG_NM, COMP_NM, COMP_TP_ID, INDUSTRY_NM, LOGO_NM, CAREERS_BENEFIT_URL)
VALUES ('hyosung_heavy', '효성중공업',
        (SELECT COMP_TP_ID FROM TCOMPANY_TYPE WHERE COMP_TP_CD = 'large'),
        '전력/중공업', '효', NULL);

-- 2) COMP_ID 조회
SET @comp_id = (SELECT COMP_ID FROM TCOMPANY WHERE COMP_ENG_NM = 'hyosung_heavy');

-- 3) 기존 추정 데이터 삭제 (official 보존)
DELETE FROM TCOMPANY_BENEFIT WHERE COMP_ID = @comp_id AND BADGE_CD = 'est';

-- 4) 복리후생 INSERT
INSERT INTO TCOMPANY_BENEFIT
  (COMP_ID, BENEFIT_CD, BENEFIT_NM, BENEFIT_AMT, BENEFIT_CTGR_CD,
   BADGE_CD, NOTE_CTNT, QUAL_YN, QUAL_DESC_CTNT, SORT_ORDER_NO)
VALUES
  -- ── 보상·금전 (compensation) ──
  (@comp_id, 'bonus', '성과급', NULL, 'compensation',
   'est', NULL, TRUE, '사업부(Performance Unit) 평가와 연계하여 조직 목표 대비 달성도에 따른 차별적 보상. 개인 인사평가 결과에 따른 기본급 차등 반영', 1),

  -- ── 근무유연성 (flexibility) ──
  (@comp_id, 'flex_work', '유연근무제', NULL, 'flexibility',
   'est', NULL, TRUE, '선택적 근로시간제와 탄력적 근로시간제 운영. 정해진 근로시간 외 근로에 대해 시간외 근로수당 지급. 임직원 개인별 업무량에 따라 근로시간을 자율 배분', 10),

  -- ── 근무환경 (work_env) ──

  -- ── 시간·휴가 (time_off) ──
  (@comp_id, 'long_service', '장기근속 포상', NULL, 'time_off',
   'est', NULL, TRUE, '10년/20년 근속자에게 포상 휴가 지급', 30),

  -- ── 건강·의료 (health) ──

  -- ── 가족·돌봄 (family) ──
  (@comp_id, 'event', '경조금 및 경조휴가', 50, 'family',
   'est', '(추정)', FALSE, NULL, 50),

  -- ── 성장·커리어 (growth) ──
  (@comp_id, 'career', '자랑스러운 효성인상', NULL, 'growth',
   'est', NULL, TRUE, '분기 및 연간 단위 시상. 마케팅/기술/연구/지원 부문별 수상자 선정, 포상금 및 인사 혜택 부여', 60),
  (@comp_id, 'retirement_support', '퇴직자 지원 제도', NULL, 'growth',
   'est', NULL, TRUE, '정년퇴직 예정자 재취업지원 제도 제공. 만 50세 이상 임직원 대상 진로설계교육 실시. 관계&네트워크/건강/재무/주거&여가 영역 중 필요 영역 개별 신청 가능', 61),

  -- ── 여가·라이프 (leisure) ──

  -- ── 경제적 부가혜택 (perks) ──
  (@comp_id, 'discount', '임직원 제휴 할인', 30, 'perks',
   'est', '효성그룹 제휴 복지몰, 세빛섬 임직원 할인 (추정)', FALSE, NULL, 80),
  (@comp_id, 'birthday_gift', '기념일 선물', 20, 'perks',
   'est', '본인+지정1인 생일선물, 창립기념품 (추정)', FALSE, NULL, 81)
ON DUPLICATE KEY UPDATE
  BENEFIT_NM=VALUES(BENEFIT_NM), BENEFIT_AMT=VALUES(BENEFIT_AMT),
  BENEFIT_CTGR_CD=VALUES(BENEFIT_CTGR_CD), BADGE_CD=VALUES(BADGE_CD),
  NOTE_CTNT=VALUES(NOTE_CTNT), QUAL_YN=VALUES(QUAL_YN),
  QUAL_DESC_CTNT=VALUES(QUAL_DESC_CTNT), SORT_ORDER_NO=VALUES(SORT_ORDER_NO);
