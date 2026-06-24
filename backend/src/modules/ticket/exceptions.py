from src.core.exceptions import ConflictException


class TicketAlreadyAssignedException(ConflictException):
    def __init__(self):
        super().__init__("Ticket is already assigned to this user.")
