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
    """comparison_feed, popular_cases, daily_stats 테이블이 없으면 자동 생성."""
    ddl = [
        """CREATE TABLE IF NOT EXISTS comparison_feed (
          id BIGINT AUTO_INCREMENT PRIMARY KEY,
          comparison_id BIGINT NOT NULL,
          job_category VARCHAR(30),
          company_a_display VARCHAR(100),
          type_a VARCHAR(20) NOT NULL,
          company_b_display VARCHAR(100),
          type_b VARCHAR(20) NOT NULL,
          headline VARCHAR(300) NOT NULL,
          detail VARCHAR(500),
          metric_val VARCHAR(30),
          metric_label VARCHAR(30),
          metric_type VARCHAR(10) DEFAULT 'neu',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (comparison_id) REFERENCES comparisons(id) ON DELETE CASCADE,
          INDEX idx_feed_created (created_at DESC)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
        """CREATE TABLE IF NOT EXISTS daily_stats (
          stat_date DATE PRIMARY KEY,
          comparison_count INT DEFAULT 0
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
        """CREATE TABLE IF NOT EXISTS popular_cases (
          id INT AUTO_INCREMENT PRIMARY KEY,
          case_type VARCHAR(20) NOT NULL,
          title_a VARCHAR(50) NOT NULL,
          type_a VARCHAR(20) NOT NULL,
          sub_a VARCHAR(30),
          title_b VARCHAR(50) NOT NULL,
          type_b VARCHAR(20) NOT NULL,
          sub_b VARCHAR(30),
          points JSON,
          view_count INT DEFAULT 0,
          comparison_count INT DEFAULT 0,
          is_active BOOLEAN DEFAULT TRUE,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          INDEX idx_active_count (is_active, comparison_count DESC)
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
