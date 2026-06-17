from fastapi import FastAPI

from src.core.exceptions import ServiceException, ObjectNotFoundException, RaceConditionException, \
    service_exception_handler, object_not_found_handler, race_condition_handler

app = FastAPI(title="Ticket Booking System")

app.add_exception_handler(ServiceException, service_exception_handler)
app.add_exception_handler(ObjectNotFoundException, object_not_found_handler)
app.add_exception_handler(RaceConditionException, race_condition_handler)
