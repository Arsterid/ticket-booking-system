class ServiceException(Exception):
    pass


class ForbiddenException(ServiceException):
    pass


class ConflictException(ServiceException):
    pass


class UnauthorizedException(ServiceException):
    pass


class ObjectNotFoundException(ServiceException):
    def __init__(self, table: str, value: any, field: str = "id"):
        message = f"Object in table '{table}' with {field} '{value}' does not exist"

        super().__init__(message)


class UniqueFieldException(ServiceException):
    def __init__(self, field: str, value: any):
        message = f"Object with unique field '{field}' with value '{value}' already exists."

        super().__init__(message)


class WrongStateException(ServiceException):
    def __init__(self, current: str, expected: str):
        message = f"Cannot perform this operation. Current state: '{current}', expected: '{expected}'"

        super().__init__(message)


class ParametersConflictException(ServiceException):
    def __init__(self, options: list[str]):
        self.options = options

        options_str = ", ".join(str(opt) for opt in options)
        message = f"Only one of the following parameters is allowed: {options_str}, but multiple were provided."

        super().__init__(message)


class MissingParameterException(ServiceException):
    def __init__(self, options: list[str]):
        self.options = options

        options_str = ", ".join(str(opt) for opt in options)
        message = f"At least one of the following parameters is required: {options_str}, but none were provided."

        super().__init__(message)


class RaceConditionException(ConflictException):
    def __init__(self, table: str, value: any, field: str = "id"):
        message = f"Object in '{table}' with {field} '{value}' was already changed by another actor concurrently."
        super().__init__(message)


class ValidationException(ServiceException):
    def __init__(self, message: str):
        super().__init__(message)
