from contextlib import asynccontextmanager
import aiomysql
from fastapi import HTTPException
from core.config import settings

pool: aiomysql.Pool = None

async def init_db_pool():
    global pool
    try:
        pool = await aiomysql.create_pool(
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            db=settings.DB_NAME,
            minsize=settings.DB_MIN_POOL,
            maxsize=settings.DB_MAX_POOL,
            autocommit=True
        )
    except aiomysql.MySQLError as err:
        print(f"Warning: Connection pool init failed: {err}")

async def close_db_pool():
    global pool
    if pool:
        pool.close()
        await pool.wait_closed()

@asynccontextmanager
async def get_db():
    global pool
    if pool is None:
        try:
            conn = await aiomysql.connect(
                host=settings.DB_HOST,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                db=settings.DB_NAME,
                autocommit=True
            )
            try:
                yield conn
            finally:
                conn.close()
            return
        except aiomysql.MySQLError as err:
            raise HTTPException(status_code=500, detail=f"Database connection error: {err}")

    async with pool.acquire() as conn:
        yield conn
