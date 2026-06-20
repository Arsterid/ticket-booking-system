from typing import Optional

from pydantic import BaseModel, Field, EmailStr

from src.common.schemas import FilterParamsSchema, GenericResponseSchema
from src.modules.user.models import UserRole


class BaseUserSchema(BaseModel):
    email: EmailStr = Field(min_length=3, max_length=50)
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=20)


class UserCreateSchema(BaseUserSchema):
    pass


class UserCreateResponseSchema(GenericResponseSchema):
    id: int


class UserLoginSchema(BaseUserSchema):
    pass


class UserLoginResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponseSchema(GenericResponseSchema):
    id: int
    role: UserRole
    username: str


class UsersFilterParamsSchema(FilterParamsSchema):
    username: Optional[str] = Field(default=None, min_length=3, max_length=50, description="Username")
