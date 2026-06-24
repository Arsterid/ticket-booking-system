from typing import Annotated, Optional

from fastapi import Depends

from src.common.uow.factory import UoWServiceFactory
from src.core.tasks import task_manager
from src.core.uow import create_sqlalchemy_uow
from src.modules.user.models import UserRole
from src.modules.user.roles import RoleChecker
from src.modules.user.schemas import UsersFilterParamsSchema
from src.modules.user.services import UserService

UserServiceDep = Annotated[
    UserService,
    Depends(UoWServiceFactory(service_cls=UserService, uow_factory=create_sqlalchemy_uow, tasks=task_manager)),
]

OptionalUserIdDep = Annotated[Optional[int], Depends(RoleChecker(optional=True))]
AnyUserIdDep = Annotated[int, Depends(RoleChecker())]

VerifiedUserIdDep = Annotated[int, Depends(RoleChecker(required_role=UserRole.VERIFIED_USER))]
ModeratorUserIdDep = Annotated[int, Depends(RoleChecker(required_role=UserRole.MODERATOR))]
AdminUserIdDep = Annotated[int, Depends(RoleChecker(required_role=UserRole.ADMIN))]

UserFiltersDep = Annotated[UsersFilterParamsSchema, Depends(UsersFilterParamsSchema)]
