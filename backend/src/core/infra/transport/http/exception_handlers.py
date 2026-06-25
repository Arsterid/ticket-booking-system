from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse


async def value_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": str(exc)})


async def service_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})


async def object_not_found_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


async def forbidden_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": str(exc)})


async def conflict_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


async def unauthorized_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": str(exc)})
