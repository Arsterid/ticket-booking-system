from src.app.exceptions import ServiceException


class UnknownModelTypeException(ServiceException):
    def __init__(self, name: str):
        super().__init__(f"Unknown model type: '{name}'")
