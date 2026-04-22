-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Migration: TMEMBER.VRFC_COMP_ID FK 제약 추가
-- Date: 2026-04-22
-- Plan: .omc/analysis/architecture-review-2026-04-22.md (BE #3 Medium — IDOR 방어 DB 근거)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 목적:
--   JWT 의 `cev` 클레임(검증된 회사 FK)은 `get_verified_user_for_comp` 미들웨어에서
--   Python 레벨로 IDOR 방어 중. 하지만 DB 에는 VRFC_COMP_ID 에 FK 제약이 없어
--   TCOMPANY 삭제 시 orphan 발생. ON DELETE SET NULL 로 정합성 보존.
--
-- 사전 조건: orphan 행이 없어야 함. 있으면 먼저 NULL 로 정리.
--   (2026-04-22 확인 시점: TMEMBER 1행, VRFC_COMP_ID IS NOT NULL 0건 — orphan 0)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- 1) 혹시 남아있을 orphan 선제 정리 (안전장치)
UPDATE TMEMBER m
  LEFT JOIN TCOMPANY c ON c.COMP_ID = m.VRFC_COMP_ID
  SET m.VRFC_COMP_ID = NULL
  WHERE m.VRFC_COMP_ID IS NOT NULL AND c.COMP_ID IS NULL;

-- 2) COMMENT 업데이트 (IDOR 방어 근거 명시)
ALTER TABLE TMEMBER
  MODIFY COLUMN VRFC_COMP_ID INT DEFAULT NULL
    COMMENT '회사 이메일로 인증된 회사 FK (tcompany.comp_id) — IDOR 방어 DB 근거';

-- 3) FK 제약 추가 (제약명 명시 — 롤백 용이)
ALTER TABLE TMEMBER
  ADD CONSTRAINT fk_tmember_vrfc_comp
  FOREIGN KEY (VRFC_COMP_ID) REFERENCES TCOMPANY(COMP_ID) ON DELETE SET NULL;

-- 검증:
-- SELECT CONSTRAINT_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME, DELETE_RULE
-- FROM information_schema.REFERENTIAL_CONSTRAINTS
-- WHERE CONSTRAINT_NAME = 'fk_tmember_vrfc_comp';
