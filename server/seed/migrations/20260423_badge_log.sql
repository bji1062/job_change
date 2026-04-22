-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Migration: TCOMPANY_BENEFIT_BADGE_LOG — 배지 승격/강등 감사 로그
-- Date: 2026-04-23
-- Plan: .omc/analysis/resume-2026-04-23.md (P4-3)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 목적:
--   관리자 est→official 승격, 만료 cron 의 official→est 강등, 수동 verify 재검증을
--   추적 가능한 감사 로그로 남긴다. 신뢰도 복원/분쟁 대응용.
--
-- 사용 흐름:
--   - PUT /admin/benefits/{id}/promote → services/benefit_service.promote_to_official() → 이 테이블에 insert
--   - scripts/expire_badges.py (P5-3) → VERIFIED_DTM+TTL 초과 시 demote + insert
--
-- 외래키 정책:
--   - BENEFIT_ID: TCOMPANY_BENEFIT 삭제 시 로그도 CASCADE (복지 자체가 사라지면 로그도 무의미)
--   - ACTOR_MBR_ID: TMEMBER 삭제 시 SET NULL (시스템 cron 주체는 NULL 로 기록, 사용자 탈퇴 시 로그는 보존)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE TABLE IF NOT EXISTS TCOMPANY_BENEFIT_BADGE_LOG (
  LOG_ID INT AUTO_INCREMENT PRIMARY KEY COMMENT '로그 PK',
  BENEFIT_ID INT NOT NULL COMMENT '복지항목 FK (tcompany_benefit.benefit_id)',
  ACTOR_MBR_ID INT DEFAULT NULL COMMENT '주체 FK (tmember.mbr_id) — NULL 은 시스템 cron',
  ACTION_CD VARCHAR(10) NOT NULL COMMENT '액션 유형 (promote: est→official, demote: official→est, verify: 재검증 연장)',
  FROM_BADGE_CD VARCHAR(10) DEFAULT NULL COMMENT '변경 전 배지 (est, official)',
  TO_BADGE_CD VARCHAR(10) DEFAULT NULL COMMENT '변경 후 배지 (est, official)',
  NOTE_CTNT VARCHAR(500) DEFAULT NULL COMMENT '승격/강등 사유 (관리자 메모, cron 자동 메시지)',
  INS_DTM TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '기록 일시',
  FOREIGN KEY (BENEFIT_ID) REFERENCES TCOMPANY_BENEFIT(BENEFIT_ID) ON DELETE CASCADE,
  FOREIGN KEY (ACTOR_MBR_ID) REFERENCES TMEMBER(MBR_ID) ON DELETE SET NULL,
  INDEX idx_benefit_ins (BENEFIT_ID, INS_DTM),
  INDEX idx_actor_ins (ACTOR_MBR_ID, INS_DTM)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 검증 (관리자가 수동으로 실행):
-- SELECT ACTION_CD, COUNT(*) FROM TCOMPANY_BENEFIT_BADGE_LOG GROUP BY ACTION_CD;
