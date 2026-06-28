from abc import ABC
from dataclasses import fields
from typing import Any, Callable, Generic, Optional, Sequence, Type, overload, Literal

from sqlalchemy import BinaryExpression, Delete, Insert, Select, Update, asc, desc, exists, func, inspect, select, \
    update, insert, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm.interfaces import ORMOption

from src.core.annotations import DTO_T, ORM_MODEL_T
from src.core.infra.database.repositories.data_objects import CreationResult, ModificationResult


class GenericRepository(ABC, Generic[ORM_MODEL_T, DTO_T]):
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

    model: Type[ORM_MODEL_T]
    dto: Type[DTO_T]

    def __init__(self, session: AsyncSession):
        self._session = session

    def __init_subclass__(cls, model: Type[ORM_MODEL_T] = None, dto: Type[DTO_T] = None, **kwargs):
        super().__init_subclass__(**kwargs)

        if model is not None:
            cls.model = model
        if dto is not None:
            cls.dto = dto

    @classmethod
    def get_model_name(cls):
        return cls.model.__tablename__.lower() if getattr(cls.model, "__tablename__",
                                                          None) else cls.model.__name__.lower()

    async def create(self, **kwargs: Any) -> Optional[DTO_T]:
        obj = self.model(**kwargs)
        result = await self._execute_creation(obj)

        return result.dto

    async def bulk_create(self, mappings: list[dict[str, Any]]) -> list[DTO_T]:
        if not mappings:
            return []

        q = insert(self.model).values(mappings).returning(self.model)
        res = await self._execute_modification(q)

        await self._session.flush()

        return [self._to_dto(row) for row in res.returning_rows]

    @overload
    async def update(
            self,
            *,
            filters: dict[str, Any],
            returning_dto: Literal[True] = True,
            **kwargs: Any
    ) -> list[DTO_T]:
        ...

    @overload
    async def update(
            self,
            *,
            filters: dict[str, Any],
            returning_dto: Literal[False],
            **kwargs: Any
    ) -> int:
        ...

    async def update(
            self,
            *,
            filters: dict[str, Any],
            returning_dto: bool = True,
            **kwargs: Any
    ) -> list[DTO_T] | int:
        if not filters:
            raise ValueError("Update operation requires at least one filter to prevent accidental global changes.")

        update_q = update(self.model).values(**kwargs)
        update_q = self._build_filtered_query(update_q, filters)

        if not returning_dto:
            res = await self._execute_modification(update_q)
            await self._session.flush()
            return res.rowcount

        update_q = update_q.returning(self.model)
        res = await self._execute_modification(update_q)
        await self._session.flush()

        return [self._to_dto(obj) for obj in res.returning_scalars]

    async def get(
            self,
            options: Sequence[ORMOption] | None = None,
            with_for_update: bool | dict[str, Any] = False,
            **filters: Any
    ) -> Optional[DTO_T]:
        q = select(self.model)

        if filters:
            q = self._build_filtered_query(q, filters)

        if options is not None:
            q = q.options(*options)

        if with_for_update:
            if isinstance(with_for_update, dict):
                q = q.with_for_update(**with_for_update)
            else:
                q = q.with_for_update()

        res = await self._session.execute(q)
        obj_orm: ORM_MODEL_T = res.scalars().unique().one_or_none()

        if not obj_orm:
            return None

        return self._to_dto(obj_orm)

    async def get_or_create(self, **kwargs: Any) -> tuple[DTO_T, bool]:
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

    async def get_all(
            self,
            *,
            with_for_update: bool | dict[str, Any] = False,
            filters: dict[str, Any] | None = None,
            order_by: str | None = None,
            options: Sequence[ORMOption] | None = None,
    ) -> list[DTO_T]:
        q = select(self.model)
        if options is not None:
            q = q.options(*options)

        if with_for_update:
            if isinstance(with_for_update, dict):
                q = q.with_for_update(**with_for_update)
            else:
                q = q.with_for_update()

        if filters:
            q = self._build_filtered_query(q, filters)

        if order_by:
            q = self._apply_sorting(q, order_by)

        res = await self._session.execute(q)
        items_orm = res.scalars().unique().all()

        return [self._to_dto(item) for item in items_orm]

    async def get_all_with_pagination(
            self,
            *,
            with_for_update: bool | dict[str, Any] = False,
            filters: dict[str, Any] | None = None,
            offset: int = 0,
            limit: int = 100,
            order_by: str | None = None,
            options: Sequence[ORMOption] | None = None,
    ) -> tuple[list[DTO_T], int]:
        q = select(self.model)
        if options is not None:
            q = q.options(*options)

        if with_for_update:
            if isinstance(with_for_update, dict):
                q = q.with_for_update(**with_for_update)
            else:
                q = q.with_for_update()

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

    async def delete(self, obj_id: int) -> bool:
        q = (
            delete(self.model)
            .where(self.model.id == obj_id)
        )
        res = await self._execute_modification(q)
        await self._session.flush()
        return res.rowcount > 0

    async def bulk_delete(self, obj_ids: set[int]) -> int:
        if not obj_ids:
            return 0

        q = (
            delete(self.model)
            .where(self.model.id.in_(obj_ids))
        )
        res = await self._execute_modification(q)
        await self._session.flush()
        return res.rowcount

    def _to_dto(self, obj_orm: ORM_MODEL_T) -> DTO_T:
        allowed_fields = {f.name for f in fields(self.dto)}
        insp = inspect(obj_orm)
        mapper = insp.mapper

        hybrid_fields = {attr.__name__ for attr in mapper.all_orm_descriptors if isinstance(attr, hybrid_property)}

        loaded_data = {}
        for f in allowed_fields:
            if f in mapper.relationships:
                if f not in insp.unloaded:
                    loaded_data[f] = getattr(obj_orm, f)
            elif f in obj_orm.__dict__:
                loaded_data[f] = obj_orm.__dict__[f]
            elif f in hybrid_fields:
                loaded_data[f] = getattr(obj_orm, f)

        return self.dto(**loaded_data)

    async def count(
            self, **filters: Any
    ) -> int:
        q = select(func.count(self.model.id))

        if filters:
            q = self._build_filtered_query(q, filters)

        result = await self._session.execute(q)

        return result.scalar()

    async def exists(self, **filters: Any) -> bool:
        if not filters:
            return False

        q = select(self.model)
        q = self._build_filtered_query(q, filters)
        q = select(exists(q.subquery()))

        result = await self._session.execute(q)
        return bool(result.scalar())

    def _build_filtered_query(self, query: select, filters: dict[str, Any]) -> select:
        joined_models = set()
        for key, value in filters.items():
            if value is not None:
                query = self._apply_filter(query, key, value, joined_models)
        return query

    def _apply_filter(self, query: select, key: str, value: Any, joined_models: set) -> select:
        path, operator = key.split("__", 1) if "__" in key else (key, "eq")

        if operator not in self._OPERATORS:
            return query

        parts = path.split(".")
        field_name = parts.pop()

        current_model = self.model

        eager_option = None

        for relation_name in parts:
            if hasattr(current_model, relation_name):
                relation_attr = getattr(current_model, relation_name)

                if hasattr(relation_attr, "property") and hasattr(relation_attr.property, "mapper"):
                    target_model = relation_attr.property.mapper.class_

                    if target_model not in joined_models:
                        query = query.join(relation_attr)

                        if eager_option is None:
                            eager_option = contains_eager(relation_attr)
                        else:
                            eager_option = eager_option.contains_eager(relation_attr)

                        query = query.options(eager_option)
                        joined_models.add(target_model)
                    else:
                        if eager_option is None:
                            eager_option = contains_eager(relation_attr)
                        else:
                            eager_option = eager_option.contains_eager(relation_attr)

                    current_model = target_model
                else:
                    current_model = relation_attr
            else:
                return query

        if hasattr(current_model, field_name):
            column = getattr(current_model, field_name)
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
            *,
            offset: int = 0,
            limit: int = 100,
    ) -> tuple[list[ORM_MODEL_T], int]:
        count_q = select(func.count()).select_from(q.subquery())
        total_result = await self._session.execute(count_q)
        total_count = total_result.scalar_one()

        paginated_q = q.offset(offset).limit(limit)
        result = await self._session.execute(paginated_q)

        items = list(result.scalars().unique().all())

        return items, total_count

    async def _execute_modification(self, q: Update | Delete | Insert) -> ModificationResult:
        try:
            res = await self._session.execute(q)

            rowcount = getattr(res, "rowcount", 0)

            try:
                has_returns = bool(res.keys())
            except Exception:
                has_returns = False

            returning_rows = list(res.all()) if has_returns else []

            if rowcount is None or rowcount == -1:
                rowcount = len(returning_rows)

            return ModificationResult(rowcount=rowcount, returning_rows=returning_rows)
        except IntegrityError:
            return ModificationResult(rowcount=0, returning_rows=[])

    async def _execute_creation(self, instance: ORM_MODEL_T) -> CreationResult[DTO_T]:
        try:
            self._session.add(instance)
            await self._session.flush()
            await self._session.refresh(instance)

            dto_obj = self._to_dto(instance)
            return CreationResult(dto=dto_obj)
        except IntegrityError:
            return CreationResult(dto=None)
