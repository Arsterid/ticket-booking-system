from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse


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


class ParametersConflictException(ServiceException):
    def __init__(
            self,
            options: list[str]
    ):
        self.options = options

        options_str = ", ".join(str(opt) for opt in options)
        message = f"Only one of the following parameters is allowed: {options_str}, but multiple were provided."

        super().__init__(message)


class MissingParameterException(ServiceException):
    def __init__(
            self,
            options: list[str]
    ):
        self.options = options

        options_str = ", ".join(str(opt) for opt in options)
        message = f"At least one of the following parameters is required: {options_str}, but none were provided."

        super().__init__(message)


class RaceConditionException(ServiceException):
    def __init__(
            self,
            table: str
    ):
        message = f"Object in '{table}' does not exist or was already changed by another actor concurrently."
        super().__init__(message)


async def service_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


async def object_not_found_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)}
    )


async def race_condition_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)}
    )
