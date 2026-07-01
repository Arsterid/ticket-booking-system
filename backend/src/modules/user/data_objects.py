from dataclasses import dataclass

from src.core.infra.database.repositories.query.data_objects import BaseDTO
from .models import UserRole


@dataclass(frozen=True)
class UserDTO(BaseDTO):
    id: int
    role: UserRole
    email: str
    username: str
    password: str
    is_active: bool
