import aiomysql
import pymysql
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
          TITLE_A_NM VARCHAR(50) NOT NULL,
          TYPE_A_CD VARCHAR(20) NOT NULL,
          SUB_A_NM VARCHAR(30),
          TITLE_B_NM VARCHAR(50) NOT NULL,
          TYPE_B_CD VARCHAR(20) NOT NULL,
          SUB_B_NM VARCHAR(30),
          POINTS_VAL JSON,
          VIEW_NO INT DEFAULT 0,
          COMPARISON_NO INT DEFAULT 0,
          ACTIVE_YN BOOLEAN DEFAULT TRUE,
          INS_ID INT,
          INS_DTM TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          MOD_ID INT,
          MOD_DTM TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
          INDEX idx_active_comparison (ACTIVE_YN, COMPARISON_NO DESC)
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
