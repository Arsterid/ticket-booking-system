from typing import Optional

from pydantic import BaseModel, Field, EmailStr, field_validator

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
    email: str


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
    role: Optional[UserRole] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50, strip_whitespace=True, description="Username")
    is_active: Optional[bool] = None

    @field_validator("username")
    @classmethod
    def validate_username_filter(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Username filter cannot be empty")
        return v

