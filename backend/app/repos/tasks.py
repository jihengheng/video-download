from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Summary, TaskArtifact, Transcript, VideoTask


def create_task(db: Session, task: VideoTask) -> VideoTask:
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: int) -> VideoTask | None:
    return db.scalar(
        select(VideoTask)
        .options(
            selectinload(VideoTask.artifacts),
            selectinload(VideoTask.summary),
            selectinload(VideoTask.transcript),
        )
        .where(VideoTask.id == task_id)
    )


def get_task_by_public_token(db: Session, task_id: int, public_token: str) -> VideoTask | None:
    return db.scalar(
        select(VideoTask)
        .options(
            selectinload(VideoTask.artifacts),
            selectinload(VideoTask.summary),
            selectinload(VideoTask.transcript),
        )
        .where(VideoTask.id == task_id, VideoTask.public_token == public_token)
    )


def list_tasks(db: Session, user_id: int | None, offset: int = 0, limit: int = 20) -> tuple[list[VideoTask], int]:
    stmt = select(VideoTask).options(selectinload(VideoTask.artifacts)).order_by(VideoTask.created_at.desc())
    count_stmt = select(func.count(VideoTask.id))
    if user_id is not None:
        stmt = stmt.where(VideoTask.user_id == user_id)
        count_stmt = count_stmt.where(VideoTask.user_id == user_id)
    items = list(db.scalars(stmt.offset(offset).limit(limit)))
    total = db.scalar(count_stmt) or 0
    return items, total


def mark_task_deleted(db: Session, task: VideoTask) -> VideoTask:
    task.status = "deleted"
    task.updated_at = datetime.now(UTC)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def save_transcript(db: Session, task: VideoTask, language: str | None, text: str, segments: list[dict]) -> Transcript:
    transcript = task.transcript or Transcript(task_id=task.id, language=language, text=text, segments_json=segments)
    transcript.language = language
    transcript.text = text
    transcript.segments_json = segments
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    return transcript


def save_summary(
    db: Session,
    task: VideoTask,
    summary_text: str,
    key_points: list[str],
    timeline: list[dict],
    title_suggestion: str | None,
    tags: list[str],
) -> Summary:
    summary = task.summary or Summary(task_id=task.id, summary_text=summary_text, key_points_json=key_points, timeline_json=timeline)
    summary.summary_text = summary_text
    summary.key_points_json = key_points
    summary.timeline_json = timeline
    summary.title_suggestion = title_suggestion
    summary.tags_json = tags
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


def add_artifact(
    db: Session,
    task: VideoTask,
    artifact_type: str,
    storage_key: str,
    mime_type: str,
    size_bytes: int | None = None,
    metadata_json: dict | None = None,
) -> TaskArtifact:
    artifact = TaskArtifact(
        task_id=task.id,
        artifact_type=artifact_type,
        storage_key=storage_key,
        mime_type=mime_type,
        size_bytes=size_bytes,
        metadata_json=metadata_json or {},
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact
