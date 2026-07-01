from typing import Any, Generic, Literal, Optional, overload, Sequence, Type, Union

from sqlalchemy import delete, exists, func, inspect, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.core.annotations import DTO_T, ORM_MODEL_T
from src.core.infra.database.query_modifiers.base import BaseQueryModifier
from .expressions import F


class RepositoryQuery(Generic[ORM_MODEL_T, DTO_T]):
    def __init__(self, repo: Any):
        self._repo = repo
        self._filters: dict[str, Any] = {}
        self._order_by: Optional[str] = None
        self._options: list[Any] = []
        self._with_for_update: Union[bool, dict[str, Any]] = False
        self._context_history: list[tuple[Type[Any], Any]] = []

    def filter(self, **kwargs: Any) -> "RepositoryQuery[ORM_MODEL_T, DTO_T]":
        clone = self._clone()
        clone._filters = {**self._filters, **kwargs}
        return clone

    def order_by(self, field: Optional[str]) -> "RepositoryQuery[ORM_MODEL_T, DTO_T]":
        if not field:
            return self
        clone = self._clone()
        clone._order_by = field
        return clone

    def options(self, *args: Any) -> "RepositoryQuery[ORM_MODEL_T, DTO_T]":
        clone = self._clone()
        clone._options = [*self._options, *args]
        return clone

    def with_for_update(self, set_val: Union[bool, dict[str, Any]] = True) -> "RepositoryQuery[ORM_MODEL_T, DTO_T]":
        clone = self._clone()
        if set_val is True:
            current_model = clone._get_current_model()
            clone._with_for_update = {"of": current_model}
        else:
            clone._with_for_update = set_val
        return clone

    def __getattr__(self, name: str) -> "RepositoryQuery[Any, Any]":
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        current_model = self._get_current_model()
        if not hasattr(current_model, name):
            raise AttributeError(f"'{current_model.__name__}' object has no attribute '{name}'")

        attr = getattr(current_model, name)
        try:
            prop = inspect(attr).property
            from sqlalchemy.orm.properties import RelationshipProperty
            if not isinstance(prop, RelationshipProperty):
                raise AttributeError()
        except Exception:
            raise AttributeError(f"'{current_model.__name__}' attribute '{name}' is not a relationship")

        target_model = prop.mapper.class_
        clone = self._clone()

        q, _ = clone._repo._prepare_query(
            options=clone._options,
            with_for_update=clone._with_for_update,
            order_by=clone._order_by,
            **clone._filters
        )

        clone._context_history.append((current_model, q))
        clone._target_model = target_model
        clone._prop_meta = prop

        clone._filters = {}
        clone._order_by = None
        clone._options = []
        clone._with_for_update = False
        return clone

    def _get_current_model(self):
        return self.__dict__.get("_target_model", self._repo.model)

    def _clone(self) -> "RepositoryQuery[ORM_MODEL_T, DTO_T]":
        clone = RepositoryQuery(self._repo)
        clone._filters = {**self._filters}
        clone._order_by = self._order_by
        clone._options = [*self._options]
        clone._with_for_update = self._with_for_update
        clone._context_history = [*self._context_history]
        if "_target_model" in self.__dict__:
            clone._target_model = self._target_model
            clone._prop_meta = self._prop_meta
        return clone

    def _build_final_criteria(self, base_stmt: Any) -> Any:
        if not self._context_history:
            return base_stmt

        current_stmt = base_stmt
        history = list(self._context_history)

        target_prop = self._prop_meta
        parent_model, parent_query = history[-1]

        local_col = target_prop.local_columns.copy().pop()
        remote_col = target_prop.remote_side.copy().pop()

        subq = parent_query.subquery()

        if remote_col.table == self._get_current_model().__table__:
            current_stmt = current_stmt.where(remote_col.in_(select(getattr(subq.c, local_col.name))))
        else:
            current_stmt = current_stmt.where(local_col.in_(select(getattr(subq.c, remote_col.name))))

        return current_stmt

    async def _execute(self) -> tuple[Any, list[BaseQueryModifier]]:
        current_model = self._get_current_model()
        if not hasattr(self, "_target_model"):
            return self._repo._prepare_query(
                options=self._options,
                with_for_update=self._with_for_update,
                order_by=self._order_by,
                **self._filters
            )

        q = select(current_model)
        if self._filters:
            q = self._repo._build_filtered_query(q, self._filters)
        if self._order_by:
            q = self._repo._apply_sorting(q, self._order_by)

        q = self._build_final_criteria(q)
        return q, []

    def with_joined(self, *relations: str) -> "RepositoryQuery[ORM_MODEL_T, DTO_T]":
        from sqlalchemy.orm import joinedload
        clone = self._clone()
        current_model = clone._get_current_model()

        options = []
        for rel in relations:
            parts = rel.split("__")
            model_attr = getattr(current_model, parts[0])
            opt = joinedload(model_attr)

            parent_model = current_model
            for part in parts[1:]:
                prop = inspect(getattr(parent_model, parts[0])).property
                parent_model = prop.mapper.class_
                next_attr = getattr(parent_model, part)
                opt = opt.joinedload(next_attr)

            options.append(opt)

        clone._options = [*self._options, *options]
        return clone

    def with_selectin(self, *relations: str) -> "RepositoryQuery[ORM_MODEL_T, DTO_T]":
        from sqlalchemy.orm import selectinload
        clone = self._clone()
        current_model = clone._get_current_model()

        options = []
        for rel in relations:
            parts = rel.split("__")
            model_attr = getattr(current_model, parts[0])
            opt = selectinload(model_attr)

            parent_model = current_model
            for part in parts[1:]:
                prop = inspect(getattr(parent_model, parts[0])).property
                parent_model = prop.mapper.class_
                next_attr = getattr(parent_model, part)
                opt = opt.joinedload(next_attr)

            options.append(opt)

        clone._options = [*self._options, *options]
        return clone

    @overload
    async def create(
            self,
            m_data: list[dict[str, Any]],
            *,
            on_conflict_do_nothing: bool = False,
            index_elements: Optional[list[str]] = None
    ) -> list[Any]:
        ...

    @overload
    async def create(
            self,
            *,
            on_conflict_do_nothing: bool = False,
            index_elements: Optional[list[str]] = None,
            **kwargs: Any
    ) -> Optional[Any]:
        ...

    async def create(
            self,
            m_data: Optional[list[dict[str, Any]]] = None,
            *,
            on_conflict_do_nothing: bool = False,
            index_elements: Optional[list[str]] = None,
            **kwargs: Any
    ) -> Union[Optional[Any], list[Any]]:
        current_model = self._get_current_model()
        raw_items = m_data if m_data is not None else [kwargs]

        if not raw_items:
            return [] if m_data is not None else None

        if self._filters:
            for item in raw_items:
                for filter_key, filter_val in self._filters.items():
                    if "__" not in filter_key and filter_key not in item:
                        item[filter_key] = filter_val

        if self._context_history:
            target_prop = self._prop_meta
            local_col = target_prop.local_columns.copy().pop()
            remote_col = target_prop.remote_side.copy().pop()

            parent_filters = self._context_history[-1][1]._where_criteria
            parent_id_val = None
            for criterion in parent_filters:
                if hasattr(criterion, "left") and hasattr(criterion, "right"):
                    if criterion.left.name == local_col.name:
                        parent_id_val = criterion.right.value
                        break

            if parent_id_val is not None:
                fk_field_name = remote_col.name if remote_col.table == current_model.__table__ else local_col.name
                for item in raw_items:
                    if fk_field_name not in item:
                        item[fk_field_name] = parent_id_val

        stmt = pg_insert(current_model).values(raw_items)

        if on_conflict_do_nothing:
            if index_elements:
                stmt = stmt.on_conflict_do_nothing(index_elements=index_elements)
            else:
                stmt = stmt.on_conflict_do_nothing()

        stmt = stmt.returning(current_model)

        mod_res = await self._repo._execute_modification(stmt)
        dtos = self._repo._to_dto(mod_res.returning_rows)

        if m_data is not None:
            return dtos

        if isinstance(dtos, list):
            return dtos[0] if len(dtos) > 0 else None
        return dtos

    async def get(self, **kwargs: Any) -> Any:
        clone = self.filter(**kwargs) if kwargs else self
        q, modifiers = await clone._execute()

        res = await clone._repo._session.execute(q)

        if not hasattr(clone, "_target_model"):
            rows = res.unique().scalars().all()
        else:
            rows = res.unique().all()

        if not rows:
            raise ValueError(f"No {clone._get_current_model().__name__} found matching the criteria.")
        if len(rows) > 1:
            raise ValueError(f"Multiple {clone._get_current_model().__name__} returned matching the criteria.")

        row = rows[0]

        if not hasattr(clone, "_target_model"):
            return clone._repo._to_dto(clone._repo._process_results(row, modifiers))
        return row

    async def all(self) -> list[Any]:
        q, modifiers = await self._execute()
        res = await self._repo._session.execute(q)

        if not hasattr(self, "_target_model"):
            items_raw = res.unique().scalars().all()
            return self._repo._to_dto(self._repo._process_results(items_raw, modifiers))

        items_raw = res.unique().all()
        return items_raw

    async def first(self) -> Optional[Any]:
        q, modifiers = await self._execute()
        res = await self._repo._session.execute(q)

        if not hasattr(self, "_target_model"):
            row = res.unique().scalar_one_or_none()
            if not row:
                return None
            return self._repo._to_dto(self._repo._process_results(row, modifiers))

        row = res.unique().one_or_none()
        return row

    async def paginate(self, offset: int = 0, limit: int = 100) -> tuple[list[Any], int]:
        q, modifiers = await self._execute()

        if not hasattr(self, "_target_model"):
            count_q = select(func.count()).select_from(q.subquery())
            total_result = await self._repo._session.execute(count_q)
            total_count = total_result.scalar_one()

            paginated_q = q.offset(offset).limit(limit)
            result = await self._repo._session.execute(paginated_q)
            items_raw = list(result.unique().scalars().all())

            return self._repo._to_dto(self._repo._process_results(items_raw, modifiers)), total_count

        items_raw, total_count = await self._repo._execute_and_paginate_query(q=q, limit=limit, offset=offset)
        return items_raw, total_count

    async def count(self, **kwargs: Any) -> int:
        clone = self.filter(**kwargs) if kwargs else self
        q, _ = await clone._execute()
        count_q = select(func.count()).select_from(q.subquery())
        result = await clone._repo._session.execute(count_q)
        return result.scalar()

    async def exists(self, **kwargs: Any) -> bool:
        clone = self.filter(**kwargs) if kwargs else self
        q, _ = await clone._execute()
        exist_q = select(exists(q.subquery()))
        result = await clone._repo._session.execute(exist_q)
        return bool(result.scalar())

    @overload
    async def update(self, *, returning: Literal[True] = True, **kwargs: Any) -> Optional[DTO_T]:
        ...

    @overload
    async def update(self, *, returning: Literal[False], **kwargs: Any) -> int:
        ...

    @overload
    async def update(self, *, returning: Sequence[Any], **kwargs: Any) -> list[Any]:
        ...

    async def update(self, returning: Union[bool, Sequence[Any]] = True, **kwargs: Any) -> Union[
        Optional[DTO_T], int, list[Any]]:
        current_model = self._get_current_model()
        q, _ = await self._execute()

        update_values = {}
        for k, v in kwargs.items():
            if isinstance(v, F):
                update_values[k] = v.resolve(current_model)
            else:
                update_values[k] = v

        update_q = update(current_model).values(**update_values)
        if q._where_criteria:
            update_q = update_q.where(*q._where_criteria)

        if returning is False:
            res = await self._repo._execute_modification(update_q)
            await self._repo._session.flush()
            return res.rowcount

        if returning is True and not hasattr(self, "_target_model"):
            update_q = update_q.returning(current_model)
            res = await self._repo._execute_modification(update_q)
            await self._repo._session.flush()
            if not res.returning_rows:
                return None
            dto_list = self._repo._to_dto(res.returning_rows)
            return dto_list[0] if isinstance(dto_list, list) and len(dto_list) > 0 else dto_list

        if returning is True:
            update_q = update_q.returning(current_model)
        else:
            update_q = update_q.returning(*returning)

        res = await self._repo._execute_modification(update_q)
        await self._repo._session.flush()
        return res.returning_rows

    async def delete(self) -> int:
        current_model = self._get_current_model()
        q, _ = await self._execute()

        delete_q = delete(current_model)
        if q._where_criteria:
            delete_q = delete_q.where(*q._where_criteria)

        res = await self._repo._execute_modification(delete_q)
        await self._repo._session.flush()
        return res.rowcount
