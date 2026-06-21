from fastapi import FastAPI

from src.modules.user.exceptions import IncorrectLoginDataException
from src.metrics import init_metrics
from src.routes import api_v1_router
from src.core.exceptions import ServiceException, ObjectNotFoundException, RaceConditionException, \
    service_exception_handler, object_not_found_handler, race_condition_handler, incorrect_logic_data_handler

app = FastAPI(
    title="Ticket Booking System",
    version="1.0.0",
)

app.add_exception_handler(ServiceException, service_exception_handler)
app.add_exception_handler(ObjectNotFoundException, object_not_found_handler)
app.add_exception_handler(RaceConditionException, race_condition_handler)
app.add_exception_handler(IncorrectLoginDataException, incorrect_logic_data_handler)

app.include_router(api_v1_router)

init_metrics(app)
