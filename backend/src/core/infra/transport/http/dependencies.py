from typing import Annotated

from fastapi import Depends

from src.core.infra.transport.http.schemas.base import PaginationParamsSchema
from src.core.security import JWTManager, PasswordManager
from src.core.settings import AppConfig, get_settings


def get_jwt_manager(config: Annotated[AppConfig, Depends(get_settings)]) -> JWTManager:
    return JWTManager(
        secret_key=config.jwt_secret_key, algorithm=config.jwt_algorithm, expire_seconds=config.jwt_expires_in
    )


def get_password_manager(config: Annotated[AppConfig, Depends(get_settings)]) -> PasswordManager:
    return PasswordManager(algorithm=config.password_algorithm, iterations=config.password_iterations)


JWTManagerDep = Annotated[JWTManager, Depends(get_jwt_manager)]
PasswordManagerDep = Annotated[PasswordManager, Depends(get_password_manager)]
PaginationParamsDep = Annotated[PaginationParamsSchema, Depends(PaginationParamsSchema)]
