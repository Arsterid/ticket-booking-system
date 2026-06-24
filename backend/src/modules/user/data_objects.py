from dataclasses import dataclass

from src.common.data_objects import BaseDTO
from src.modules.user.models import UserRole


@dataclass(frozen=True)
class UserDTO(BaseDTO):
    id: int
    role: UserRole
    email: str
    username: str
    password: str
    is_active: bool
