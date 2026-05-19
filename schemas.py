from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional


class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str

    @field_validator("password")
    @classmethod
    def check_password(cls, val: str):
        if len(val) <= 8:
            raise ValueError("password must be at least 8 chars")
        return val

    @field_validator("username")
    @classmethod
    def username_clean(cls, val: str) -> str:
        if len(val) < 3:
            raise ValueError("Username must be at least 3 characters")
        return val.strip().lower()


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfileResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    is_active: bool

    model_config = {"from_attributes": True}


class AdminProfileResponse(UserProfileResponse):
    is_admin: bool


class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
