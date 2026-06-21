from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi.params import Path

if TYPE_CHECKING:
    from src.common.repositories import GenericRepository
    from src.common.services import GenericService
    from src.common.uow.units.abstract import AbstractUnitOfWork
    from src.common.data_objects import BaseDTO


from pydantic import BaseModel
from typing import TypeVar


DB_INT_MIN = -2_147_483_648
DB_INT_MAX = 2_147_483_647


T = TypeVar('T', bound=BaseModel)
R = TypeVar("R", bound="GenericRepository")
S = TypeVar("S", bound="GenericService")
U = TypeVar("U", bound="AbstractUnitOfWork")

ModelType = TypeVar("ModelType", bound=BaseModel)
DTOType = TypeVar("DTOType", bound="BaseDTO")

Int32Path = Annotated[int, Path(..., ge=1, le=DB_INT_MAX)]
