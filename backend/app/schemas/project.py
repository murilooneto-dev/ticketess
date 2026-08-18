from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, computed_field

from app.models.project import ProjectStatus
from app.schemas.user import UserOut

GithubRepoField = Annotated[
    str,
    StringConstraints(strip_whitespace=True, pattern=r"^[\w.-]+/[\w.-]+$", max_length=200),
]

GithubTokenField = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None
    status: ProjectStatus = ProjectStatus.ATIVO
    manager_id: int | None = None
    github_repo: GithubRepoField | None = None
    github_token: GithubTokenField | None = None


class ProjectUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = None
    status: ProjectStatus | None = None
    manager_id: int | None = None
    github_repo: GithubRepoField | None = None
    github_token: GithubTokenField | None = None
    clear_github_token: bool = False


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    status: ProjectStatus
    manager: UserOut | None
    github_repo: str | None
    github_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime

    # o valor do token nunca é exposto pela API; só se existe um configurado
    github_token: str | None = Field(default=None, exclude=True, repr=False)

    @computed_field
    @property
    def has_github_token(self) -> bool:
        return bool(self.github_token)


class ProjectProgressUpdateCreate(BaseModel):
    message: str = Field(min_length=1)


class ProjectProgressUpdateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    author: UserOut | None
    message: str
    created_at: datetime
