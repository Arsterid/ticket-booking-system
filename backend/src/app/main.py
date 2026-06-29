from fastapi import FastAPI
from starlette import status

from src.app.lifespan import app_lifespan
from src.core.infra.transport.http.exception_handlers import create_exception_handler
from src.app.exceptions import (
    ServiceException,
    ForbiddenException,
    ConflictException,
    ObjectNotFoundException,
    UnauthorizedException
)
from src.app.metrics import init_metrics
from src.app.routes import api_v1_router

app = FastAPI(
    title="Ticket Booking System",
    version="1.0.0",
    lifespan=app_lifespan
)

EXCEPTION_MAPPING = {
    ServiceException: status.HTTP_400_BAD_REQUEST,
    UnauthorizedException: status.HTTP_401_UNAUTHORIZED,
    ForbiddenException: status.HTTP_403_FORBIDDEN,
    ObjectNotFoundException: status.HTTP_404_NOT_FOUND,
    ConflictException: status.HTTP_409_CONFLICT,
    ValueError: status.HTTP_422_UNPROCESSABLE_CONTENT,

}

for exception_cls, status_code in EXCEPTION_MAPPING.items():
    handler = create_exception_handler(status_code)
    app.add_exception_handler(exception_cls, handler)

app.include_router(api_v1_router)

init_metrics(app)
