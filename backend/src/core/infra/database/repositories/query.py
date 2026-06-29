from typing import Any, Generic, Literal, Optional, Union, overload, Sequence

from sqlalchemy import select, update, delete, func, exists

from src.core.annotations import ORM_MODEL_T, DTO_T
from src.core.infra.database.query_modifiers.base import BaseQueryModifier


class RepositoryQuery(Generic[ORM_MODEL_T, DTO_T]):
    def __init__(self, repo: Any):
        self._repo = repo
        self._filters: dict[str, Any] = {}
        self._order_by: Optional[str] = None
        self._options: list[Any] = []
        self._with_for_update: Union[bool, dict[str, Any]] = False

    def filter(self, **kwargs: Any) -> "RepositoryQuery[ORM_MODEL_T, DTO_T]":
        clone = RepositoryQuery(self._repo)
        clone._filters = {**self._filters, **kwargs}
        clone._order_by = self._order_by
        clone._options = [*self._options]
        clone._with_for_update = self._with_for_update
        return clone

    def order_by(self, field: Optional[str]) -> "RepositoryQuery[ORM_MODEL_T, DTO_T]":
        if not field:
            return self

        clone = RepositoryQuery(self._repo)
        clone._filters = {**self._filters}
        clone._order_by = field
        clone._options = [*self._options]
        clone._with_for_update = self._with_for_update
        return clone

    def options(self, *args: Any) -> "RepositoryQuery[ORM_MODEL_T, DTO_T]":
        clone = RepositoryQuery(self._repo)
        clone._filters = {**self._filters}
        clone._order_by = self._order_by
        clone._options = [*self._options, *args]
        clone._with_for_update = self._with_for_update
        return clone

    def with_for_update(self, set_val: Union[bool, dict[str, Any]] = True) -> "RepositoryQuery[ORM_MODEL_T, DTO_T]":
        clone = RepositoryQuery(self._repo)
        clone._filters = {**self._filters}
        clone._order_by = self._order_by
        clone._options = [*self._options]
        clone._with_for_update = set_val
        return clone

    async def _execute(self) -> tuple[Any, list[BaseQueryModifier]]:
        return self._repo._prepare_query(
            options=self._options,
            with_for_update=self._with_for_update,
            order_by=self._order_by,
            **self._filters
        )

    async def all(self) -> list[DTO_T]:
        q, modifiers = await self._execute()
        res = await self._repo._session.execute(q)
        items_raw = res.unique().all()
        return self._repo._to_dto(self._repo._process_results(items_raw, modifiers))

    async def first(self) -> Optional[DTO_T]:
        q, modifiers = await self._execute()
        res = await self._repo._session.execute(q)
        row = res.unique().one_or_none()
        if not row:
            return None
        return self._repo._to_dto(self._repo._process_results(row, modifiers))

    async def paginate(self, offset: int = 0, limit: int = 100) -> tuple[list[DTO_T], int]:
        q, modifiers = await self._execute()
        items_raw, total_count = await self._repo._execute_and_paginate_query(
            q=q,
            limit=limit,
            offset=offset
        )
        return self._repo._to_dto(self._repo._process_results(items_raw, modifiers)), total_count

    async def count(self) -> int:
        q, _ = await self._execute()
        count_q = select(func.count(self._repo.model.id)).select_from(q.subquery())
        result = await self._repo._session.execute(count_q)
        return result.scalar()

    async def exists(self) -> bool:
        q, _ = await self._execute()
        exist_q = select(exists(q.subquery()))
        result = await self._repo._session.execute(exist_q)
        return bool(result.scalar())

    @overload
    async def update(self, *, returning: Literal[True] = True, **kwargs: Any) -> list[DTO_T]:
        ...

    @overload
    async def update(self, *, returning: Literal[False], **kwargs: Any) -> int:
        ...

    @overload
    async def update(self, *, returning: Sequence[Any], **kwargs: Any) -> list[Any]:
        ...

    async def update(self, returning: Union[bool, Sequence[Any]] = True, **kwargs: Any) -> Union[
        list[DTO_T], int, list[Any]]:
        q, _ = await self._execute()
        update_q = update(self._repo.model).values(**kwargs)

        if q._where_criteria:
            update_q = update_q.where(*q._where_criteria)

        if returning is False:
            res = await self._repo._execute_modification(update_q)
            await self._repo._session.flush()
            return res.rowcount

        if returning is True:
            update_q = update_q.returning(self._repo.model)
            res = await self._repo._execute_modification(update_q)
            await self._repo._session.flush()
            return self._repo._to_dto(res.returning_scalars)

        update_q = update_q.returning(*returning)
        res = await self._repo._execute_modification(update_q)
        await self._repo._session.flush()
        return res.returning_rows

    async def delete(self) -> int:
        q, _ = await self._execute()
        delete_q = delete(self._repo.model)
        if q._where_criteria:
            delete_q = delete_q.where(*q._where_criteria)
        res = await self._repo._execute_modification(delete_q)
        await self._repo._session.flush()
        return res.rowcount
