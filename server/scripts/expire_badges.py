"""만료된 official 배지를 est 로 강등하고 TCOMPANY_BENEFIT_BADGE_LOG 에 기록.

실행: systemd timer (jobchoice-expire-badges.timer, 일 1회 03:00)
수동 실행: python3 server/scripts/expire_badges.py

동작:
  - BADGE_CD='official' AND EXPIRES_DTM <= NOW() 인 행을 est 로 강등
  - 강등 시 VERIFIED_DTM / VERIFIED_BY_ID / EXPIRES_DTM 는 유지 (언제 누가 공식화했는지 기록 보존)
  - BADGE_LOG 에 'demote' 행 추가 (ACTOR_MBR_ID=NULL — 시스템 cron)

exit code: 성공=0, DB 오류=1
stdout: 강등 건수 한 줄 (모니터링용 — journalctl 에서 grep)
"""
import logging
import os
import sys
from pathlib import Path

import pymysql

# 서버 루트를 import path 에 추가 (config 모듈 재사용)
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

import config  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s expire_badges: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def main() -> int:
    conn = pymysql.connect(
        host=config.DB_HOST, port=config.DB_PORT,
        user=config.DB_USER, password=config.DB_PASS,
        database=config.DB_NAME, charset="utf8mb4",
        autocommit=False,
    )
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(
                """SELECT BENEFIT_ID AS benefit_id, BADGE_CD AS badge_cd
                   FROM TCOMPANY_BENEFIT
                   WHERE BADGE_CD='official' AND EXPIRES_DTM IS NOT NULL AND EXPIRES_DTM <= NOW()"""
            )
            rows = cur.fetchall()
            if not rows:
                log.info("no expired badges — nothing to do")
                print("expired=0")
                return 0

            ids = [r["benefit_id"] for r in rows]
            log.info("demoting %d badges: %s", len(ids), ids[:10])

            # UPDATE 루프 — 건수가 커야 수백 단위라 IN 절이면 충분. 원자성 위해 트랜잭션.
            placeholders = ",".join(["%s"] * len(ids))
            cur.execute(
                f"UPDATE TCOMPANY_BENEFIT SET BADGE_CD='est' WHERE BENEFIT_ID IN ({placeholders})",
                ids,
            )
            log_rows = [(bid, None, "demote", "official", "est", "TTL 만료 — 자동 강등") for bid in ids]
            cur.executemany(
                """INSERT INTO TCOMPANY_BENEFIT_BADGE_LOG
                   (BENEFIT_ID, ACTOR_MBR_ID, ACTION_CD, FROM_BADGE_CD, TO_BADGE_CD, NOTE_CTNT)
                   VALUES (%s,%s,%s,%s,%s,%s)""",
                log_rows,
            )
            conn.commit()
            log.info("demoted %d badges, logs written", len(ids))
            print(f"expired={len(ids)}")
            return 0
    except Exception as e:
        conn.rollback()
        log.exception("expire_badges failed: %s", e)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
