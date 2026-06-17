from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.base.core.repository import GenericRepository
    from src.base.core.service import GenericService
    from src.base.uow.units.abstract import AbstractUnitOfWork

from pydantic import BaseModel
from typing import TypeVar

T = TypeVar('T', bound=BaseModel)
R = TypeVar("R", bound=GenericRepository)
S = TypeVar("S", bound=GenericService)
U = TypeVar("U", bound=AbstractUnitOfWork)

ModelType = TypeVar("ModelType", bound=BaseModel)
