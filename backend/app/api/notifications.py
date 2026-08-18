from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.models.user import User
from app.schemas.notification import NotificationOut, UnreadCountOut
from app.security.dependencies import get_current_user
from app.services.notification_service import (
    NotificationNotFoundError,
    list_notifications,
    mark_all_read,
    mark_read,
    unread_count,
)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def get_notifications(
    unread_only: bool = Query(default=False),
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_notifications(db, current_user.id, unread_only=unread_only)


@router.get("/unread-count", response_model=UnreadCountOut)
def get_unread_count(
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return UnreadCountOut(unread_count=unread_count(db, current_user.id))


@router.post("/{notification_id}/read", response_model=NotificationOut)
def post_mark_read(
    notification_id: int,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return mark_read(db, current_user.id, notification_id)
    except NotificationNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificação não encontrada")


@router.post("/read-all")
def post_mark_all_read(
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mark_all_read(db, current_user.id)
    return {"detail": "Todas as notificações foram marcadas como lidas"}
