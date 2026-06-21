from dataclasses import dataclass

from src.modules.user.models import UserRole


@dataclass(frozen=True)
class UserDTO:
    id: int
    role: UserRole
    email: str
    username: str
    password: str
    is_active: bool
