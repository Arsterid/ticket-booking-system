from dataclasses import dataclass
from typing import Optional

from src.core.infra.database.repositories import BaseDTO


@dataclass
class ViewLogDTO(BaseDTO):
    id: int
    object_type: str
    object_id: int

    user_id: Optional[int] = None
