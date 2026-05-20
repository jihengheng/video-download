from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import user_error
from app.models import AuditLog, QuotaAccount, User
from app.repos.users import get_or_create_daily_quota


def get_quota_snapshot(db: Session, user: User | None) -> QuotaAccount:
    settings = get_settings()
    if user is None:
        return QuotaAccount(user_id=0, quota_date=date.today(), limit_count=settings.anon_daily_quota, used_count=0)
    return get_or_create_daily_quota(db, user.id, settings.default_daily_quota)


def consume_quota_or_raise(db: Session, user: User | None, ip_address: str | None, source_url: str) -> QuotaAccount:
    quota = get_quota_snapshot(db, user)
    if quota.used_count >= quota.limit_count:
        db.add(
            AuditLog(
                user_id=user.id if user else None,
                action="quota_denied",
                ip_address=ip_address,
                source_url=source_url,
                hit_rule="daily_quota",
                success=False,
            )
        )
        db.commit()
        raise user_error(status.HTTP_429_TOO_MANY_REQUESTS, "今日额度已用完，请明天再试。")
    if user:
        quota.used_count += 1
        db.add(quota)
        db.commit()
        db.refresh(quota)
    return quota
