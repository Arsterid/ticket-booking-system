from src.base.exceptions import ServiceException


class IncorrectLoginDataException(ServiceException):
    def __init__(self):
        super().__init__('Incorrect login data.')


class UserIsBannedException(ServiceException):
    def __init__(self):
        super().__init__('User is banned.')


class InsufficientRightsException(ServiceException):
    def __init__(self):
        super().__init__('Insufficient rights.')
