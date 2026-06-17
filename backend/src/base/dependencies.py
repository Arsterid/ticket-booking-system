from typing import Annotated
from fastapi import Depends

from src.base.security.jwt_tokens import JWTManager
from src.base.security.passwords import PasswordManager
from src.settings import AppConfig, settings


def get_config() -> AppConfig:
    return settings


def get_jwt_manager(config: Annotated[AppConfig, Depends(get_config)]) -> JWTManager:
    return JWTManager(
        secret_key=config.JWT_SECRET_KEY,
        algorithm=config.JWT_ALGORITHM,
        expire_minutes=config.JWT_EXPIRE_MINUTES
    )


def get_password_manager(config: Annotated[AppConfig, Depends(get_config)]) -> PasswordManager:
    return PasswordManager(
        algorithm=config.PWD_ALGORITHM,
        iterations=config.PWD_ITERATIONS
    )


JWTManagerDep = Annotated[JWTManager, Depends(get_jwt_manager)]
PasswordManagerDep = Annotated[PasswordManager, Depends(get_password_manager)]
