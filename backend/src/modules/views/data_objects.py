from typing import Optional


from src.core.infra.database.repositories.data_objects import BaseDTO


class ViewLogDTO(BaseDTO):
    id: int
    object_type: str
    object_id: int

    user_id: Optional[int] = None
