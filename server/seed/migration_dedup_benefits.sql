-- Migration: 복지 중복 제거 및 UNIQUE 제약 추가
-- company_benefits 테이블에서 (company_id, ben_key) 중복 행 제거

-- 1) 중복 중 id가 큰(나중에 들어간) 행 삭제
DELETE cb1 FROM company_benefits cb1
INNER JOIN company_benefits cb2
  ON cb1.company_id = cb2.company_id
  AND cb1.ben_key = cb2.ben_key
  AND cb1.id > cb2.id;

-- 2) UNIQUE 제약 추가 (이미 있으면 무시)
ALTER TABLE company_benefits
  ADD UNIQUE KEY uq_company_ben (company_id, ben_key);
