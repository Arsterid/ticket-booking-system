from typing import Optional, Any
from src.common.views.protocols import ViewableServiceProtocol


class ViewableServiceMixin:

    def _get_cache_key(self: ViewableServiceProtocol, obj_id: int) -> str:
        return f"views:{self._repo_cls.get_model_name()}:{obj_id}"

    def _get_hll_key(self: ViewableServiceProtocol, obj_id: int) -> str:
        return f"views:{self._repo_cls.get_model_name()}:{obj_id}:daily_hll"

    async def get_views_count(self: ViewableServiceProtocol, obj_id: int) -> int:
        cache_key = self._get_cache_key(obj_id)
        lock_key = f"lock:{cache_key}"

        cached_views = await self.cache.get(cache_key)
        if cached_views is not None:
            return int(cached_views)

        async with self.cache.lock(lock_key, timeout=5.0, blocking_timeout=3.0):
            cached_views = await self.cache.get(cache_key)
            if cached_views is not None:
                return int(cached_views)

            async with self.uow:
                db_count = await self.uow.view_logs.get_object_views_count(
                    table_name=self._repo_cls.get_model_name(),
                    obj_id=obj_id
                )

            await self.cache.set(cache_key, db_count, ttl=86400)
            return db_count

    async def increment_views(self: ViewableServiceProtocol, obj_id: int,
                              actor_id: Optional[int] = None) -> None:
        if not actor_id:
            return

        hll_key = self._get_hll_key(obj_id)
        is_new_view = await self.cache.pfadd(hll_key, actor_id)

        if is_new_view:
            cache_key = self._get_cache_key(obj_id)

            await self.cache.incr(cache_key)
            await self.cache.expire(hll_key, 86400)

            async with self.uow:
                await self.uow.view_logs.create_view_log(
                    table_name=self._repo_cls.get_model_name(),
                    obj_id=obj_id,
                    user_id=actor_id
                )

    async def bulk_get_views_counts(self: ViewableServiceProtocol, obj_ids: list[int]) -> dict[int, int]:
        if not obj_ids:
            return {}

        id_to_key = {obj_id: self._get_cache_key(obj_id) for obj_id in obj_ids}
        keys = list(id_to_key.values())

        cached_values = await self.cache.bulk_get(keys)

        final_counts, missing_ids = {}, []
        for (obj_id, key), val in zip(id_to_key.items(), cached_values):
            if val is not None:
                final_counts[obj_id] = int(val)
            else:
                missing_ids.append(obj_id)

        if missing_ids:
            async with self.uow:
                db_results = await self.uow.view_logs.bulk_get_objects_views(
                    table_name=self._repo_cls.get_model_name(),
                    obj_ids=missing_ids
                )

            final_counts.update(db_results)
            cache_mapping = {id_to_key[m_id]: db_results[m_id] for m_id in missing_ids}
            await self.cache.bulk_set(cache_mapping, ttl=86400)

        return final_counts

    async def bulk_increment_views(self: ViewableServiceProtocol, obj_ids: list[int],
                                   actor_id: Optional[int] = None) -> None:
        if not actor_id or not obj_ids:
            return

        hll_keys = [self._get_hll_key(oid) for oid in obj_ids]
        uniques_mask = await self.cache.bulk_pfadd(hll_keys, actor_id)

        unique_ids = [oid for oid, is_unique in zip(obj_ids, uniques_mask) if is_unique]
        if not unique_ids:
            return

        target_cache_keys = [self._get_cache_key(oid) for oid in unique_ids]
        target_hll_keys = [self._get_hll_key(oid) for oid in unique_ids]

        await self.cache.bulk_incr_and_expire(target_cache_keys, target_hll_keys, 86400)

        async with self.uow:
            await self.uow.view_logs.bulk_create_view_logs(
                table_name=self._repo_cls.get_model_name(),
                obj_ids=unique_ids,
                user_id=actor_id
            )

    async def _enrich_items_with_views(self: ViewableServiceProtocol, items: list[Any]) -> list[Any]:
        if not items:
            return items
        ids = [e.id for e in items]
        views_map = await self.bulk_get_views_counts(obj_ids=ids)
        for item in items:
            item.views = views_map.get(item.id, 0)
        return items

    async def _enrich_item_with_views(self: ViewableServiceProtocol, item: Any) -> Any:
        if not item:
            return item
        item.views = await self.get_views_count(obj_id=item.id)
        return item
