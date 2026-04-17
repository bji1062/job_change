import aiomysql
import pymysql
from contextlib import asynccontextmanager
from decimal import Decimal
import config

def _convert_row(row):
    """Convert Decimal values to float for JSON serialization."""
    if row is None:
        return None
    return {k: float(v) if isinstance(v, Decimal) else v for k, v in row.items()}

pool = None

async def init_pool():
    global pool
    pool = await aiomysql.create_pool(
        host=config.DB_HOST, port=config.DB_PORT,
        user=config.DB_USER, password=config.DB_PASS,
        db=config.DB_NAME, charset="utf8mb4",
        autocommit=True, minsize=2, maxsize=10,
        auth_plugin="mysql_native_password",
    )
    await _ensure_tables()

async def _ensure_tables():
    """TCOMPARISON_FEED, TPOPULAR_CASE, TDAILY_STAT 테이블이 없으면 자동 생성."""
    ddl = [
        """CREATE TABLE IF NOT EXISTS TCOMPARISON_FEED (
          FEED_ID INT AUTO_INCREMENT PRIMARY KEY,
          COMPARISON_ID INT NOT NULL,
          JOB_CTGR_NM VARCHAR(30),
          COMP_A_DISP_NM VARCHAR(100),
          COMP_A_TP_CD VARCHAR(20) NOT NULL,
          COMP_B_DISP_NM VARCHAR(100),
          COMP_B_TP_CD VARCHAR(20) NOT NULL,
          HEADLINE_CTNT VARCHAR(300) NOT NULL,
          DETAIL_CTNT VARCHAR(500),
          METRIC_VAL_CTNT VARCHAR(30),
          METRIC_LABEL_NM VARCHAR(30),
          METRIC_TYPE_CD VARCHAR(10) DEFAULT 'neu',
          INS_ID INT,
          INS_DTM TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          MOD_ID INT,
          MOD_DTM TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
          FOREIGN KEY (COMPARISON_ID) REFERENCES TCOMPARISON(COMPARISON_ID) ON DELETE CASCADE,
          INDEX idx_feed_ins (INS_DTM DESC)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
        """CREATE TABLE IF NOT EXISTS TDAILY_STAT (
          STAT_DT DATE PRIMARY KEY,
          COMPARISON_NO INT DEFAULT 0,
          INS_ID INT,
          INS_DTM TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          MOD_ID INT,
          MOD_DTM TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
        """CREATE TABLE IF NOT EXISTS TPOPULAR_CASE (
          CASE_ID INT AUTO_INCREMENT PRIMARY KEY,
          CASE_TYPE_CD VARCHAR(20) NOT NULL,
          CURRENT_COMP_NM VARCHAR(50) NOT NULL,
          CURRENT_COMP_TP_CD VARCHAR(20) NOT NULL,
          CURRENT_SUB_NM VARCHAR(30),
          OFFER_COMP_NM VARCHAR(50) NOT NULL,
          OFFER_COMP_TP_CD VARCHAR(20) NOT NULL,
          OFFER_SUB_NM VARCHAR(30),
          POINTS_VAL JSON,
          VIEW_NO INT DEFAULT 0,
          COMPARISON_NO INT DEFAULT 0,
          ACTIVE_YN BOOLEAN DEFAULT TRUE,
          INS_ID INT,
          INS_DTM TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          MOD_ID INT,
          MOD_DTM TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
          INDEX idx_active_comparison (ACTIVE_YN, COMPARISON_NO DESC),
          UNIQUE KEY uq_case_pair (CASE_TYPE_CD, CURRENT_COMP_NM, OFFER_COMP_NM)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    ]
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            for sql in ddl:
                try:
                    await cur.execute(sql)
                except Exception as e:
                    print(f"[_ensure_tables] {e}")

async def close_pool():
    global pool
    if pool:
        pool.close()
        await pool.wait_closed()

async def fetch_all(sql, args=None):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql, args)
            rows = await cur.fetchall()
            return [_convert_row(r) for r in rows]

async def fetch_one(sql, args=None):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql, args)
            return _convert_row(await cur.fetchone())

async def execute(sql, args=None):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, args)
            return cur.lastrowid


@asynccontextmanager
async def transaction():
    """원자적 다중 쿼리용 트랜잭션 컨텍스트.

    사용 예:
        async with database.transaction() as tx:
            await tx.execute("DELETE ...", (id,))
            await tx.executemany("INSERT ...", rows)

    풀의 autocommit=True를 일시적으로 꺼 BEGIN/COMMIT/ROLLBACK을 수동 관리한다.
    컨텍스트 블록 내부 예외 발생 시 전체 rollback.
    """
    async with pool.acquire() as conn:
        await conn.begin()
        try:
            async with conn.cursor() as cur:
                tx = _Tx(cur)
                yield tx
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise


class _Tx:
    """transaction() 블록 내부에서 사용하는 경량 래퍼 — 같은 커서로 다중 쿼리 실행."""

    def __init__(self, cur):
        self._cur = cur

    async def execute(self, sql, args=None):
        await self._cur.execute(sql, args)
        return self._cur.lastrowid

    async def executemany(self, sql, rows):
        await self._cur.executemany(sql, rows)
        return self._cur.lastrowid
