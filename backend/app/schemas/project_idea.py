from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.project_idea import ProjectIdeaStatus
from app.schemas.user import UserOut


class ProjectIdeaCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1)


class ProjectIdeaStatusUpdate(BaseModel):
    status: ProjectIdeaStatus


class ProjectIdeaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: ProjectIdeaStatus
    author: UserOut | None
    created_at: datetime
    updated_at: datetime
