from fastapi import APIRouter
from starlette import status

from src.common.dependencies import PasswordManagerDep, JWTManagerDep
from src.modules.user.dependencies import UserServiceDep
from src.modules.user.schemas import UserCreateResponseSchema, UserCreateSchema, UserLoginResponseSchema, UserLoginSchema

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
    user_id = await user_service.create_user(data=body)
    return UserCreateResponseSchema(id=user_id)


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=UserLoginResponseSchema
)
async def login(
        body: UserLoginSchema,
        service: UserServiceDep,
        pwd_manager: PasswordManagerDep,
        jwt_manager: JWTManagerDep
) -> UserLoginResponseSchema:
    token, bearer = await service.authenticate(
        data=body,
        pwd_manager=pwd_manager,
        jwt_manager=jwt_manager
    )
    return UserLoginResponseSchema(access_token=token, token_type=bearer)
