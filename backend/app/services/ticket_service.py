import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.config import settings
from app.models.project import Project
from app.models.ticket import Ticket, TicketAttachment, TicketComment, TicketHistory, TicketStatus
from app.schemas.ticket import TicketCommentCreate, TicketCreate, TicketUpdateIn


class TicketNotFoundError(Exception):
    pass


class ProjectNotFoundError(Exception):
    pass


class FileTooLargeError(Exception):
    pass


class TicketNotFinalizableError(Exception):
    pass


class TicketAlreadyFinalizedError(Exception):
    pass


TRACKED_FIELDS = ("status", "priority", "type")

FIELD_LABELS_PT = {"status": "Status", "priority": "Prioridade", "type": "Tipo"}


def _value_label(value) -> str:
    if value is None:
        return "—"
    return str(value).replace("_", " ").capitalize()


def _ticket_query():
    return select(Ticket)


def list_tickets(
    db: DbSession,
    project_id: int | None = None,
    status: str | None = None,
    priority: str | None = None,
    finalized: bool = False,
) -> list[Ticket]:
    query = _ticket_query().order_by(Ticket.created_at.desc())
    if project_id is not None:
        query = query.where(Ticket.project_id == project_id)
    if status is not None:
        query = query.where(Ticket.status == status)
    if priority is not None:
        query = query.where(Ticket.priority == priority)
    if finalized:
        query = query.where(Ticket.finalized_at.is_not(None))
    else:
        query = query.where(Ticket.finalized_at.is_(None))
    return list(db.execute(query).unique().scalars())


def get_ticket(db: DbSession, ticket_id: int) -> Ticket | None:
    query = _ticket_query().where(Ticket.id == ticket_id)
    return db.execute(query).unique().scalar_one_or_none()


def create_ticket(db: DbSession, data: TicketCreate) -> Ticket:
    project = db.get(Project, data.project_id)
    if project is None:
        raise ProjectNotFoundError(data.project_id)

    ticket = Ticket(
        project_id=data.project_id,
        requester_name=data.requester_name,
        title=data.title,
        description=data.description,
        type=data.type,
        priority=data.priority,
        status=data.status,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def update_ticket(db: DbSession, ticket_id: int, data: TicketUpdateIn) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError(ticket_id)
    if ticket.finalized_at is not None:
        raise TicketAlreadyFinalizedError(ticket_id)

    updates = data.model_dump(exclude_unset=True)

    for field in TRACKED_FIELDS:
        if field not in updates:
            continue
        new_value = updates[field]
        old_value = getattr(ticket, field)
        old_value = old_value.value if hasattr(old_value, "value") else old_value
        new_value_normalized = new_value.value if hasattr(new_value, "value") else new_value
        if old_value != new_value_normalized:
            db.add(
                TicketHistory(
                    ticket_id=ticket.id,
                    field=field,
                    old_value=str(old_value) if old_value is not None else None,
                    new_value=str(new_value_normalized) if new_value_normalized is not None else None,
                )
            )

    if "title" in updates:
        ticket.title = updates["title"]
    if "description" in updates:
        ticket.description = updates["description"]
    if "requester_name" in updates:
        ticket.requester_name = updates["requester_name"]
    if "type" in updates:
        ticket.type = updates["type"]
    if "priority" in updates:
        ticket.priority = updates["priority"]
    if "status" in updates:
        ticket.status = updates["status"]

    db.commit()
    db.refresh(ticket)
    return ticket


def finalize_ticket(db: DbSession, ticket_id: int) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError(ticket_id)
    if ticket.status not in (TicketStatus.CONCLUIDO, TicketStatus.CANCELADO):
        raise TicketNotFinalizableError(ticket_id)
    if ticket.finalized_at is not None:
        raise TicketAlreadyFinalizedError(ticket_id)

    from datetime import datetime, timezone

    ticket.finalized_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ticket)
    return ticket


def add_comment(db: DbSession, ticket_id: int, data: TicketCommentCreate) -> TicketComment:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError(ticket_id)

    comment = TicketComment(ticket_id=ticket_id, message=data.message)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def list_comments(db: DbSession, ticket_id: int) -> list[TicketComment]:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError(ticket_id)

    query = (
        select(TicketComment)
        .where(TicketComment.ticket_id == ticket_id)
        .order_by(TicketComment.created_at)
    )
    return list(db.execute(query).unique().scalars())


def list_history(db: DbSession, ticket_id: int) -> list[TicketHistory]:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError(ticket_id)

    query = (
        select(TicketHistory)
        .where(TicketHistory.ticket_id == ticket_id)
        .order_by(TicketHistory.created_at.desc())
    )
    return list(db.execute(query).unique().scalars())


def ticket_storage_dir(ticket_id: int) -> Path:
    directory = settings.storage_dir / "tickets" / str(ticket_id)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def save_attachment(
    db: DbSession,
    ticket_id: int,
    original_filename: str,
    content_type: str | None,
    content: bytes,
) -> TicketAttachment:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError(ticket_id)

    max_bytes = settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise FileTooLargeError(len(content))

    extension = Path(original_filename).suffix
    stored_filename = f"{uuid.uuid4().hex}{extension}"
    destination = ticket_storage_dir(ticket_id) / stored_filename
    destination.write_bytes(content)

    attachment = TicketAttachment(
        ticket_id=ticket_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        content_type=content_type,
        size_bytes=len(content),
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


def list_attachments(db: DbSession, ticket_id: int) -> list[TicketAttachment]:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError(ticket_id)

    query = (
        select(TicketAttachment)
        .where(TicketAttachment.ticket_id == ticket_id)
        .order_by(TicketAttachment.created_at)
    )
    return list(db.execute(query).unique().scalars())


def get_attachment(db: DbSession, ticket_id: int, attachment_id: int) -> TicketAttachment | None:
    query = select(TicketAttachment).where(
        TicketAttachment.id == attachment_id, TicketAttachment.ticket_id == ticket_id
    )
    return db.execute(query).scalar_one_or_none()


def attachment_file_path(attachment: TicketAttachment) -> Path:
    return ticket_storage_dir(attachment.ticket_id) / attachment.stored_filename
