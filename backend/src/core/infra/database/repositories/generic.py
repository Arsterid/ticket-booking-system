from abc import ABC
from typing import Any, Optional, Sequence, Type, overload, Literal, Union

from sqlalchemy import select, insert, delete, update, func, exists, Select, Update, Delete, Insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.interfaces import ORMOption

from src.core.annotations import ORM_MODEL_T, DTO_T
from src.core.infra.database.query_modifiers import BaseQueryModifier
from src.core.infra.database.repositories.data_objects import CreationResult, ModificationResult
from src.core.infra.database.repositories.mapper import RepositoryMapper
from src.core.infra.database.repositories.preparer import QueryPreparer


class GenericRepository(ABC, QueryPreparer[ORM_MODEL_T], RepositoryMapper[ORM_MODEL_T, DTO_T]):
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

    async def get(
        self,
        options: Sequence[Union[ORMOption, BaseQueryModifier]] | None = None,
        with_for_update: bool | dict[str, Any] = False,
        **kwargs: Any
    ) -> Optional[DTO_T]:
        q, modifiers = self._prepare_query(
            options=options,
            with_for_update=with_for_update,
            **kwargs
        )
        res = await self._session.execute(q)
        row = res.unique().one_or_none()
        if not row:
            return None
        return self._to_dto(self._process_results(row, modifiers))

    async def get_all(
        self,
        *,
        order_by: Optional[str] = None,
        options: Sequence[Union[ORMOption, BaseQueryModifier]] | None = None,
        with_for_update: bool | dict[str, Any] = False,
        **kwargs: Any
    ) -> list[DTO_T]:
        q, modifiers = self._prepare_query(
            order_by=order_by,
            options=options,
            with_for_update=with_for_update,
            **kwargs
        )
        res = await self._session.execute(q)
        items_raw = res.unique().all()
        return self._to_dto(self._process_results(items_raw, modifiers))

    async def paginate(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        options: Sequence[Union[ORMOption, BaseQueryModifier]] | None = None,
        with_for_update: bool | dict[str, Any] = False,
        **kwargs: Any
    ) -> tuple[list[DTO_T], int]:
        q, modifiers = self._prepare_query(
            order_by=order_by,
            options=options,
            with_for_update=with_for_update,
            **kwargs
        )
        items_raw, total_count = await self._execute_and_paginate_query(
            q=q,
            limit=limit,
            offset=offset
        )
        return self._to_dto(self._process_results(items_raw, modifiers)), total_count

    @overload
    async def create(self, mappings: list[dict[str, Any]]) -> list[DTO_T]:
        ...

    @overload
    async def create(self, **kwargs: Any) -> Optional[DTO_T]:
        ...

    async def create(self, m_data: Optional[list[dict[str, Any]]] = None, **kwargs: Any) -> Union[
        Optional[DTO_T], list[DTO_T]]:
        if m_data is not None:
            if not m_data:
                return []
            q = insert(self.model).values(m_data).returning(self.model)
            res = await self._execute_modification(q)
            await self._session.flush()
            return self._to_dto(res.returning_rows)

        obj = self.model(**kwargs)
        result = await self._execute_creation(obj)
        return result.dto

    @overload
    async def delete(self, obj_id: int) -> bool:
        ...

    @overload
    async def delete(self, obj_id: Union[set[int], list[int]]) -> int:
        ...

    async def delete(self, obj_id: Union[int, set[int], list[int]]) -> Union[bool, int]:
        if isinstance(obj_id, (set, list)):
            if not obj_id:
                return 0
            q = delete(self.model).where(self.model.id.in_(obj_id))
            res = await self._execute_modification(q)
            await self._session.flush()
            return res.rowcount

        q = delete(self.model).where(self.model.id == obj_id)
        res = await self._execute_modification(q)
        await self._session.flush()
        return res.rowcount > 0

    @overload
    async def update(
            self,
            data: dict[str, Any],
            *,
            returning_dto: Literal[True] = True,
            **kwargs: Any
    ) -> list[DTO_T]:
        ...

    @overload
    async def update(
            self,
            data: dict[str, Any],
            *,
            returning_dto: Literal[False],
            **kwargs: Any
    ) -> int:
        ...

    async def update(
            self,
            data: dict[str, Any],
            *,
            returning_dto: bool = True,
            **kwargs: Any
        ) -> list[DTO_T] | int:
        if not kwargs:
            raise ValueError("Update operation requires at least one filter to prevent accidental global changes.")

        q, _ = self._prepare_query(**kwargs)

        update_q = update(self.model).values(**data)
        if q._where_criteria:
            update_q = update_q.where(*q._where_criteria)

        if not returning_dto:
            res = await self._execute_modification(update_q)
            await self._session.flush()
            return res.rowcount

        update_q = update_q.returning(self.model)
        res = await self._execute_modification(update_q)
        await self._session.flush()

        return self._to_dto(res.returning_scalars)

    async def count(self, **filters: Any) -> int:
        q, _ = self._prepare_query(filters=filters)
        count_q = select(func.count(self.model.id)).select_from(q.subquery())
        result = await self._session.execute(count_q)
        return result.scalar()

    async def exists(self, **filters: Any) -> bool:
        if not filters:
            return False

        q, _ = self._prepare_query(filters=filters)
        q = select(exists(q.subquery()))
        result = await self._session.execute(q)
        return bool(result.scalar())

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

    async def _execute_and_paginate_query(
            self,
            q: Select[tuple[Any, ...]],
            *,
            offset: int = 0,
            limit: int = 100,
    ) -> tuple[list[Any], int]:
        count_q = select(func.count()).select_from(q.subquery())
        total_result = await self._session.execute(count_q)
        total_count = total_result.scalar_one()

        paginated_q = q.offset(offset).limit(limit)
        result = await self._session.execute(paginated_q)

        items = list(result.unique().all())

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
