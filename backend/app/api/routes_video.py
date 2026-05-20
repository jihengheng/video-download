import mimetypes
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse

from app.api.deps import DBSession, get_current_user
from app.models import AuditLog, SiteRule, User
from app.schemas.video import DirectDownloadRequest, VideoInspectRequest, VideoInspectResponse
from app.services.media import InspectorService, YtDlpMediaService

router = APIRouter(prefix="/video", tags=["video"])


@router.post("/inspect", response_model=VideoInspectResponse)
def inspect_video(
    payload: VideoInspectRequest,
    request: Request,
    db: DBSession,
    user: User | None = Depends(get_current_user),
) -> VideoInspectResponse:
    result = InspectorService().inspect(str(payload.url))
    db.add(
        AuditLog(
            user_id=user.id if user else None,
            action="inspect_video",
            ip_address=request.client.host if request.client else None,
            source_url=str(payload.url),
            source_platform=result["source_platform"],
            success=True,
        )
    )
    db.commit()
    return VideoInspectResponse(**result)


@router.post("/download")
def direct_download_video(
    payload: DirectDownloadRequest,
    request: Request,
    db: DBSession,
    user: User | None = Depends(get_current_user),
):
    workspace = Path("storage/direct_downloads")
    workspace.mkdir(parents=True, exist_ok=True)
    info, video_path = YtDlpMediaService().download_selected_format(
        str(payload.url),
        payload.format_id,
        workspace,
    )
    db.add(
        AuditLog(
            user_id=user.id if user else None,
            action="direct_download_video",
            ip_address=request.client.host if request.client else None,
            source_url=str(payload.url),
            source_platform=(info.get("extractor_key") or "unknown").lower(),
            success=True,
            details_json={"format_id": payload.format_id, "filename": video_path.name},
        )
    )
    db.commit()

    media_type = mimetypes.guess_type(video_path.name)[0] or "application/octet-stream"
    return FileResponse(
        path=video_path,
        media_type=media_type,
        filename=video_path.name,
    )
