from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import QuotaAccount, User, UserRole


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def create_user(db: Session, email: str, password_hash: str, role: UserRole = UserRole.user) -> User:
    user = User(email=email, password_hash=password_hash, role=role.value)
    db.add(user)
    db.flush()
    quota = QuotaAccount(
        user_id=user.id,
        quota_date=date.today(),
        limit_count=get_settings().default_daily_quota,
        used_count=0,
    )
    db.add(quota)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_daily_quota(db: Session, user_id: int, limit_count: int) -> QuotaAccount:
    quota = db.scalar(
        select(QuotaAccount).where(
            QuotaAccount.user_id == user_id,
            QuotaAccount.quota_date == date.today(),
        )
    )
    if quota:
        return quota
    quota = QuotaAccount(user_id=user_id, quota_date=date.today(), limit_count=limit_count, used_count=0)
    db.add(quota)
    db.commit()
    db.refresh(quota)
    return quota
