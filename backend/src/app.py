from fastapi import FastAPI

from src.core.exceptions import (
    ConflictException,
    ForbiddenException,
    ObjectNotFoundException,
    ServiceException,
    conflict_exception_handler,
    forbidden_exception_handler,
    incorrect_logic_data_handler,
    object_not_found_handler,
    service_exception_handler,
    value_exception_handler,
)
from src.metrics import init_metrics
from src.modules.user.exceptions import IncorrectLoginDataException
from src.routes import api_v1_router

app = FastAPI(
    title="Ticket Booking System",
    version="1.0.0",
)

app.add_exception_handler(ServiceException, service_exception_handler)
app.add_exception_handler(ValueError, value_exception_handler)
app.add_exception_handler(ObjectNotFoundException, object_not_found_handler)
app.add_exception_handler(ConflictException, conflict_exception_handler)
app.add_exception_handler(IncorrectLoginDataException, incorrect_logic_data_handler)
app.add_exception_handler(ForbiddenException, forbidden_exception_handler)

app.include_router(api_v1_router)

init_metrics(app)
