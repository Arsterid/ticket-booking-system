import re
from abc import ABC
from typing import Type, Generic, Optional, Sequence, Union, Any, Callable

from sqlalchemy import select, exists, func, Select, BinaryExpression, desc, asc, Update, Delete, Insert, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.interfaces import ORMOption

from src.common.annotations import ModelType


class GenericRepository(ABC, Generic[ModelType]):
    _OPERATORS: dict[str, Callable[[Any, Any], BinaryExpression]] = {
        "eq": lambda col, val: col == val,
        "ne": lambda col, val: col != val,
        "gte": lambda col, val: col >= val,
        "lte": lambda col, val: col <= val,
        "gt": lambda col, val: col > val,
        "lt": lambda col, val: col < val,
        "in": lambda col, val: col.in_(val),
        "ilike": lambda col, val: col.ilike(f"%{val}%"),
    }

    model: Type[ModelType]
    id_field: str = "id"

    def __init__(self, session: AsyncSession):
        self.session = session

    def __init_subclass__(cls, model: Type[ModelType] = None, **kwargs):
        super().__init_subclass__(**kwargs)

        if model is not None:
            cls.model = model

    @property
    def model_name(self):
        return self.model.__name__.lower() or "unnamed table"

    def _get_model_id_field(self):
        try:
            return getattr(self.model, self.id_field)
        except AttributeError:
            raise AssertionError(f"Field {self.id_field} not found in {self.model.__name__}")

    async def create(self, **kwargs) -> Optional[ModelType]:
        obj = self.model(**kwargs)
        self.session.add(obj)
        return await self._execute_creation(obj)

    async def get_by_id(
            self,
            obj_id: Union[str, int],
            options: Sequence[ORMOption] | None = None,
    ) -> Optional[ModelType]:
        q = select(self.model).where(self._get_model_id_field() == obj_id)
        if options is not None:
            q = q.options(*options)
        result = await self.session.execute(q)
        return result.scalar()

    async def exists(self, obj_id: Union[str, int]) -> bool:
        q = select(exists().where(self._get_model_id_field() == obj_id))
        result = await self.session.execute(q)
        return result.scalar()

    async def get_all(
            self,
            offset: int = 0,
            limit: int = 100,
            filters: dict[str, Any] | None = None,
            order_by: str | None = None,
            *,
            options: Sequence[ORMOption] | None = None,
    ) -> tuple[list[ModelType], int]:
        q = select(self.model)
        if options is not None:
            q = q.options(*options)

        if filters:
            for key, value in filters.items():
                if value is not None:
                    q = self._apply_filter(q, key, value)

        if order_by:
            q = self._apply_sorting(q, order_by)

        return await self._execute_and_paginate_query(
            q=q,
            limit=limit,
            offset=offset,
        )

    def _apply_filter(self, query: select, key: str, value: Any) -> select:
        field_name, operator = key.split("__", 1) if "__" in key else (key, "eq")

        if hasattr(self.model, field_name) and operator in self._OPERATORS:
            column = getattr(self.model, field_name)
            return query.where(self._OPERATORS[operator](column, value))

        return query

    def _apply_sorting(self, query: select, order_by: str) -> select:
        if order_by.startswith("-"):
            field_name = order_by[1:]
            direction = desc
        else:
            field_name = order_by
            direction = asc

        if hasattr(self.model, field_name):
            column = getattr(self.model, field_name)
            return query.order_by(direction(column))

        return query

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

        items = list(result.scalars().unique().all())

        return items, total_count

    async def _execute_modification(self, q: Update | Delete) -> int:
        try:
            res = await self.session.execute(q)
            return res.rowcount
        except IntegrityError:
            return 0

    async def _execute_creation(self, instance: ModelType) -> Optional[ModelType]:
        try:
            await self.session.flush()
            await self.session.refresh(instance)
            return instance
        except IntegrityError:
            await self.session.rollback()
            return None

    async def _execute_insert(self, q: Insert) -> Any | None:
        try:
            res = await self.session.execute(q)
            return res.scalar()
        except IntegrityError:
            return None

