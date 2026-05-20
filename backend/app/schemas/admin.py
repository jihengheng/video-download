from pydantic import BaseModel, Field


class SiteRuleRequest(BaseModel):
    platform: str = Field(min_length=1, max_length=100)
    is_enabled: bool
    note: str | None = Field(default=None, max_length=500)


class BanUserRequest(BaseModel):
    is_banned: bool
