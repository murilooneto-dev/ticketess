from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.services.email_service import send_email


class NotificationNotFoundError(Exception):
    pass


def notify_users(
    db: DbSession,
    users: list[User],
    notif_type: NotificationType,
    title: str,
    message: str,
    link: str | None = None,
    exclude_user_id: int | None = None,
) -> None:
    for user in users:
        if user.id == exclude_user_id:
            continue

        db.add(
            Notification(
                user_id=user.id,
                type=notif_type,
                title=title,
                message=message,
                link=link,
            )
        )
        if user.email:
            send_email(user.email, title, message)

    db.commit()


def list_notifications(db: DbSession, user_id: int, unread_only: bool = False) -> list[Notification]:
    query = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        query = query.where(Notification.is_read.is_(False))
    query = query.order_by(Notification.created_at.desc())
    return list(db.execute(query).scalars())


def unread_count(db: DbSession, user_id: int) -> int:
    query = select(func.count()).select_from(Notification).where(
        Notification.user_id == user_id, Notification.is_read.is_(False)
    )
    return db.execute(query).scalar_one()


def mark_read(db: DbSession, user_id: int, notification_id: int) -> Notification:
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != user_id:
        raise NotificationNotFoundError(notification_id)

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_read(db: DbSession, user_id: int) -> None:
    query = select(Notification).where(Notification.user_id == user_id, Notification.is_read.is_(False))
    for notification in db.execute(query).scalars():
        notification.is_read = True
    db.commit()
