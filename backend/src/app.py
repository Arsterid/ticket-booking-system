from fastapi import FastAPI

from src.core.exceptions import ServiceException, ObjectNotFoundException, RaceConditionException, \
    service_exception_handler, object_not_found_handler, race_condition_handler
from src.modules.admin.routes import moderation_router, admin_router
from src.modules.event.routes import event_router
from src.modules.ticket.routes import ticket_router
from src.modules.user.routes import user_router

app = FastAPI(title="Ticket Booking System")

app.add_exception_handler(ServiceException, service_exception_handler)
app.add_exception_handler(ObjectNotFoundException, object_not_found_handler)
app.add_exception_handler(RaceConditionException, race_condition_handler)

app.include_router(moderation_router)
app.include_router(admin_router)
app.include_router(event_router)
app.include_router(ticket_router)
app.include_router(user_router)

# TODO write final docker-compose file

# TODO add alembic
