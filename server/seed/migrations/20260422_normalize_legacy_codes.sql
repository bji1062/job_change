-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Migration: 레거시 카테고리/뱃지 값 → 9-카테고리 정규화
-- Date: 2026-04-22
-- Plan: .omc/analysis/architecture-review-2026-04-22.md (BE TOP #2 — Literal 허용값 고정)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 배경:
--   4349a89 커밋에서 9-카테고리로 스키마 리팩터를 했지만, 기존 행은 backfill 되지 않아
--   DB 에 레거시 값(financial, wellness, life, time, auto) 이 남아 있음.
--   Pydantic Literal 로 허용값을 고정하면 조회 응답 직렬화가 실패하므로 먼저 정규화.
--
-- 매핑 근거:
--   financial  → compensation (bonus/stock 계열) 또는 perks (나머지) — 개별 BENEFIT_CD 로 분기
--   wellness   → health     (건강·의료)
--   life       → leisure    (여가)
--   time       → time_off   (시간·휴가)
--   BADGE_CD 'auto' → 'est' (자동 삽입된 프리셋 기반 추정치로 해석)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- 1) TCOMPANY_BENEFIT: compensation 키만 먼저 승격
UPDATE TCOMPANY_BENEFIT
SET BENEFIT_CTGR_CD = 'compensation'
WHERE BENEFIT_CTGR_CD = 'financial'
  AND BENEFIT_CD IN ('bonus', 'stock', 'stock_option', 'stock_grant',
                     'profit_sharing', 'incentive', 'holiday_gift',
                     'excellence_award', 'long_service_award');

-- 2) TCOMPANY_BENEFIT: 나머지 financial → perks
UPDATE TCOMPANY_BENEFIT SET BENEFIT_CTGR_CD = 'perks'    WHERE BENEFIT_CTGR_CD = 'financial';
UPDATE TCOMPANY_BENEFIT SET BENEFIT_CTGR_CD = 'health'   WHERE BENEFIT_CTGR_CD = 'wellness';
UPDATE TCOMPANY_BENEFIT SET BENEFIT_CTGR_CD = 'leisure'  WHERE BENEFIT_CTGR_CD = 'life';
UPDATE TCOMPANY_BENEFIT SET BENEFIT_CTGR_CD = 'time_off' WHERE BENEFIT_CTGR_CD = 'time';
UPDATE TCOMPANY_BENEFIT SET BADGE_CD = 'est' WHERE BADGE_CD = 'auto';

-- 3) TBENEFIT_PRESET: 동일 규칙
UPDATE TBENEFIT_PRESET
SET BENEFIT_CTGR_CD = 'compensation'
WHERE BENEFIT_CTGR_CD = 'financial'
  AND BENEFIT_CD IN ('bonus', 'stock', 'stock_option', 'stock_grant',
                     'profit_sharing', 'incentive', 'holiday_gift',
                     'excellence_award', 'long_service_award');
UPDATE TBENEFIT_PRESET SET BENEFIT_CTGR_CD = 'perks'    WHERE BENEFIT_CTGR_CD = 'financial';
UPDATE TBENEFIT_PRESET SET BENEFIT_CTGR_CD = 'health'   WHERE BENEFIT_CTGR_CD = 'wellness';
UPDATE TBENEFIT_PRESET SET BENEFIT_CTGR_CD = 'leisure'  WHERE BENEFIT_CTGR_CD = 'life';
UPDATE TBENEFIT_PRESET SET BENEFIT_CTGR_CD = 'time_off' WHERE BENEFIT_CTGR_CD = 'time';
UPDATE TBENEFIT_PRESET SET BADGE_CD = 'est' WHERE BADGE_CD = 'auto';

-- 4) 스키마 COMMENT 도 정합성 위해 최신 9-카테고리로 교체
--    (schema.sql 은 이미 9-cat 이지만, 운영 DB 에 과거 COMMENT 가 남아있을 수 있음)
ALTER TABLE TCOMPANY_BENEFIT
  MODIFY COLUMN BENEFIT_CTGR_CD VARCHAR(20) NOT NULL
    COMMENT '복지 카테고리 (compensation, flexibility, work_env, time_off, health, family, growth, leisure, perks)';
ALTER TABLE TBENEFIT_PRESET
  MODIFY COLUMN BENEFIT_CTGR_CD VARCHAR(20) NOT NULL
    COMMENT '복지 카테고리 (compensation, flexibility, work_env, time_off, health, family, growth, leisure, perks)';

-- 검증 (관리자 수동 실행):
-- SELECT BENEFIT_CTGR_CD, COUNT(*) FROM TCOMPANY_BENEFIT GROUP BY BENEFIT_CTGR_CD;
-- SELECT BADGE_CD, COUNT(*) FROM TCOMPANY_BENEFIT GROUP BY BADGE_CD;
-- 기대: 9개 카테고리만, 뱃지는 est/official 만.
