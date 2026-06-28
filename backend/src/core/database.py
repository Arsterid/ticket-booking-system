from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine
)
from src.core.settings import get_settings


class DatabaseSessionFactory:
    def __init__(self):
        self._engine: AsyncEngine | None = None
        self._session_maker: async_sessionmaker[AsyncSession] | None = None

    def _init_if_needed(self) -> None:
        if self._engine is None:
            self._engine = create_async_engine(
                get_settings().db_url,
                echo=get_settings().sql_logs,
                pool_size=15,
                max_overflow=10,
            )

            self._session_maker = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

    def get_engine(self) -> AsyncEngine:
        self._init_if_needed()
        return self._engine

    def get_session_maker(self) -> async_sessionmaker[AsyncSession]:
        self._init_if_needed()
        return self._session_maker


db_factory = DatabaseSessionFactory()
