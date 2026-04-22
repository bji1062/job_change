"""공용 Literal 타입 정의 — 코드성 컬럼의 허용값을 Pydantic 레벨에서 강제.

ENUM 을 쓰지 않는 규약(CLAUDE.md)을 유지하면서, 오타/잘못된 값은 API 경계에서 400 으로 거부.
새 값을 추가할 때는:
  1) schema.sql 의 COMMENT 에 값을 먼저 추가
  2) 여기 Literal 에 추가
  3) 필요 시 DB 마이그레이션 (기존 행에 신규 값 backfill)
"""
from typing import Literal

# 복지 카테고리 (9종) — schema.sql TCOMPANY_BENEFIT.BENEFIT_CTGR_CD COMMENT 와 동기화
BenefitCtgrCd = Literal[
    "compensation", "flexibility", "work_env", "time_off",
    "health", "family", "growth", "leisure", "perks",
]

# 데이터 신뢰도 뱃지 (2종) — schema.sql TCOMPANY_BENEFIT.BADGE_CD COMMENT 와 동기화
BadgeCd = Literal["est", "official"]

# 데이터 출처 (5종) — 2026-04-22 badge 운영 전략 Phase 1 신규
# schema.sql TCOMPANY_BENEFIT.BADGE_SRC_CD COMMENT 와 동기화
BadgeSrcCd = Literal[
    "scrape_official",
    "scrape_fallback",
    "ai_parse",
    "manual",
    "user_report",
]

# 기업유형 (6종) — TCOMPANY_TYPE.COMP_TP_CD 기준, CLAUDE.md 에 명시
CompTpCd = Literal["large", "startup", "mid", "foreign", "public", "freelance"]

# 사용자 역할 (2종) — TMEMBER.ROLE_CD
RoleCd = Literal["user", "admin"]

# Popular case 유형 (2종) — TPOPULAR_CASE.CASE_TYPE_CD
CaseTypeCd = Literal["company", "scenario"]

# Feed metric 방향 (3종) — TCOMPARISON_FEED.METRIC_TYPE_CD
MetricTypeCd = Literal["up", "down", "neu"]
