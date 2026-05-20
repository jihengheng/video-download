from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.deps import DBSession, get_current_user, require_user
from app.core.errors import user_error
from app.models import User
from app.repos.tasks import get_task, list_tasks, mark_task_deleted
from app.schemas.common import MessageResponse
from app.schemas.task import CreateTaskRequest, RetryTaskResponse, SummaryResultResponse, TaskListResponse, TaskResponse
from app.services.media import InspectorService
from app.services.quota import consume_quota_or_raise
from app.services.storage import LocalObjectStorage
from app.services.tasks import TaskPipeline

router = APIRouter(prefix="/tasks", tags=["tasks"])
storage = LocalObjectStorage()


def _resolve_task_access(
    db: DBSession,
    task_id: int,
    user: User | None,
    access_token: str | None,
):
    task = get_task(db, task_id)
    if task is None:
        raise user_error(status.HTTP_404_NOT_FOUND, "未找到对应任务。")
    if user is not None and task.user_id == user.id:
        return task
    if access_token and task.public_token == access_token:
        return task
    raise user_error(status.HTTP_404_NOT_FOUND, "未找到对应任务。")


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_video_task(
    payload: CreateTaskRequest,
    request: Request,
    db: DBSession,
    user: User | None = Depends(get_current_user),
) -> TaskResponse:
    consume_quota_or_raise(db, user, request.client.host if request.client else None, payload.url)
    inspected = InspectorService().inspect(payload.url)
    task = TaskPipeline().create_from_inspection(db, user, inspected, payload.url, payload.format_id, payload.need_summary)
    task = TaskPipeline().process_task(db, task.id)
    return TaskResponse.model_validate(task)


@router.get("", response_model=TaskListResponse)
def get_tasks(
    db: DBSession,
    user: User = Depends(require_user),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> TaskListResponse:
    items, total = list_tasks(db, user.id, offset, limit)
    return TaskListResponse(items=[TaskResponse.model_validate(item) for item in items], total=total)


@router.get("/{task_id}", response_model=TaskResponse)
def get_video_task(
    task_id: int,
    db: DBSession,
    access_token: str | None = Query(default=None),
    user: User | None = Depends(get_current_user),
) -> TaskResponse:
    task = _resolve_task_access(db, task_id, user, access_token)
    return _build_task_response(task)


@router.post("/{task_id}/retry", response_model=RetryTaskResponse)
def retry_video_task(
    task_id: int,
    db: DBSession,
    access_token: str | None = Query(default=None),
    user: User | None = Depends(get_current_user),
) -> RetryTaskResponse:
    task = _resolve_task_access(db, task_id, user, access_token)
    retried = TaskPipeline().retry_task(db, task_id)
    return RetryTaskResponse(task_id=retried.id, status=retried.status)


@router.delete("/{task_id}", response_model=MessageResponse)
def delete_video_task(
    task_id: int,
    db: DBSession,
    access_token: str | None = Query(default=None),
    user: User | None = Depends(get_current_user),
) -> MessageResponse:
    task = _resolve_task_access(db, task_id, user, access_token)
    mark_task_deleted(db, task)
    return MessageResponse(message="Task deleted")


@router.get("/{task_id}/result", response_model=SummaryResultResponse)
def get_task_result(
    task_id: int,
    db: DBSession,
    access_token: str | None = Query(default=None),
    user: User | None = Depends(get_current_user),
) -> SummaryResultResponse:
    task = _resolve_task_access(db, task_id, user, access_token)
    if task.summary is None or task.transcript is None:
        raise user_error(status.HTTP_409_CONFLICT, "任务结果尚未生成，请稍后再试。")
    return SummaryResultResponse(
        task_id=task.id,
        summary=task.summary.summary_text,
        key_points=task.summary.key_points_json,
        timeline=task.summary.timeline_json,
        title_suggestion=task.summary.title_suggestion,
        tags=task.summary.tags_json,
        transcript=task.transcript.text,
        transcript_segments=task.transcript.segments_json,
        artifacts=[
            {
                "artifact_type": artifact.artifact_type,
                "storage_key": artifact.storage_key,
                "download_url": storage.public_url(artifact.storage_key),
                "mime_type": artifact.mime_type,
                "size_bytes": artifact.size_bytes,
            }
            for artifact in task.artifacts
        ],
    )


def _build_task_response(task) -> TaskResponse:
    return TaskResponse.model_validate(
        {
            "id": task.id,
            "source_url": task.source_url,
            "source_platform": task.source_platform,
            "video_title": task.video_title,
            "thumbnail_url": task.thumbnail_url,
            "duration_seconds": task.duration_seconds,
            "selected_format_id": task.selected_format_id,
            "public_token": task.public_token,
            "need_summary": task.need_summary,
            "status": task.status,
            "progress": task.progress,
            "retry_count": task.retry_count,
            "error_code": task.error_code,
            "error_message": task.error_message,
            "can_retry": task.can_retry,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "completed_at": task.completed_at,
            "artifacts": [
                {
                    "artifact_type": artifact.artifact_type,
                    "storage_key": artifact.storage_key,
                    "download_url": storage.public_url(artifact.storage_key),
                    "mime_type": artifact.mime_type,
                    "size_bytes": artifact.size_bytes,
                }
                for artifact in task.artifacts
            ],
        }
    )
