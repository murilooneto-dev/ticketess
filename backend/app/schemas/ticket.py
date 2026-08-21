from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.ticket import TicketPriority, TicketStatus, TicketType
from app.schemas.user import UserOut


class TicketCreate(BaseModel):
    project_id: int
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    type: TicketType = TicketType.OUTRO
    priority: TicketPriority = TicketPriority.MEDIA


class TicketUpdateIn(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    type: TicketType | None = None
    priority: TicketPriority | None = None
    status: TicketStatus | None = None


class TicketListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    type: TicketType
    priority: TicketPriority
    status: TicketStatus
    author: UserOut | None
    created_at: datetime
    updated_at: datetime
    finalized_at: datetime | None


class TicketOut(TicketListItemOut):
    description: str | None


class TicketCommentCreate(BaseModel):
    message: str = Field(min_length=1)


class TicketCommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    author: UserOut | None
    message: str
    created_at: datetime


class TicketAttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    original_filename: str
    content_type: str | None
    size_bytes: int
    uploader: UserOut | None
    created_at: datetime


class TicketHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    field: str
    old_value: str | None
    new_value: str | None
    author: UserOut | None
    created_at: datetime
