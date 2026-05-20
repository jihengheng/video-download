from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DBSession, require_admin
from app.core.errors import user_error
from app.models import User
from app.repos.tasks import list_tasks
from app.schemas.admin import BanUserRequest, SiteRuleRequest
from app.schemas.common import MessageResponse
from app.schemas.task import TaskListResponse, TaskResponse
from app.services.admin import ban_user, upsert_site_rule

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/tasks", response_model=TaskListResponse)
def admin_tasks(db: DBSession, _: User = Depends(require_admin)) -> TaskListResponse:
    items, total = list_tasks(db, user_id=None, offset=0, limit=100)
    return TaskListResponse(items=[TaskResponse.model_validate(item) for item in items], total=total)


@router.post("/site-rules", response_model=MessageResponse)
def admin_site_rules(payload: SiteRuleRequest, db: DBSession, _: User = Depends(require_admin)) -> MessageResponse:
    upsert_site_rule(db, payload.platform, payload.is_enabled, payload.note)
    return MessageResponse(message="Site rule updated")


@router.post("/users/{user_id}/ban", response_model=MessageResponse)
def admin_ban_user(user_id: int, payload: BanUserRequest, db: DBSession, _: User = Depends(require_admin)) -> MessageResponse:
    user = ban_user(db, user_id, payload.is_banned)
    if user is None:
        raise user_error(status.HTTP_404_NOT_FOUND, "未找到对应用户。")
    return MessageResponse(message="User status updated")
