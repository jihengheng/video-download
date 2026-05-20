from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.errors import user_error
from app.models import AuditLog, TaskStatus, User, VideoTask
from app.repos.tasks import add_artifact, create_task, get_task, save_summary, save_transcript
from app.services.media import InspectorService, YtDlpMediaService, ensure_workspace, normalize_duration_seconds, normalize_thumbnail_url, write_manifest
from app.services.storage import LocalObjectStorage
from app.services.summarization import SummarizationService
from app.services.transcription import TranscriptionService


class TaskPipeline:
    def __init__(self) -> None:
        self.storage = LocalObjectStorage()
        self.media = YtDlpMediaService()
        self.transcription = TranscriptionService()
        self.summarization = SummarizationService()

    def create_from_inspection(
        self,
        db: Session,
        user: User | None,
        inspected: dict,
        url: str,
        format_id: str,
        need_summary: bool,
    ) -> VideoTask:
        task = VideoTask(
            user_id=user.id if user else None,
            source_url=url,
            source_platform=inspected["source_platform"],
            video_title=inspected["title"],
            thumbnail_url=inspected.get("thumbnail_url"),
            duration_seconds=inspected.get("duration_seconds"),
            selected_format_id=format_id,
            need_summary=need_summary,
            status=TaskStatus.pending.value,
            progress=5,
        )
        task = create_task(db, task)
        db.add(
            AuditLog(
                user_id=user.id if user else None,
                action="task_created",
                source_url=url,
                source_platform=task.source_platform,
                success=True,
                details_json={"task_id": task.id, "format_id": format_id},
            )
        )
        db.commit()
        return task

    def process_task(self, db: Session, task_id: int) -> VideoTask:
        task = get_task(db, task_id)
        if task is None:
            raise user_error(status.HTTP_404_NOT_FOUND, "未找到对应任务。")

        workspace = ensure_workspace(task.id)
        self._transition(db, task, TaskStatus.parsing, 15)
        inspect_info = self.media.extract_info(task.source_url, download=False)
        manifest_key = f"tasks/{task.id}/manifest.json"
        manifest_path = self.storage.root / manifest_key
        write_manifest(
            manifest_path,
            {
                "task_id": task.id,
                "source_url": task.source_url,
                "source_platform": task.source_platform,
                "selected_format_id": task.selected_format_id,
                "inspect_info": {
                    "id": inspect_info.get("id"),
                    "title": inspect_info.get("title"),
                    "duration": inspect_info.get("duration"),
                    "extractor_key": inspect_info.get("extractor_key"),
                },
            },
        )
        add_artifact(db, task, "manifest", manifest_key, "application/json")

        self._transition(db, task, TaskStatus.downloading, 35)
        download_dir = workspace / "download"
        info, video_path = self.media.download_selected_format(task.source_url, task.selected_format_id or "best", download_dir)
        task.video_title = info.get("title") or task.video_title
        task.thumbnail_url = normalize_thumbnail_url(info.get("thumbnail")) or task.thumbnail_url
        task.duration_seconds = normalize_duration_seconds(info.get("duration")) or task.duration_seconds
        db.add(task)
        db.commit()
        db.refresh(task)

        video_key = f"tasks/{task.id}/video/{video_path.name}"
        stored_video_path = self.storage.write_bytes(video_key, video_path.read_bytes())
        add_artifact(db, task, "video", video_key, _mime_for_suffix(video_path.suffix), stored_video_path.stat().st_size)

        self._transition(db, task, TaskStatus.transcribing, 60)
        subtitle_text, subtitle_segments = self.media.extract_subtitle_text(info, workspace / "subtitles")
        transcript_payload = self.transcription.transcribe_from_subtitles(subtitle_text, subtitle_segments)
        save_transcript(
            db,
            task,
            transcript_payload["language"],
            transcript_payload["text"],
            transcript_payload["segments"],
        )

        if task.need_summary:
            self._transition(db, task, TaskStatus.summarizing, 82)
            summary_payload = self.summarization.summarize(transcript_payload["text"], transcript_payload["segments"])
            save_summary(
                db,
                task,
                summary_payload["summary"],
                summary_payload["key_points"],
                summary_payload["timeline"],
                summary_payload["title_suggestion"],
                summary_payload["tags"],
            )

        note_key = f"tasks/{task.id}/notes/summary.md"
        note_body = self._build_export_note(task.video_title, transcript_payload["text"], task.summary.summary_text if task.summary else "")
        note_path = self.storage.write_bytes(note_key, note_body.encode("utf-8"))
        add_artifact(db, task, "notes", note_key, "text/markdown", note_path.stat().st_size)

        task.status = TaskStatus.completed.value
        task.progress = 100
        task.completed_at = datetime.now(UTC)
        task.updated_at = datetime.now(UTC)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def retry_task(self, db: Session, task_id: int) -> VideoTask:
        task = get_task(db, task_id)
        if task is None:
            raise user_error(status.HTTP_404_NOT_FOUND, "未找到对应任务。")
        if not task.can_retry:
            raise user_error(status.HTTP_400_BAD_REQUEST, "当前任务不支持重试。")
        task.status = TaskStatus.pending.value
        task.progress = 5
        task.error_code = None
        task.error_message = None
        task.retry_count += 1
        db.add(task)
        db.commit()
        db.refresh(task)
        return self.process_task(db, task.id)

    def _build_export_note(self, title: str, transcript_text: str, summary_text: str) -> str:
        return f"# {title}\n\n## Summary\n\n{summary_text}\n\n## Transcript\n\n{transcript_text}\n"

    def _transition(self, db: Session, task: VideoTask, status_value: TaskStatus, progress: int) -> None:
        task.status = status_value.value
        task.progress = progress
        task.updated_at = datetime.now(UTC)
        db.add(task)
        db.commit()
        db.refresh(task)


def _mime_for_suffix(suffix: str) -> str:
    normalized = suffix.lower().lstrip(".")
    return {
        "mp4": "video/mp4",
        "webm": "video/webm",
        "mkv": "video/x-matroska",
    }.get(normalized, "application/octet-stream")
