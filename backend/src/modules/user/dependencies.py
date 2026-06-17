from typing import Annotated, Optional

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette import status

from src.common.dependencies import JWTManagerDep
from src.common.uow.factory import UoWServiceFactory
from src.core.uow import create_sqlalchemy_uow
from src.modules.user.services import UserService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_optional_user_id(
        jwt_manager: JWTManagerDep,
        token: Annotated[Optional[str], Depends(oauth2_scheme)] = None,
) -> Optional[int]:
    if not token:
        return None

    try:
        payload = jwt_manager.decode_access_token(token)
        if not payload:
            return None

        user_id_str = payload.get("sub")
        return int(user_id_str) if user_id_str else None
    except Exception:
        return None


async def get_required_user_id(
        user_id: Annotated[Optional[int], Depends(get_optional_user_id)]
) -> int:
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


get_user_service = UoWServiceFactory(
    service_cls=UserService,
    uow_factory=create_sqlalchemy_uow
)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
OptionalUserIdDep = Annotated[int, Depends(get_optional_user_id)]
RequiredUserIdDep = Annotated[int, Depends(get_required_user_id)]
