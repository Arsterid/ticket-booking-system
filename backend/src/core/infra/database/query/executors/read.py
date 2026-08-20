from typing import Any, Optional

from sqlalchemy import exists, func, select


class ReadQueryExecutor:
    @staticmethod
    async def get(query: Any, **kwargs: Any) -> Any:
        clone = query.filter(**kwargs) if kwargs else query
        q, modifiers = await clone._execute()
        res = await clone._repo._session.execute(q)

        if not hasattr(clone, "_target_model"):
            rows = res.unique().scalars().all()
        else:
            rows = res.unique().all()

        if not rows:
            raise ValueError(f"No {clone._get_current_model().__name__} found matching criteria.")
        if len(rows) > 1:
            raise ValueError(f"Multiple {clone._get_current_model().__name__} returned matching criteria.")

        single_row = rows[0]

        if not hasattr(clone, "_target_model"):
            processed = clone._repo._process_results(single_row, modifiers)
            return clone._to_dto(processed)

        return clone._to_dto(single_row)

    @staticmethod
    async def all(query: Any) -> list[Any]:
        q, modifiers = await query._execute()
        res = await query._repo._session.execute(q)

        if not hasattr(query, "_target_model"):
            items_raw = res.unique().scalars().all()
            return query._to_dto(query._repo._process_results(items_raw, modifiers))

        items_raw = res.unique().all()
        return query._to_dto(items_raw)

    @staticmethod
    async def first(query: Any) -> Optional[Any]:
        q, modifiers = await query._execute()
        res = await query._repo._session.execute(q)

        if not hasattr(query, "_target_model"):
            row = res.unique().scalars().first()
            if not row:
                return None
            return query._to_dto(query._repo._process_results(row, modifiers))

        rows = res.unique().all()
        if not rows:
            return None
        return query._to_dto(rows[0])

    @staticmethod
    async def paginate(query: Any, offset: int = 0, limit: int = 100) -> tuple[list[Any], int]:
        q, modifiers = await query._execute()
        items_raw, total_count = await query._repo._execute_and_paginate_query(
            q=q, offset=offset, limit=limit
        )

        if not hasattr(query, "_target_model"):
            processed_items = query._repo._process_results(items_raw, modifiers)
            return query._to_dto(processed_items), total_count
        return query._to_dto(items_raw), total_count


    @staticmethod
    async def count(query: Any, **kwargs: Any) -> int:
        clone = query.filter(**kwargs) if kwargs else query
        q, _ = await clone._execute()
        count_q = select(func.count()).select_from(q.subquery())
        result = await clone._repo._session.execute(count_q)
        return result.scalar()

    @staticmethod
    async def exists(query: Any, **kwargs: Any) -> bool:
        clone = query.filter(**kwargs) if kwargs else query
        q, _ = await clone._execute()
        exist_q = select(exists(q.subquery()))
        result = await clone._repo._session.execute(exist_q)
        return bool(result.scalar())
