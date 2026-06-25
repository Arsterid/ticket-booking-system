from src.app.exceptions import ConflictException


class EventCategoryIsNotALeafException(ConflictException):
    def __init__(self, id: int):
        super().__init__(f"Event category with id {id} is not a leaf.")


class EventCategoryHasEventsException(ConflictException):
    def __init__(self, id: int):
        super().__init__(f"Event category with id {id} is a leaf.")
