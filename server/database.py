import aiomysql
import pymysql
import config

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

async def close_pool():
    global pool
    if pool:
        pool.close()
        await pool.wait_closed()

async def fetch_all(sql, args=None):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql, args)
            return await cur.fetchall()

async def fetch_one(sql, args=None):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql, args)
            return await cur.fetchone()

async def execute(sql, args=None):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, args)
            return cur.lastrowid
