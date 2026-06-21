from abc import ABC
from dataclasses import fields
from typing import Type, Generic, Optional, Sequence, Any, Callable

from sqlalchemy import select, exists, func, Select, BinaryExpression, desc, asc, Update, Delete, Insert, inspect
from sqlalchemy.exc import IntegrityError, ResourceClosedError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.interfaces import ORMOption

from src.common.annotations import ModelType, DTOType
from src.common.data_objects import ModificationResult, CreationResult


class GenericRepository(ABC, Generic[ModelType, DTOType]):
    _OPERATORS: dict[str, Callable[[Any, Any], BinaryExpression]] = {
        "eq": lambda col, val: col == val,
        "ne": lambda col, val: col != val,
        "gte": lambda col, val: col >= val,
        "lte": lambda col, val: col <= val,
        "gt": lambda col, val: col > val,
        "lt": lambda col, val: col < val,
        "in": lambda col, val: col.in_(val),
        "ilike": lambda col, val: col.ilike(f"%{val}%"),
        "has_any": lambda col, val: col.any(),
        "has_no": lambda col, val: ~col.any(),
    }

    model: Type[ModelType]
    dto: Type[DTOType]

    def __init__(self, session: AsyncSession):
        self._session = session

    def __init_subclass__(cls, model: Type[ModelType] = None, dto: Type[DTOType] = None, **kwargs):
        super().__init_subclass__(**kwargs)

        if model is not None:
            cls.model = model
        if dto is not None:
            cls.dto = dto

    @property
    def model_name(self):
        return self.model.__name__.lower() or "unnamed table"

    def _to_dto(self, obj_orm: ModelType) -> DTOType:
        allowed_fields = {f.name for f in fields(self.dto)}
        mapper = inspect(obj_orm).mapper

        hybrid_fields = {
            attr.__name__ for attr in mapper.all_orm_descriptors
            if isinstance(attr, hybrid_property)
        }

        loaded_data = {}
        for f in allowed_fields:
            if f in obj_orm.__dict__:
                loaded_data[f] = obj_orm.__dict__[f]
            elif f in hybrid_fields:
                loaded_data[f] = getattr(obj_orm, f)

        return self.dto(**loaded_data)

    async def create(self, **kwargs: Any) -> Optional[DTOType]:
        obj = self.model(**kwargs)
        result = await self._execute_creation(obj)

        return result.dto

    async def get(
            self,
            options: Sequence[ORMOption] | None = None,
            with_for_update: bool = False,
            **filters: Any
    ) -> Optional[DTOType]:
        q = select(self.model)

        if filters:
            q = self._build_filtered_query(q, filters)

        if options is not None:
            q = q.options(*options)

        if with_for_update:
            q = q.with_for_update()

        result = await self._session.execute(q)
        obj_orm = result.scalar_one_or_none()

        if not obj_orm:
            return None

        return self._to_dto(obj_orm)

    async def get_or_create(self, **kwargs: Any) -> tuple[DTOType, bool]:
        obj_dto = await self.get(**kwargs)
        if obj_dto is not None:
            return obj_dto, False

        instance = self.model(**kwargs)

        try:
            async with self._session.begin_nested():
                result = await self._execute_creation(instance)

                if result.success and result.dto is not None:
                    return result.dto, True

                raise ValueError("Failed to create instance within get_or_create.")

        except (IntegrityError, ValueError):
            obj_dto = await self.get(**kwargs)

            if obj_dto is not None:
                return obj_dto, False

            raise

    async def exists(self, **filters: Any) -> bool:
        if not filters:
            return False

        q = select(self.model)
        q = self._build_filtered_query(q, filters)
        q = select(exists(q.subquery()))

        result = await self._session.execute(q)
        return bool(result.scalar())

    async def get_all(
            self,
            offset: int = 0,
            limit: int = 100,
            filters: dict[str, Any] | None = None,
            order_by: str | None = None,
            *,
            options: Sequence[ORMOption] | None = None,
    ) -> tuple[list[DTOType], int]:
        q = select(self.model)
        if options is not None:
            q = q.options(*options)

        if filters:
            q = self._build_filtered_query(q, filters)

        if order_by:
            q = self._apply_sorting(q, order_by)

        items_orm, total_count = await self._execute_and_paginate_query(
            q=q,
            limit=limit,
            offset=offset,
        )

        items_dto = [self._to_dto(item) for item in items_orm]
        return items_dto, total_count

    def _build_filtered_query(self, query: select, filters: dict[str, Any]) -> select:
        for key, value in filters.items():
            if value is not None:
                query = self._apply_filter(query, key, value)
        return query

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

        raise ValueError(f"Invalid sort field '{field_name}' for model {self.model.__name__}")

    async def _execute_and_paginate_query(
            self,
            q: Select[tuple[Any, ...]],
            offset: int = 0,
            limit: int = 100,
    ) -> tuple[list[ModelType], int]:
        count_q = select(func.count()).select_from(q.subquery())
        total_result = await self._session.execute(count_q)
        total_count = total_result.scalar_one()

        paginated_q = q.offset(offset).limit(limit)
        result = await self._session.execute(paginated_q)

        items = list(result.scalars().unique().all())

        return items, total_count

    async def _execute_modification(self, q: Update | Delete | Insert) -> ModificationResult:
        try:
            conn = await self._session.connection()
            res = await conn.execute(q)

            returning_rows = list(res.all()) if res.returns_rows else []
            rowcount = res.rowcount

            return ModificationResult(
                rowcount=rowcount,
                returning_rows=returning_rows
            )
        except IntegrityError:
            return ModificationResult(rowcount=0, returning_rows=[])

    async def _execute_creation(self, instance: ModelType) -> CreationResult[DTOType]:
        try:
            self._session.add(instance)
            await self._session.flush()
            await self._session.refresh(instance)

            dto_obj = self._to_dto(instance)
            return CreationResult(dto=dto_obj)
        except IntegrityError:
            return CreationResult(dto=None)
