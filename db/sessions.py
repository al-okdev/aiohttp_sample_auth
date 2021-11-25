from contextlib import asynccontextmanager
from typing import ContextManager

from db.db_models import Base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


@asynccontextmanager
async def get_async_session(
    dsn: str, drop: bool = False, create: bool = False
) -> ContextManager[AsyncSession]:
    engine = create_async_engine(dsn)
    async with engine.begin() as conn:
        if drop:
            await conn.run_sync(Base.metadata.drop_all)
        if create:
            await conn.run_sync(Base.metadata.create_all)
    async_session_maker = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    yield async_session_maker

    await engine.dispose()
