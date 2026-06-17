from typing import Optional

from pydantic import BaseModel, Field, EmailStr


class BaseUserSchema(BaseModel):
    email: EmailStr = Field(min_length=3, max_length=50)
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=20)


class UserCreateSchema(BaseUserSchema):
    pass


class UserCreateResponseSchema(BaseModel):
    id: int


class UserLoginSchema(BaseUserSchema):
    pass


class UserLoginResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
