from fastapi import APIRouter
from starlette import status

from src.common.dependencies import PasswordManagerDep, JWTManagerDep
from src.common.schemas import GenericSuccessResponseSchema
from src.modules.user.dependencies import UserServiceDep, AnyUserIdDep
from src.modules.user.schemas import UserCreateResponseSchema, UserCreateSchema, UserLoginResponseSchema, \
    UserLoginSchema

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserCreateResponseSchema
)
async def register(
        user_service: UserServiceDep,
        body: UserCreateSchema,
) -> UserCreateResponseSchema:
    user_id = await user_service.create(data=body)
    return UserCreateResponseSchema(id=user_id)


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=UserLoginResponseSchema
)
async def login(
        body: UserLoginSchema,
        user_service: UserServiceDep,
        pwd_manager: PasswordManagerDep,
        jwt_manager: JWTManagerDep
) -> UserLoginResponseSchema:
    token, bearer = await user_service.authenticate(
        data=body,
        pwd_manager=pwd_manager,
        jwt_manager=jwt_manager
    )
    return UserLoginResponseSchema(access_token=token, token_type=bearer)


@router.post(
    "/verification/apply",
    status_code=status.HTTP_200_OK,
    response_model=GenericSuccessResponseSchema
)
async def apply_for_verification(
        user_service: UserServiceDep,
        user_id: AnyUserIdDep
) -> GenericSuccessResponseSchema:
    is_success = await user_service.apply_for_verification(user_id)
    return GenericSuccessResponseSchema(success=is_success)
