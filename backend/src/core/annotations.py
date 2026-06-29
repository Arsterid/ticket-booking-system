from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.services import GenericService
    from src.core.infra.database.repositories import GenericRepository
    from src.core.infra.database.uow.units import AbstractUnitOfWork
    from src.core.infra.database.orm.base import BaseORMModel
    from src.core.infra.database.repositories.data_objects import BaseDTO

from typing import TypeVar


SERVICE_T = TypeVar("SERVICE_T", bound="GenericService")
REPOSITORY_T = TypeVar("REPOSITORY_T", bound="GenericRepository")
UOW_T = TypeVar("UOW_T", bound="AbstractUnitOfWork")

ORM_MODEL_T = TypeVar("ORM_MODEL_T", bound="BaseORMModel")
DTO_T = TypeVar("DTO_T", bound="BaseDTO")
