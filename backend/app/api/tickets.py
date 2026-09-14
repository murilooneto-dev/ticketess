from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.models.ticket import TicketPriority, TicketStatus
from app.schemas.ticket import (
    TicketAttachmentOut,
    TicketCommentCreate,
    TicketCommentOut,
    TicketCreate,
    TicketHistoryOut,
    TicketListItemOut,
    TicketOut,
    TicketUpdateIn,
)
from app.services.ticket_service import (
    FileTooLargeError,
    ProjectNotFoundError,
    TicketAlreadyFinalizedError,
    TicketNotFinalizableError,
    TicketNotFoundError,
    add_comment,
    create_ticket,
    finalize_ticket,
    get_attachment,
    get_ticket,
    list_attachments,
    list_comments,
    list_history,
    list_tickets,
    save_attachment,
    attachment_file_path,
    update_ticket,
)

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


def _get_ticket_or_404(db: DbSession, ticket_id: int):
    ticket = get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    return ticket


@router.get("", response_model=list[TicketListItemOut])
def get_tickets(
    project_id: int | None = Query(default=None),
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    priority: TicketPriority | None = Query(default=None),
    finalized: bool = Query(default=False),
    db: DbSession = Depends(get_db),
):
    return list_tickets(db, project_id=project_id, status=status_filter, priority=priority, finalized=finalized)


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def post_ticket(
    payload: TicketCreate,
    db: DbSession = Depends(get_db),
):
    try:
        return create_ticket(db, payload)
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Projeto informado não existe")


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket_detail(
    ticket_id: int,
    db: DbSession = Depends(get_db),
):
    return _get_ticket_or_404(db, ticket_id)


@router.put("/{ticket_id}", response_model=TicketOut)
def put_ticket(
    ticket_id: int,
    payload: TicketUpdateIn,
    db: DbSession = Depends(get_db),
):
    try:
        return update_ticket(db, ticket_id, payload)
    except TicketNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    except TicketAlreadyFinalizedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Não é possível editar uma solicitação já finalizada"
        )


@router.post("/{ticket_id}/finalize", response_model=TicketOut)
def post_finalize_ticket(
    ticket_id: int,
    db: DbSession = Depends(get_db),
):
    try:
        return finalize_ticket(db, ticket_id)
    except TicketNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    except TicketNotFinalizableError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Só é possível finalizar solicitações concluídas ou canceladas",
        )
    except TicketAlreadyFinalizedError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solicitação já finalizada")


@router.get("/{ticket_id}/comments", response_model=list[TicketCommentOut])
def get_comments(
    ticket_id: int,
    db: DbSession = Depends(get_db),
):
    _get_ticket_or_404(db, ticket_id)
    return list_comments(db, ticket_id)


@router.post("/{ticket_id}/comments", response_model=TicketCommentOut, status_code=status.HTTP_201_CREATED)
def post_comment(
    ticket_id: int,
    payload: TicketCommentCreate,
    db: DbSession = Depends(get_db),
):
    _get_ticket_or_404(db, ticket_id)
    try:
        return add_comment(db, ticket_id, payload)
    except TicketNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")


@router.get("/{ticket_id}/history", response_model=list[TicketHistoryOut])
def get_history(
    ticket_id: int,
    db: DbSession = Depends(get_db),
):
    _get_ticket_or_404(db, ticket_id)
    return list_history(db, ticket_id)


@router.get("/{ticket_id}/attachments", response_model=list[TicketAttachmentOut])
def get_attachments(
    ticket_id: int,
    db: DbSession = Depends(get_db),
):
    _get_ticket_or_404(db, ticket_id)
    return list_attachments(db, ticket_id)


@router.post("/{ticket_id}/attachments", response_model=TicketAttachmentOut, status_code=status.HTTP_201_CREATED)
async def post_attachment(
    ticket_id: int,
    file: UploadFile = File(...),
    db: DbSession = Depends(get_db),
):
    _get_ticket_or_404(db, ticket_id)
    content = await file.read()
    try:
        return save_attachment(db, ticket_id, file.filename or "arquivo", file.content_type, content)
    except TicketNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    except FileTooLargeError:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Arquivo excede o tamanho máximo permitido"
        )


@router.get("/{ticket_id}/attachments/{attachment_id}/download")
def download_attachment(
    ticket_id: int,
    attachment_id: int,
    db: DbSession = Depends(get_db),
):
    _get_ticket_or_404(db, ticket_id)
    attachment = get_attachment(db, ticket_id, attachment_id)
    if attachment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anexo não encontrado")

    file_path = attachment_file_path(attachment)
    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo não encontrado no armazenamento")

    return FileResponse(
        file_path, filename=attachment.original_filename, media_type=attachment.content_type or "application/octet-stream"
    )
