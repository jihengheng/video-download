from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class CreateTaskRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    format_id: str = Field(min_length=1, max_length=100)
    need_summary: bool = True


class RetryTaskResponse(BaseModel):
    task_id: int
    status: str


class ArtifactResponse(ORMModel):
    artifact_type: str
    storage_key: str
    download_url: str | None = None
    mime_type: str
    size_bytes: int | None = None


class TaskResponse(ORMModel):
    id: int
    source_url: str
    source_platform: str
    video_title: str
    thumbnail_url: str | None = None
    duration_seconds: int | None = None
    selected_format_id: str | None = None
    public_token: str
    need_summary: bool
    status: str
    progress: int
    retry_count: int
    error_code: str | None = None
    error_message: str | None = None
    can_retry: bool
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    artifacts: list[ArtifactResponse] = []


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int


class SummaryResultResponse(BaseModel):
    task_id: int
    summary: str
    key_points: list[str]
    timeline: list[dict]
    title_suggestion: str | None = None
    tags: list[str]
    transcript: str
    transcript_segments: list[dict]
    artifacts: list[ArtifactResponse]
