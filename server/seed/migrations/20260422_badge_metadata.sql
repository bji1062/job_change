-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Migration: badge=est 운영 전략 — Phase 1 메타 컬럼 추가
-- Date: 2026-04-22
-- Plan: .omc/analysis/architecture-review-2026-04-22.md (badge=est 섹션)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 목적:
--   기존 BADGE_CD('est'/'official') 단일 컬럼으로는 아래를 구분할 수 없음:
--     1) 출처(Provenance): 공식 페이지 vs 집계 사이트 vs AI 파싱 vs 수동
--     2) 신선도(Freshness): 언제 재확인했는가
--     3) 만료(Expiry): 언제까지 유효한가
--   Phase 1에서는 데이터 저장 구조만 갖추고, 만료 cron/검수 UI는 후속 단계(P4-3, P5-3).
--
-- 영향: 신규 컬럼은 모두 NULL 허용 + DEFAULT NULL 이므로 기존 INSERT 구문 호환.
--       기존 행은 BADGE_SRC_CD='ai_parse' (보수적 가정) 으로 backfill.
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ALTER TABLE TCOMPANY_BENEFIT
  ADD COLUMN BADGE_SRC_CD VARCHAR(20) DEFAULT NULL
    COMMENT '데이터 출처 (scrape_official, scrape_fallback, ai_parse, manual, user_report)'
    AFTER BADGE_CD,
  ADD COLUMN BADGE_SRC_URL_CTNT VARCHAR(500) DEFAULT NULL
    COMMENT '출처 URL (공식 페이지 스크래핑 시)'
    AFTER BADGE_SRC_CD,
  ADD COLUMN VERIFIED_DTM DATETIME DEFAULT NULL
    COMMENT '마지막 출처 재확인 시점 (INS/MOD_DTM과 별개, badge 신선도 기준)'
    AFTER BADGE_SRC_URL_CTNT,
  ADD COLUMN VERIFIED_BY_ID INT DEFAULT NULL
    COMMENT '검증자 FK (tmember.mbr_id) — 관리자 수동 승격 추적'
    AFTER VERIFIED_DTM,
  ADD COLUMN EXPIRES_DTM DATETIME DEFAULT NULL
    COMMENT '유효 만료 시점 (VERIFIED_DTM + category별 TTL, 초과 시 재검증 필요)'
    AFTER VERIFIED_BY_ID;

-- 기존 행 backfill: 출처 불명 → 보수적으로 ai_parse 로 기록
UPDATE TCOMPANY_BENEFIT
SET BADGE_SRC_CD = 'ai_parse'
WHERE BADGE_SRC_CD IS NULL;

-- 검증 (관리자가 수동으로 실행):
-- SELECT BADGE_CD, BADGE_SRC_CD, COUNT(*) FROM TCOMPANY_BENEFIT GROUP BY BADGE_CD, BADGE_SRC_CD;
