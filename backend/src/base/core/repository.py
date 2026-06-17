from abc import ABC
from typing import Type, Generic, Optional, Sequence, Union, Any

from sqlalchemy import select, exists, func, Select
from sqlalchemy.ext.asyncio import AsyncSession

from src.base.annotations import ModelType


class GenericRepository(ABC, Generic[ModelType]):
    _registry: dict[str, Type['GenericRepository']] = {}

    model: Type[ModelType]
    id_field: str = "id"

    def __init__(self, session: AsyncSession):
        self.session = session

    def __init_subclass__(cls, model: Type[ModelType] = None, **kwargs):
        super().__init_subclass__(**kwargs)

        if model is not None:
            cls.model = model
            repo_key = model.__name__.lower()
            GenericRepository._registry[repo_key] = cls

    @property
    def model_name(self):
        return self.model.__name__.lower() or "unnamed table"

    def _get_model_id_field(self):
        try:
            return getattr(self.model, self.id_field)
        except AttributeError:
            raise AssertionError(f"Field {self.id_field} not found in {self.model.__name__}")

    async def create(self, **kwargs) -> ModelType:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def get_by_id(self, obj_id: Union[str, int]) -> Optional[ModelType]:
        if self.id_field == "id":
            return await self.session.get(self.model, obj_id)

        q = select(self.model).where(self._get_model_id_field() == obj_id)
        result = await self.session.execute(q)
        return result.scalar()

    async def exists(self, obj_id: Union[str, int]) -> bool:
        q = select(exists().where(self._get_model_id_field() == obj_id))
        result = await self.session.execute(q)
        return result.scalar()

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        q = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(q)
        return result.scalars().all()

    async def _execute_and_paginate_query(
            self,
            q: Select[tuple[Any, ...]],
            offset: int = 0,
            limit: int = 100,
    ) -> tuple[list[ModelType], int]:
        count_q = select(func.count()).select_from(q.subquery())
        total_result = await self.session.execute(count_q)
        total_count = total_result.scalar_one()

        paginated_q = q.offset(offset).limit(limit)
        result = await self.session.execute(paginated_q)
        items = list(result.scalars().all())

        return items, total_count
