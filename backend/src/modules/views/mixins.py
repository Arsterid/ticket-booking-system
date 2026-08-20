from collections import Counter
from typing import Any, Optional, overload, Union
import logging

from src.app.exceptions import ObjectNotFoundException
from src.core.infra.cache.exceptions import CacheUnavailableError
from src.core.infra.database.exceptions import ForeignKeyViolationError
from .protocols import ViewableServiceProtocol

logger = logging.getLogger(__name__)


class ViewableServiceMixin:

    def _get_model_name(self) -> str:
        raise NotImplementedError(
            f"Service '{self.__class__.__name__}' uses ViewableServiceMixin "
            f"but does not implement the '_get_model_name()' method."
        )

    def _get_cache_key(self: ViewableServiceProtocol, obj_id: int) -> str:
        return f"views:{self._get_model_name()}:{obj_id}"

    def _get_hll_key(self: ViewableServiceProtocol, obj_id: int) -> str:
        return f"views:{self._get_model_name()}:{obj_id}:daily_hll"

    @overload
    async def get_views(self: ViewableServiceProtocol, obj_id: int) -> int:
        ...

    @overload
    async def get_views(self: ViewableServiceProtocol, obj_id: list[int]) -> dict[int, int]:
        ...

    async def get_views(self: ViewableServiceProtocol, obj_id: Union[int, list[int]]) -> Union[int, dict[int, int]]:
        if isinstance(obj_id, list):
            if not obj_id:
                return {}

            id_to_key = {oid: self._get_cache_key(oid) for oid in obj_id}
            keys = list(id_to_key.values())

            cached_values = None
            try:
                cached_values = await self.cache.get(keys)
            except CacheUnavailableError as e:
                logger.warning(f"Cache down in get_views (batch) for {self._get_model_name()}: {e}")

            final_counts, missing_ids = {}, []
            if cached_values:
                for (oid, key), val in zip(id_to_key.items(), cached_values):
                    if val is not None:
                        final_counts[oid] = int(val)
                    else:
                        missing_ids.append(oid)
            else:
                missing_ids = list(obj_id)

            if missing_ids:
                async with self.uow.as_readonly():
                    logs = await (
                        self.uow.view_logs
                        .filter(
                            object_type=self._get_model_name(),
                            object_id__in=missing_ids
                        )
                        .all()
                    )

                counts_map = Counter(log.object_id for log in logs)
                db_results = {oid: counts_map[oid] for oid in missing_ids}
                final_counts.update(db_results)

                if cached_values is not None:
                    try:
                        cache_mapping = {id_to_key[m_id]: db_results[m_id] for m_id in missing_ids}
                        await self.cache.set(cache_mapping, ttl=86400)
                    except CacheUnavailableError as e:
                        logger.warning(f"Failed to fill cache in get_views (batch) for {self._get_model_name()}: {e}")

            return final_counts

        cache_key = self._get_cache_key(obj_id)
        lock_key = f"lock:{cache_key}"

        try:
            cached_views = await self.cache.get(cache_key)
            if cached_views is not None:
                return int(cached_views)
        except CacheUnavailableError as e:
            logger.warning(f"Cache down in get_views (single) for {self._get_model_name()}: {e}")
            cached_views = None

        if cached_views is None:
            try:
                async with self.cache.lock(lock_key, timeout=5.0, blocking_timeout=3.0):
                    cached_views = await self.cache.get(cache_key)
                    if cached_views is not None:
                        return int(cached_views)

                    async with self.uow.as_readonly():
                        db_count = await (
                            self.uow.view_logs
                            .filter(
                                object_type=self._get_model_name(),
                                object_id=obj_id
                            )
                            .count()
                        )

                    await self.cache.set(cache_key, db_count, ttl=86400)
                    return db_count
            except CacheUnavailableError as e:
                logger.warning(
                    f"Cache lock/operations down in get_views for {self._get_model_name()}, using direct DB query: {e}")
                async with self.uow.as_readonly():
                    return await (
                        self.uow.view_logs
                        .filter(
                            object_type=self._get_model_name(),
                            object_id=obj_id
                        )
                        .count()
                    )

    @overload
    async def increment_views(self: ViewableServiceProtocol, obj_id: int, user_id: Optional[int] = None) -> None:
        ...

    @overload
    async def increment_views(self: ViewableServiceProtocol, obj_id: list[int], user_id: Optional[int] = None) -> None:
        ...

    async def increment_views(self: ViewableServiceProtocol, obj_id: Union[int, list[int]],
                              user_id: Optional[int] = None) -> None:
        if not user_id or not obj_id:
            return

        if isinstance(obj_id, list):
            try:
                hll_keys = [self._get_hll_key(oid) for oid in obj_id]
                uniques_mask = await self.cache.pfadd(hll_keys, user_id)
                unique_ids = [oid for oid, is_unique in zip(obj_id, uniques_mask) if is_unique]

                if not unique_ids:
                    return

                target_cache_keys = [self._get_cache_key(oid) for oid in unique_ids]
                target_hll_keys = [self._get_hll_key(oid) for oid in unique_ids]
                await self.cache.incr(target_cache_keys, ttl=86400, expire_keys=target_hll_keys)
            except CacheUnavailableError as e:
                logger.warning(f"Cache storage down during increment_views (batch) for {self._get_model_name()}: {e}")
                unique_ids = list(obj_id)

            view_logs_data = [
                {"object_type": self._get_model_name(), "object_id": oid, "user_id": user_id}
                for oid in unique_ids
            ]

            async with self.uow:
                try:
                    await self.uow.view_logs.create(
                        view_logs_data,
                        on_conflict_do_nothing=True,
                        index_elements=["object_type", "object_id", "user_id"]
                    )
                    await self.uow.commit()
                except ForeignKeyViolationError:
                    raise ObjectNotFoundException(
                        table=self._get_model_name(),
                        value=unique_ids
                    )
            return

        try:
            hll_key = self._get_hll_key(obj_id)
            is_new_view = await self.cache.pfadd(hll_key, user_id)
            if is_new_view:
                cache_key = self._get_cache_key(obj_id)
                await self.cache.incr(cache_key)
                await self.cache.expire(hll_key, 86400)
        except CacheUnavailableError as e:
            logger.warning(f"Cache storage down during increment_views (single) for {self._get_model_name()}: {e}")
            is_new_view = True

        if is_new_view:
            async with self.uow:
                try:
                    await self.uow.view_logs.create(
                        object_type=self._get_model_name(),
                        object_id=obj_id,
                        user_id=user_id,
                        on_conflict_do_nothing=True,
                        index_elements=["object_type", "object_id", "user_id"]
                    )
                    await self.uow.commit()
                except ForeignKeyViolationError:
                    raise ObjectNotFoundException(
                        table=self._get_model_name(),
                        value=obj_id
                    )

    @overload
    async def _enrich_with_views(self: ViewableServiceProtocol, items: Any) -> Any:
        ...

    @overload
    async def _enrich_with_views(self: ViewableServiceProtocol, items: list[Any]) -> list[Any]:
        ...

    async def _enrich_with_views(self: ViewableServiceProtocol, items: Any | list[Any]) -> Any | list[Any]:
        if not items:
            return items

        if isinstance(items, list):
            ids = [e.id for e in items]
            views_map = await self.get_views(obj_id=ids)
            for item in items:
                item.views = views_map.get(item.id, 0)
            return items

        items.views = await self.get_views(obj_id=items.id)
        return items
