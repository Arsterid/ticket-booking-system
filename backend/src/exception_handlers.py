from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.base.exceptions import ServiceException, ObjectNotFoundException, RaceConditionException
from src.main import app


@app.exception_handler(ServiceException)
async def service_exception_handler(request: Request, exc: ServiceException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


@app.exception_handler(ObjectNotFoundException)
async def object_not_found_handler(request: Request, exc: ObjectNotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)}
    )


@app.exception_handler(RaceConditionException)
async def race_condition_handler(request: Request, exc: RaceConditionException):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)}
    )
