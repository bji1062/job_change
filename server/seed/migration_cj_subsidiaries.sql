-- ============================================================
-- CJ 계열사 분리 + 별칭 중복 제거 마이그레이션
-- ============================================================
-- 실행 순서:
--   mysql -u root jobchoice < server/seed/migration_cj_subsidiaries.sql
-- ============================================================

-- 1. 기존 company_aliases 중복 제거 (가장 작은 id만 남김)
DELETE ca1 FROM company_aliases ca1
INNER JOIN company_aliases ca2
  ON ca1.company_id = ca2.company_id
  AND ca1.alias = ca2.alias
  AND ca1.id > ca2.id;

-- 2. company_aliases UNIQUE 제약 추가 (중복 재발 방지)
ALTER TABLE company_aliases
  ADD UNIQUE KEY uq_company_alias (company_id, alias);

-- 3. CJ그룹에서 계열사 별칭 제거
DELETE FROM company_aliases
WHERE company_id = 'cj'
  AND alias IN ('CJ제일제당', 'CJ올리브영', 'CJ ENM');

-- 4. CJ그룹 자체 별칭 보강 (누락된 것이 있을 경우)
INSERT IGNORE INTO company_aliases (company_id, alias) VALUES
  ('cj', 'CJ'),
  ('cj', 'cj'),
  ('cj', '씨제이'),
  ('cj', 'CJ주식회사');

-- 5. CJ 계열사를 별도 회사로 추가
INSERT IGNORE INTO companies (id, name, type_id, industry, logo, work_style, careers_benefit_url) VALUES
  ('cj_cheiljedang', 'CJ제일제당', 'large', '식품/바이오', 'CJ',
    '{"remote": false, "flex": false, "unlimitedPTO": false, "overtime": "일반적 대기업 수준"}',
    'https://recruit.cj.net/'),
  ('cj_enm', 'CJ ENM', 'large', '엔터/미디어', 'CE',
    '{"remote": false, "flex": true, "unlimitedPTO": false, "overtime": "콘텐츠 제작 특성상 변동 큼"}',
    'https://recruit.cj.net/'),
  ('cj_oliveyoung', 'CJ올리브영', 'large', '유통/뷰티', 'OY',
    '{"remote": false, "flex": false, "unlimitedPTO": false, "overtime": "일반적 대기업 수준"}',
    'https://recruit.cj.net/');

-- 6. 계열사 별칭 추가
INSERT IGNORE INTO company_aliases (company_id, alias) VALUES
  ('cj_cheiljedang', 'CJ제일제당'),
  ('cj_cheiljedang', '제일제당'),
  ('cj_cheiljedang', 'cj_cheiljedang'),
  ('cj_enm', 'CJ ENM'),
  ('cj_enm', 'CJ이엔엠'),
  ('cj_enm', 'cj_enm'),
  ('cj_enm', 'tvN'),
  ('cj_enm', '티빙'),
  ('cj_oliveyoung', 'CJ올리브영'),
  ('cj_oliveyoung', '올리브영'),
  ('cj_oliveyoung', 'cj_oliveyoung'),
  ('cj_oliveyoung', 'oliveyoung');

-- 7. 결과 확인
SELECT c.id, c.name, COUNT(ca.id) AS alias_count
FROM companies c
LEFT JOIN company_aliases ca ON ca.company_id = c.id
WHERE c.id LIKE 'cj%'
GROUP BY c.id, c.name;
