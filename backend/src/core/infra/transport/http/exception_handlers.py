from fastapi import Request, status
from fastapi.responses import JSONResponse
from typing import Any


def _build_error_content(exc: Exception) -> dict[str, Any]:
    content = {"detail": str(exc)}
    extra = getattr(exc, "extra", None)
    if extra:
        content["extra"] = extra
    return content


async def value_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=_build_error_content(exc)
    )


async def service_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=_build_error_content(exc)
    )


async def object_not_found_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=_build_error_content(exc)
    )


async def forbidden_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=_build_error_content(exc)
    )


async def conflict_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=_build_error_content(exc)
    )


async def unauthorized_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=_build_error_content(exc)
    )