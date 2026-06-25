from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.core.database import db_factory
from src.core.infra.cache.factory import get_cache_manager
from src.core.infra.tasks.config import broker


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    await broker.startup()

    cache_manager = get_cache_manager()
    if hasattr(cache_manager, "redis_client"):
        await cache_manager.redis_client.ping()

    yield

    await broker.shutdown()

    if hasattr(cache_manager, "redis_client"):
        await cache_manager.redis_client.close()

    engine = db_factory.get_engine()
    await engine.dispose()
