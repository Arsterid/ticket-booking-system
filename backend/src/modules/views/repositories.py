from typing import Any, Optional, Union, overload
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.core.infra.database.repositories import GenericRepository
from src.modules.views.data_objects import ViewLogDTO
from src.modules.views.models import ViewLog


class ViewLogRepository(GenericRepository[ViewLog, ViewLogDTO], model=ViewLog, dto=ViewLogDTO):

    @overload
    async def get_views(self, table_name: str, obj_id: int) -> int: ...

    @overload
    async def get_views(self, table_name: str, obj_id: list[int]) -> dict[int, int]: ...

    async def get_views(self, table_name: str, obj_id: Union[int, list[int]]) -> Union[int, dict[int, int]]:
        if isinstance(obj_id, list):
            if not obj_id:
                return {}

            stmt = select(self.model.object_id, func.count(self.model.id))
            stmt = self._build_filtered_query(stmt, {"object_type": table_name, "object_id__in": obj_id})
            stmt = stmt.group_by(self.model.object_id)

            result = await self._session.execute(stmt)
            db_counts = dict(result.tuples())

            return {oid: db_counts.get(oid, 0) for oid in obj_id}

        return await super().count(object_type=table_name, object_id=obj_id)

    @overload
    async def log_view(self, table_name: str, obj_id: list[int], user_id: int) -> None: ...

    @overload
    async def log_view(self, table_name: str, obj_id: int, user_id: Optional[int]) -> Optional[ViewLogDTO]: ...

    async def log_view(self, table_name: str, obj_id: Union[int, list[int]], user_id: Optional[int]) -> Optional[ViewLogDTO] | None:
        if isinstance(obj_id, list):
            if not obj_id or user_id is None:
                return

            view_logs_data = [
                {"object_type": table_name, "object_id": oid, "user_id": user_id}
                for oid in obj_id
            ]

            stmt = pg_insert(self.model).values(view_logs_data)
            stmt = stmt.on_conflict_do_nothing(index_elements=["object_type", "object_id", "user_id"])
            await self._session.execute(stmt)
            return

        return await super().create(object_type=table_name, object_id=obj_id, user_id=user_id)
