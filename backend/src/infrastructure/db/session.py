"""Para cuando se necesita levantar una sesión manualmente con sessionmaker"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from contextlib import asynccontextmanager, contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.config.settings import env_vars



sync_engine = create_engine(env_vars.url_db_sync)
engine = create_async_engine(env_vars.url_db)

SyncSessionLocal = sessionmaker(bind=sync_engine, future=True)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

@asynccontextmanager
async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session

@contextmanager
def get_sync_db_session():
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()