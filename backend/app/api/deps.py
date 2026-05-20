from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import user_error
from app.models import User

DBSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DBSession,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> User | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise user_error(status.HTTP_401_UNAUTHORIZED, "登录凭证格式不正确，请重新登录后重试。")
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"], issuer=settings.jwt_issuer)
    except JWTError as exc:
        raise user_error(status.HTTP_401_UNAUTHORIZED, "登录状态已失效，请重新登录。") from exc
    subject = payload.get("sub")
    if subject is None:
        raise user_error(status.HTTP_401_UNAUTHORIZED, "登录状态无效，请重新登录。")
    user = db.get(User, int(subject))
    if user is None or user.is_banned:
        raise user_error(status.HTTP_403_FORBIDDEN, "当前账号不可用，请联系管理员。")
    return user


def require_user(user: Annotated[User | None, Depends(get_current_user)]) -> User:
    if user is None:
        raise user_error(status.HTTP_401_UNAUTHORIZED, "请先登录后再执行此操作。")
    return user


def require_admin(user: Annotated[User, Depends(require_user)]) -> User:
    if user.role != "admin":
        raise user_error(status.HTTP_403_FORBIDDEN, "当前操作需要管理员权限。")
    return user
