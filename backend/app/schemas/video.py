from pydantic import BaseModel, Field, HttpUrl


class VideoInspectRequest(BaseModel):
    url: HttpUrl


class DirectDownloadRequest(BaseModel):
    url: HttpUrl
    format_id: str = Field(min_length=1, max_length=100)


class VideoFormatOption(BaseModel):
    format_id: str
    ext: str
    resolution: str
    filesize_mb: float | None = None
    note: str | None = None
    has_video: bool = False
    has_audio: bool = False


class VideoInspectResponse(BaseModel):
    title: str
    thumbnail_url: str | None = None
    duration_seconds: int | None = None
    source_platform: str
    supports_summary: bool
    estimated_processing_minutes: int
    formats: list[VideoFormatOption]
