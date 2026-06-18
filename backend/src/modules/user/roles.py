from fastapi import Depends, HTTPException, status
from typing import Annotated

from fastapi.security import OAuth2PasswordBearer

from src.common.dependencies import JWTManagerDep
from src.modules.user.models import UserRole


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class RoleChecker:
    def __init__(self, required_role: UserRole | None = None, optional: bool = False):
        self.required_role = required_role
        self.optional = optional

    async def __call__(
            self,
            jwt_manager: JWTManagerDep,
            token: Annotated[str | None, Depends(oauth2_scheme)] = None,
    ) -> int | None:
        payload = self._get_payload(jwt_manager, token)
        if payload is None:
            return None

        user_id = self._extract_user_id(payload)

        if self.required_role is not None:
            user_role = self._extract_user_role(payload)
            self._validate_permissions(user_role)

        return user_id

    def _get_payload(self, jwt_manager: JWTManagerDep, token: str | None) -> dict | None:
        if not token or not (payload := jwt_manager.decode_access_token(token)):
            if self.optional:
                return None
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload

    def _extract_user_id(self, payload: dict) -> int | None:
        user_id_str = payload.get("sub")
        if not user_id_str:
            if self.optional:
                return None
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found in token.",
            )
        return int(user_id_str)

    def _extract_user_role(self, payload: dict) -> UserRole:
        role_str = payload.get("role")
        if not role_str:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Role not found in token.",
            )
        try:
            return UserRole(role_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unknown role in token.",
            )

    def _validate_permissions(self, user_role: UserRole) -> None:
        if user_role < self.required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions.",
            )
