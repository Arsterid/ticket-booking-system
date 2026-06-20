import inspect
from typing import Any, get_type_hints, Type, get_origin

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from src.common.repositories import GenericRepository
from src.common.uow.units.abstract import AbstractUnitOfWork


class SQLAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.session: AsyncSession | None = None
        self._repositories: dict[str, Any] = {}

        self._validate_annotations()

    def _validate_annotations(self) -> None:
        hints = get_type_hints(self.__class__)
        seen_repo_classes: set[Type] = set()

        for attr_name, attr_type in hints.items():
            if get_origin(attr_type) is not None:
                raise TypeError(
                    f"Invalid annotation in {self.__class__.__name__}.{attr_name}: "
                    f"Using Generic types like 'Repository[Model]' is forbidden. "
                    f"Please specify a concrete repository class."
                )

            if not inspect.isclass(attr_type):
                raise TypeError(
                    f"Invalid annotation in {self.__class__.__name__}.{attr_name}: "
                    f"The type hint must be a clean class. "
                    f"Using Union, Optional, or '| None' is forbidden."
                )

            if attr_type is GenericRepository or not issubclass(attr_type, GenericRepository):
                raise TypeError(
                    f"Invalid annotation in {self.__class__.__name__}.{attr_name}: "
                    f"Class '{attr_type.__name__}' must strictly inherit from 'GenericRepository'."
                )

            if attr_type in seen_repo_classes:
                raise ValueError(
                    f"Invalid configuration in {self.__class__.__name__}: "
                    f"Repository class '{attr_type.__name__}' is already assigned to another attribute."
                )

            seen_repo_classes.add(attr_type)

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        if self.session is not None:
            raise RuntimeError("Database session is already active in this context.")
        self.session = self.session_factory()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.session:
            try:
                if exc_type:
                    await self.session.rollback()
                else:
                    await self.session.commit()
            finally:
                await self.session.close()
                self.session = None
                self._repositories.clear()

    def __getattr__(self, name: str) -> Any:
        if name in self._repositories:
            return self._repositories[name]

        hints = get_type_hints(self.__class__)
        if name not in hints:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

        if self.session is None:
            raise RuntimeError(
                f"Attempted to access repository '{name}' outside of a transaction context. "
                f"Please use 'async with uow:'"
            )

        repo_cls = hints[name]
        repo_instance = repo_cls(self.session)

        self._repositories[name] = repo_instance
        return repo_instance

    async def commit(self):
        if self.session:
            await self.session.commit()

    async def rollback(self):
        if self.session:
            await self.session.rollback()

    async def refresh(self, *args, **kwargs):
        if self.session:
            await self.session.refresh(*args, **kwargs)
