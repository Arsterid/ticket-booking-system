from abc import ABC
from dataclasses import dataclass
from typing import Optional, Any, Generic

from src.common.annotations import DTOType


class BaseDTO(ABC):
    pass


@dataclass(frozen=True)
class ModificationResult:
    rowcount: int
    returning_rows: list[Any]

    @property
    def success(self) -> bool:
        return self.rowcount > 0 or bool(self.returning_rows)

    @property
    def first_returning(self) -> Optional[Any]:
        return self.returning_rows[0] if self.returning_rows else None

    @property
    def scalar_returning(self) -> Optional[Any]:
        return self.returning_rows[0][0] if self.returning_rows else None


@dataclass(frozen=True)
class CreationResult(Generic[DTOType]):
    dto: Optional[DTOType] = None

    @property
    def success(self) -> bool:
        return self.dto is not None
