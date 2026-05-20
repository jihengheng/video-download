from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DBSession, get_current_user, require_user
from app.core.config import get_settings
from app.core.errors import user_error
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.repos.users import create_user, get_or_create_daily_quota, get_user_by_email
from app.schemas.auth import LoginRequest, QuotaResponse, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DBSession) -> TokenResponse:
    existing = get_user_by_email(db, payload.email)
    if existing:
        raise user_error(status.HTTP_409_CONFLICT, "该邮箱已经注册，请直接登录。")
    user = create_user(db, payload.email, hash_password(payload.password))
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DBSession) -> TokenResponse:
    user = get_user_by_email(db, payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise user_error(status.HTTP_401_UNAUTHORIZED, "邮箱或密码错误。")
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(require_user)) -> UserResponse:
    return UserResponse.model_validate(user)


@router.get("/quota", response_model=QuotaResponse)
def quota(db: DBSession, user: User | None = Depends(get_current_user)) -> QuotaResponse:
    settings = get_settings()
    if user is None:
        return QuotaResponse(
            quota_date=date.today(),
            limit_count=settings.anon_daily_quota,
            used_count=0,
            remaining_count=settings.anon_daily_quota,
        )
    snapshot = get_or_create_daily_quota(db, user.id, settings.default_daily_quota)
    return QuotaResponse(
        quota_date=snapshot.quota_date,
        limit_count=snapshot.limit_count,
        used_count=snapshot.used_count,
        remaining_count=max(snapshot.limit_count - snapshot.used_count, 0),
    )
