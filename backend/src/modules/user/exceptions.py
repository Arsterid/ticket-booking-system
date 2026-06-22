from src.core.exceptions import ServiceException, ForbiddenException, ConflictException


class IncorrectLoginDataException(ServiceException):
    def __init__(self):
        super().__init__('Incorrect login data.')


class UserIsBannedException(ServiceException):
    def __init__(self):
        super().__init__('User is banned.')


class UserIsNotBannedException(ServiceException):
    def __init__(self):
        super().__init__('User is not banned.')


class UserVerificationConflictException(ConflictException):
    def __init__(self):
        super().__init__('User is already verified, pending verification, or inactive.')


class UserIsNotAppliedToVerificationException(ServiceException):
    def __init__(self):
        super().__init__('User was not applied to verification.')


class CannotBanAdminException(ForbiddenException):
    def __init__(self):
        super().__init__('You cannot ban user with administrator right.')


class CannotBanYourselfException(ForbiddenException):
    def __init__(self):
        super().__init__('You cannot ban yourself.')


class CannotUnbanYourselfException(ForbiddenException):
    def __init__(self):
        super().__init__('You cannot ban yourself.')


class AlreadyRegisteredException(ConflictException):
    def __init__(self):
        super().__init__('User with this email already registered, cannot reserve as anonym.')
