from fastapi import FastAPI

from src.app.lifespan import app_lifespan
from src.core.infra.transport.http.exception_handlers import (
    value_exception_handler,
    service_exception_handler,
    object_not_found_handler,
    forbidden_exception_handler,
    conflict_exception_handler,
    unauthorized_exception_handler
)
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

app.add_exception_handler(ServiceException, service_exception_handler)
app.add_exception_handler(ValueError, value_exception_handler)
app.add_exception_handler(ObjectNotFoundException, object_not_found_handler)
app.add_exception_handler(ConflictException, conflict_exception_handler)
app.add_exception_handler(UnauthorizedException, unauthorized_exception_handler)
app.add_exception_handler(ForbiddenException, forbidden_exception_handler)

app.include_router(api_v1_router)

init_metrics(app)
