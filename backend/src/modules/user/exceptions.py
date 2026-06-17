from src.core.exceptions import ServiceException


class IncorrectLoginDataException(ServiceException):
    def __init__(self):
        super().__init__('Incorrect login data.')


class UserIsBannedException(ServiceException):
    def __init__(self):
        super().__init__('User is banned.')
