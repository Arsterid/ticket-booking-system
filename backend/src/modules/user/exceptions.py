from src.core.exceptions import ServiceException, RaceConditionException


class IncorrectLoginDataException(ServiceException):
    def __init__(self):
        super().__init__('Incorrect login data.')


class UserIsBannedException(ServiceException):
    def __init__(self):
        super().__init__('User is banned.')


class UserVerificationConflictException(RaceConditionException):
    def __init__(self):
        super().__init__('User is already verified, pending verification, or inactive.')
