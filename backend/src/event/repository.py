from src.base.core.repository import GenericRepository
from src.event.models import Event


class EventRepository(GenericRepository[Event], model=Event):
    pass

