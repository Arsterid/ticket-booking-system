from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from src.common.repositories import GenericRepository
from src.common.views.data_objects import ViewLogDTO
from src.common.views.models import ViewLog


class ViewLogRepository(GenericRepository[ViewLog, ViewLogDTO], model=ViewLog, dto=ViewLogDTO):
    async def get_object_views_count(self, table_name: str, obj_id: int) -> int:
        return await self.count(object_type=table_name, object_id=obj_id)

    async def create_view_log(self, table_name: str, obj_id: int, user_id: Optional[int]) -> ViewLogDTO:
        return await self.create(object_type=table_name, object_id=obj_id, user_id=user_id)

    async def bulk_get_objects_views(self, table_name: str, obj_ids: list[int]) -> dict[int, int]:
        if not obj_ids:
            return {}

        stmt = select(self.model.object_id, func.count(self.model.id).label("views_count"))
        stmt = self._build_filtered_query(stmt, {"object_type": table_name, "object_id__in": obj_ids})
        stmt = stmt.group_by(self.model.object_id)

        result = await self._session.execute(stmt)

        db_counts = dict(result.tuples().all())

        return dict.fromkeys(obj_ids, 0) | db_counts

    async def bulk_create_view_logs(self, table_name: str, obj_ids: list[int], user_id: int) -> None:
        if not obj_ids:
            return

        view_logs_data = [
            {"object_type": table_name, "object_id": oid, "user_id": user_id}
            for oid in obj_ids
        ]

        stmt = insert(self.model).values(view_logs_data)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["object_type", "object_id", "user_id"]
        )

        await self._session.execute(stmt)
