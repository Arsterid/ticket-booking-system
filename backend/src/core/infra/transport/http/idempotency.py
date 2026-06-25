import json
from functools import wraps
from typing import Any, Callable
from fastapi import Request
from pydantic import BaseModel

from src.core.infra.cache.factory import get_cache_manager


def idempotent_endpoint(ttl: int = 3600):
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request: Request = kwargs.get("request") or next(
                (arg for arg in args if isinstance(arg, Request)), None
            )

            if request is None:
                return await func(*args, **kwargs)

            raw_key = request.headers.get("idempotency-key")

            if not raw_key or str(raw_key).strip().lower() in ("", "none", "null"):
                return await func(*args, **kwargs)

            idempotency_key = str(raw_key).strip()

            cache_manager = get_cache_manager()
            cache_key = f"idempotency:{idempotency_key}"
            lock_key = f"lock:{cache_key}"

            cached_data = await cache_manager.get(cache_key)
            if cached_data:
                return json.loads(cached_data)

            async with cache_manager.lock(lock_key, timeout=10.0, blocking_timeout=0.1):
                cached_data = await cache_manager.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)

                try:
                    response = await func(*args, **kwargs)

                    serializable_response = response
                    if isinstance(response, BaseModel):
                        serializable_response = response.model_dump()
                    elif hasattr(response, "__dict__"):
                        serializable_response = response.__dict__

                    await cache_manager.set(
                        cache_key,
                        json.dumps(serializable_response),
                        ttl=ttl
                    )
                    return response

                except Exception:
                    raise

        return wrapper

    return decorator
