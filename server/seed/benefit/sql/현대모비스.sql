-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 현대모비스 복리후생 데이터
-- 출처: AI 파싱 (2026-03-31)
-- URL: https://careers.mobis.co.kr
-- badge: 'est' (추정치 — 공식 확인 시 'official'로 변경)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- 1) 회사 등록 (없는 경우)
INSERT IGNORE INTO TCOMPANY (COMP_ENG_NM, COMP_NM, COMP_TP_ID, INDUSTRY_NM, LOGO_NM, CAREERS_BENEFIT_URL)
VALUES ('hyundai_mobis', '현대모비스',
        (SELECT COMP_TP_ID FROM TCOMPANY_TYPE WHERE COMP_TP_CD = 'large'),
        '자동차부품', 'H', 'https://careers.mobis.co.kr');

-- 2) COMP_ID 조회
SET @comp_id = (SELECT COMP_ID FROM TCOMPANY WHERE COMP_ENG_NM = 'hyundai_mobis');

-- 3) 기존 추정 데이터 삭제 (official 보존)
DELETE FROM TCOMPANY_BENEFIT WHERE COMP_ID = @comp_id AND BADGE_CD = 'est';

-- 4) 복리후생 INSERT
INSERT INTO TCOMPANY_BENEFIT
  (COMP_ID, BENEFIT_CD, BENEFIT_NM, BENEFIT_AMT, BENEFIT_CTGR_CD,
   BADGE_CD, NOTE_CTNT, QUAL_YN, QUAL_DESC_CTNT, SORT_ORDER_NO)
VALUES
  -- ── 근무유연성 (flexibility) ──
  (@comp_id, 'flex_work', '선택적 근로시간제/재택근무', NULL, 'flexibility',
   'est', NULL, TRUE, '정해진 근로시간을 자율 조정 가능한 선택적 근로시간제, 재택근무 공식 제도화, 계획 근무시간 초과 시 PC 자동 종료(PC-OFF)', 10),
  (@comp_id, 'remote_office', '거점오피스', NULL, 'flexibility',
   'est', NULL, TRUE, '집 근처 거점오피스에서 근무 가능', 11),

  -- ── 근무환경 (work_env) ──

  -- ── 시간·휴가 (time_off) ──
  (@comp_id, 'leave_general', '연월차 및 기타 휴가', NULL, 'time_off',
   'est', NULL, TRUE, '법정 연차 외 월차, 장기근속휴가, 하계휴가, 경조휴가 제공', 30),
  (@comp_id, 'refresh_leave', '장기근속자 포상', NULL, 'time_off',
   'est', NULL, TRUE, '근속연수에 따라 휴가, 해외여행 등 포상 제공 및 퇴직 지원', 31),

  -- ── 건강·의료 (health) ──
  (@comp_id, 'health_check', '건강검진', 100, 'health',
   'est', '전직원 예방접종/건강검진/여성검진, 40세 이상 추가검진 (추정)', FALSE, NULL, 40),
  (@comp_id, 'medical', '진료비 지원', 100, 'health',
   'est', '본인+부양가족 외래/약제/입원 본인부담금 (추정)', FALSE, NULL, 41),

  -- ── 가족·돌봄 (family) ──
  (@comp_id, 'child_edu', '학자금 지원', NULL, 'family',
   'est', NULL, TRUE, '유아/고등/대학 학자금 지원', 50),
  (@comp_id, 'parenting', '임신/출산/육아 지원', NULL, 'family',
   'est', NULL, TRUE, '임신기/육아기 근로시간 단축, 출산 전후 휴가, 육아휴직 자녀당 최대 2년, 가족돌봄휴직 최대 90일, 상병휴직 지원', 51),
  (@comp_id, 'event', '경조사 지원', 100, 'family',
   'est', '휴가/지원금 (추정)', FALSE, NULL, 52),

  -- ── 성장·커리어 (growth) ──
  (@comp_id, 'edu_support', '교육/학습 지원', NULL, 'growth',
   'est', NULL, TRUE, '스마트러닝/러닝타임제(업무시간 중 주당 최대 2시간 학습), 직무자격증 취득지원(강의비/교재비/응시료), 재직자 석사학위 프로그램(서울대 공학/경영 전문석사 등록금·해외연수 전액 지원), 학습동아리, 직무전문가 양성교육', 60),
  (@comp_id, 'career', '커리어 마켓/사내 스타트업', NULL, 'growth',
   'est', NULL, TRUE, '커리어 마켓을 통한 원하는 직무 이동, 전사 공모를 통한 사내 스타트업 창업 지원, Up-skilling/Re-skilling 직무 전환 교육', 61),

  -- ── 여가·라이프 (leisure) ──
  (@comp_id, 'resort', '휴양시설', 100, 'leisure',
   'est', '사계절 휴양시설/하계휴양소/우리아이 행복여행 (추정)', FALSE, NULL, 70),
  (@comp_id, 'club', '동호회', 30, 'leisure',
   'est', '활동지원금 (추정)', FALSE, NULL, 71),

  -- ── 경제적 부가혜택 (perks) ──
  (@comp_id, 'welfare_point', '종합 포인트', 200, 'perks',
   'est', '여가생활/일상복지 포인트 (추정)', FALSE, NULL, 80),
  (@comp_id, 'discount', '차량 할인', 150, 'perks',
   'est', '현대/기아차 최대 30%, 신입 첫차 20%, 공임비·부품비 30% (추정)', FALSE, NULL, 81),
  (@comp_id, 'relocation', '부임이사 지원', NULL, 'perks',
   'est', NULL, TRUE, '장거리 부임 시 이사비, 부임여비 등 지원', 82),
  (@comp_id, 'housing_support', '새내기 정착/주거지원금', NULL, 'perks',
   'est', NULL, TRUE, '신입사원 정착지원금 및 주거지원금을 임차/구입 무관하게 지원', 83),
  (@comp_id, 'transport', '셔틀버스', 120, 'perks',
   'est', '서울/경기 약 60개 노선 (추정)', FALSE, NULL, 84)
ON DUPLICATE KEY UPDATE
  BENEFIT_NM=VALUES(BENEFIT_NM), BENEFIT_AMT=VALUES(BENEFIT_AMT),
  BENEFIT_CTGR_CD=VALUES(BENEFIT_CTGR_CD), BADGE_CD=VALUES(BADGE_CD),
  NOTE_CTNT=VALUES(NOTE_CTNT), QUAL_YN=VALUES(QUAL_YN),
  QUAL_DESC_CTNT=VALUES(QUAL_DESC_CTNT), SORT_ORDER_NO=VALUES(SORT_ORDER_NO);
