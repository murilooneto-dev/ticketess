from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.project_idea import ProjectIdeaStatus


class ProjectIdeaCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1)
    project_id: int


class ProjectIdeaStatusUpdate(BaseModel):
    status: ProjectIdeaStatus
    project_id: int | None = None
    rejection_reason: str | None = None


class ProjectIdeaProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ProjectIdeaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: ProjectIdeaStatus
    project: ProjectIdeaProjectOut | None
    rejection_reason: str | None
    generated_ticket_id: int | None
    created_at: datetime
    updated_at: datetime
