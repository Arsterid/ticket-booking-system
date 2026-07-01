from fastapi import APIRouter, status

from src.core.infra.transport.http import GenericSuccessResponseSchema, JWTManagerDep, PasswordManagerDep

from .dependencies import AnyUserIdDep, UserServiceDep
from .schemas import (
    UserCreateResponseSchema,
    UserCreateSchema,
    UserLoginResponseSchema,
    UserLoginSchema,
)

user_router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@user_router.post("", status_code=status.HTTP_201_CREATED, response_model=UserCreateResponseSchema)
async def register(
        user_service: UserServiceDep,
        pwd_manager: PasswordManagerDep,
        body: UserCreateSchema,
) -> UserCreateResponseSchema:
    return await user_service.create(pwd_manager=pwd_manager, data=body)


@user_router.post("/login", status_code=status.HTTP_200_OK, response_model=UserLoginResponseSchema)
async def login(
        body: UserLoginSchema, user_service: UserServiceDep, pwd_manager: PasswordManagerDep, jwt_manager: JWTManagerDep
) -> UserLoginResponseSchema:
    return await user_service.authenticate(data=body, pwd_manager=pwd_manager, jwt_manager=jwt_manager)


@user_router.post("/verification/apply", status_code=status.HTTP_200_OK, response_model=GenericSuccessResponseSchema)
async def apply_for_verification(user_service: UserServiceDep, user_id: AnyUserIdDep) -> GenericSuccessResponseSchema:
    is_success = await user_service.apply_for_verification(user_id)
    return GenericSuccessResponseSchema(success=is_success)
