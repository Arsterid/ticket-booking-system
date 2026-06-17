class ServiceException(Exception):
    pass


class ObjectNotFoundException(ServiceException):
    def __init__(
            self,
            table: str,
            value: any,
            field: str = "id"
    ):
        message = f"Object in table '{table}' with {field} '{value}' does not exist"

        super().__init__(message)


class UniqueFieldException(ServiceException):
    def __init__(
            self,
            field: str,
            value: any
    ):
        message = f"Object with unique field '{field}' with value '{value}' already exists."

        super().__init__(message)


class WrongStateException(ServiceException):
    def __init__(
            self,
            current: str,
            expected: str
    ):
        message = (
            f"Cannot perform this operation. "
            f"Current state: '{current}', expected: '{expected}'"
        )

        super().__init__(message)
