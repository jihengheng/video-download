from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SiteRule, User


def upsert_site_rule(db: Session, platform: str, is_enabled: bool, note: str | None) -> SiteRule:
    rule = db.scalar(select(SiteRule).where(SiteRule.platform == platform))
    if rule is None:
        rule = SiteRule(platform=platform, is_enabled=is_enabled, note=note)
    else:
        rule.is_enabled = is_enabled
        rule.note = note
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def ban_user(db: Session, user_id: int, is_banned: bool) -> User | None:
    user = db.get(User, user_id)
    if user is None:
        return None
    user.is_banned = is_banned
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
