-- Migration: 복지 카테고리 통일 (money/health/housing/edu/leave → financial/work_env/wellness/growth/time)
-- 현대자동차·삼성전자 기준 카테고리에 맞춰 CJ·토스·프리셋 카테고리 업데이트
SET NAMES utf8mb4;

-- ━━ 1. company_benefits 카테고리 업데이트 ━━

-- CJ: money → work_env/financial
UPDATE company_benefits SET category='work_env'  WHERE company_id='cj' AND ben_key IN ('meal', 'commute_sup');
UPDATE company_benefits SET category='financial' WHERE company_id='cj' AND ben_key IN ('cafe_point', 'event', 'housing');
UPDATE company_benefits SET category='wellness'  WHERE company_id='cj' AND ben_key IN ('health', 'medical', 'fitness');
UPDATE company_benefits SET category='growth'    WHERE company_id='cj' AND ben_key='lang';
UPDATE company_benefits SET category='life'      WHERE company_id='cj' AND ben_key='resort';
UPDATE company_benefits SET category='time'      WHERE company_id='cj' AND ben_key='creative_leave';

-- Toss: money → work_env/financial
UPDATE company_benefits SET category='work_env'  WHERE company_id='toss' AND ben_key IN ('meal', 'salon', 'cafe', 'hardware');
UPDATE company_benefits SET category='financial' WHERE company_id='toss' AND ben_key IN ('fitness_comm', 'housing');
UPDATE company_benefits SET category='wellness'  WHERE company_id='toss' AND ben_key='insurance';
UPDATE company_benefits SET category='growth'    WHERE company_id='toss' AND ben_key='edu';
UPDATE company_benefits SET category='time'      WHERE company_id='toss' AND ben_key IN ('flex', 'unlimited_pto', 'refresh');

-- ━━ 2. benefit_presets 카테고리 업데이트 ━━

-- money → work_env (식대, 교통비)
UPDATE benefit_presets SET category='work_env' WHERE ben_key IN ('meal', 'transport');

-- money → financial (복지포인트, 성과급, 경조사, 스톡옵션)
UPDATE benefit_presets SET category='financial' WHERE ben_key IN ('welfare', 'bonus', 'event', 'stock');

-- health → wellness
UPDATE benefit_presets SET category='wellness' WHERE category='health';

-- housing → financial
UPDATE benefit_presets SET category='financial' WHERE category='housing';

-- edu → growth
UPDATE benefit_presets SET category='growth' WHERE category='edu';
