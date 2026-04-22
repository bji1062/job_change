-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Migration: TBENEFIT_REPORT — 사용자 값 틀림 제보
-- Date: 2026-04-23
-- Plan: .omc/analysis/resume-2026-04-23.md (P5-3)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 목적:
--   복지 금액/내용이 잘못됐다는 사용자 제보를 저장하여 관리자 검수 큐에 노출.
--   제보가 쌓인 항목은 신뢰도 하향 신호로 활용 (추후 가중 랭킹).
--
-- 외래키:
--   - BENEFIT_ID: TCOMPANY_BENEFIT CASCADE (복지 삭제 시 제보도 삭제)
--   - REPORTER_MBR_ID: TMEMBER SET NULL (비로그인 제보 허용, 사용자 탈퇴 시 제보는 보존)
--   - RESOLVED_BY_ID: TMEMBER SET NULL (관리자 탈퇴 시 해결 이력은 보존)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE TABLE IF NOT EXISTS TBENEFIT_REPORT (
  REPORT_ID INT AUTO_INCREMENT PRIMARY KEY COMMENT '제보 PK',
  BENEFIT_ID INT NOT NULL COMMENT '복지항목 FK (tcompany_benefit.benefit_id)',
  REPORTER_MBR_ID INT DEFAULT NULL COMMENT '제보자 FK (tmember.mbr_id) — NULL 은 비로그인 제보',
  REPORT_TYPE_CD VARCHAR(20) NOT NULL COMMENT '제보 유형 (wrong_amount: 금액 오류, outdated: 제도 변경됨, missing_field: 누락)',
  REPORTED_AMT INT DEFAULT NULL COMMENT '제보자가 주장하는 올바른 금액 (만원, wrong_amount 일 때)',
  COMMENT_CTNT VARCHAR(500) DEFAULT NULL COMMENT '제보 사유/추가 설명',
  STATUS_CD VARCHAR(10) NOT NULL DEFAULT 'open' COMMENT '처리 상태 (open: 검수 대기, resolved: 반영, rejected: 기각)',
  RESOLVED_BY_ID INT DEFAULT NULL COMMENT '처리한 관리자 FK (tmember.mbr_id)',
  RESOLVED_DTM DATETIME DEFAULT NULL COMMENT '처리 일시',
  RESOLVE_NOTE_CTNT VARCHAR(500) DEFAULT NULL COMMENT '관리자 처리 메모',
  INS_DTM TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '제보 일시',
  FOREIGN KEY (BENEFIT_ID) REFERENCES TCOMPANY_BENEFIT(BENEFIT_ID) ON DELETE CASCADE,
  FOREIGN KEY (REPORTER_MBR_ID) REFERENCES TMEMBER(MBR_ID) ON DELETE SET NULL,
  FOREIGN KEY (RESOLVED_BY_ID) REFERENCES TMEMBER(MBR_ID) ON DELETE SET NULL,
  INDEX idx_status_ins (STATUS_CD, INS_DTM),
  INDEX idx_benefit_ins (BENEFIT_ID, INS_DTM)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 검증:
-- SELECT STATUS_CD, COUNT(*) FROM TBENEFIT_REPORT GROUP BY STATUS_CD;
