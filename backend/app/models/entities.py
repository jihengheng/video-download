from __future__ import annotations

from datetime import UTC, datetime, date
from enum import Enum
from secrets import token_urlsafe

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class UserRole(str, Enum):
    user = "user"
    admin = "admin"


class TaskStatus(str, Enum):
    pending = "pending"
    parsing = "parsing"
    downloading = "downloading"
    transcribing = "transcribing"
    summarizing = "summarizing"
    completed = "completed"
    failed = "failed"
    deleted = "deleted"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default=UserRole.user.value)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    quotas: Mapped[list[QuotaAccount]] = relationship(back_populates="user", cascade="all, delete-orphan")
    tasks: Mapped[list[VideoTask]] = relationship(back_populates="user")


class QuotaAccount(Base):
    __tablename__ = "quota_accounts"
    __table_args__ = (UniqueConstraint("user_id", "quota_date", name="uq_quota_user_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    quota_date: Mapped[date] = mapped_column(Date, default=date.today)
    limit_count: Mapped[int] = mapped_column(Integer)
    used_count: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped[User] = relationship(back_populates="quotas")


class VideoTask(Base):
    __tablename__ = "video_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    source_url: Mapped[str] = mapped_column(String(2048))
    source_platform: Mapped[str] = mapped_column(String(100))
    video_title: Mapped[str] = mapped_column(String(500))
    thumbnail_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    selected_format_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    public_token: Mapped[str] = mapped_column(String(64), default=lambda: token_urlsafe(24), unique=True, index=True)
    need_summary: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(30), default=TaskStatus.pending.value, index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    can_retry: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User | None] = relationship(back_populates="tasks")
    artifacts: Mapped[list[TaskArtifact]] = relationship(back_populates="task", cascade="all, delete-orphan")
    transcript: Mapped[Transcript | None] = relationship(back_populates="task", uselist=False, cascade="all, delete-orphan")
    summary: Mapped[Summary | None] = relationship(back_populates="task", uselist=False, cascade="all, delete-orphan")


class TaskArtifact(Base):
    __tablename__ = "task_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("video_tasks.id"), index=True)
    artifact_type: Mapped[str] = mapped_column(String(50))
    storage_key: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    task: Mapped[VideoTask] = relationship(back_populates="artifacts")


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("video_tasks.id"), unique=True)
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    segments_json: Mapped[list[dict]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    task: Mapped[VideoTask] = relationship(back_populates="transcript")


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("video_tasks.id"), unique=True)
    summary_text: Mapped[str] = mapped_column(Text)
    key_points_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    timeline_json: Mapped[list[dict]] = mapped_column(JSON, default=list)
    title_suggestion: Mapped[str | None] = mapped_column(String(300), nullable=True)
    tags_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    task: Mapped[VideoTask] = relationship(back_populates="summary")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100))
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    source_platform: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hit_rule: Mapped[str | None] = mapped_column(String(100), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SiteRule(Base):
    __tablename__ = "site_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform: Mapped[str] = mapped_column(String(100), unique=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
