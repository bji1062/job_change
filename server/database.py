import logging

import aiomysql
import pymysql
from contextlib import asynccontextmanager
from decimal import Decimal
import config

logger = logging.getLogger(__name__)

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
    # DDL 은 seed/schema.sql 및 seed/migrations/ 를 단일 소스로 한다.
    # (이전에 있던 _ensure_tables() 는 drift 근원이라 2026-04-22 제거됨 — 분석 리포트 BE #2)

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
