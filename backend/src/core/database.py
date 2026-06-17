from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from src.core.settings import AppConfig

settings = AppConfig()

engine = create_async_engine(
    settings.db_url,
    echo=True,
    pool_size=15,
    max_overflow=10,
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
