from __future__ import annotations

from fastapi import HTTPException, status
from app.core.errors import user_error


class TranscriptionService:
    def transcribe_from_subtitles(self, transcript_text: str | None, segments: list[dict]) -> dict:
        if not transcript_text:
            raise user_error(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "当前视频没有可用字幕或自动字幕。DeepSeek 单模型模式下，只有带字幕的视频才能生成摘要。",
            )
        return {
            "language": None,
            "text": transcript_text,
            "segments": segments,
        }
