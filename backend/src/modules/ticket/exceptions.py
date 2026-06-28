from src.app.exceptions import ConflictException


class NoTicketsAvailableException(ConflictException):
    def __init__(self, category: str, available: int, requested: int | None = None):
        message = (f"Not enough tickets available in category {category} to process an order."
                   f" Available: {available}.")
        if requested is not None:
            message += f" Requested: {requested}."

        super().__init__(message)
        self.extra = {
            "category": category,
            "available": available,
            "requested": requested
        }
