from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from src.common.repositories import GenericRepository
from src.common.uow.units.abstract import AbstractUnitOfWork


class SQLAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.session: AsyncSession | None = None
        self._repositories = {}

    async def __aenter__(self):
        self.session = self.session_factory()
        self._repositories = {}
        return self

    def __getattr__(self, name: str) -> GenericRepository:
        repo_class = GenericRepository._registry.get(name)

        if not repo_class:
            raise AttributeError(f"Repository '{name}' is not registered anywhere in the system.")

        if name not in self._repositories:
            self._repositories[name] = repo_class(self.session)

        return self._repositories[name]

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        if self.session:
            await self.session.close()

    async def commit(self):
        if self.session:
            await self.session.commit()

    async def rollback(self):
        if self.session:
            await self.session.rollback()
