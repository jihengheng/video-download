from datetime import date

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(RegisterRequest):
    pass


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(ORMModel):
    id: int
    email: EmailStr
    role: str
    is_banned: bool


class QuotaResponse(BaseModel):
    quota_date: date
    limit_count: int
    used_count: int
    remaining_count: int
