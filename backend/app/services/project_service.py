from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.models.project import Project, ProjectUpdate
from app.schemas.project import ProjectCreate, ProjectProgressUpdateCreate, ProjectUpdateIn


class ProjectNotFoundError(Exception):
    pass


def list_projects(db: DbSession) -> list[Project]:
    query = select(Project).order_by(Project.created_at.desc())
    return list(db.execute(query).unique().scalars())


def get_project(db: DbSession, project_id: int) -> Project | None:
    return db.get(Project, project_id)


def create_project(db: DbSession, data: ProjectCreate) -> Project:
    project = Project(
        name=data.name,
        description=data.description,
        status=data.status,
        github_repo=data.github_repo,
        github_token=data.github_token,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update_project(db: DbSession, project_id: int, data: ProjectUpdateIn) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise ProjectNotFoundError(project_id)

    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    if data.status is not None:
        project.status = data.status
    if "github_repo" in data.model_fields_set:
        project.github_repo = data.github_repo
    if data.clear_github_token:
        project.github_token = None
    elif data.github_token is not None:
        project.github_token = data.github_token

    db.commit()
    db.refresh(project)
    return project


def delete_project(db: DbSession, project_id: int) -> None:
    project = db.get(Project, project_id)
    if project is None:
        raise ProjectNotFoundError(project_id)

    db.delete(project)
    db.commit()


def add_progress_update(db: DbSession, project_id: int, data: ProjectProgressUpdateCreate) -> ProjectUpdate:
    project = db.get(Project, project_id)
    if project is None:
        raise ProjectNotFoundError(project_id)

    update = ProjectUpdate(project_id=project_id, message=data.message)
    db.add(update)
    db.commit()
    db.refresh(update)
    return update


def list_progress_updates(db: DbSession, project_id: int) -> list[ProjectUpdate]:
    project = db.get(Project, project_id)
    if project is None:
        raise ProjectNotFoundError(project_id)

    query = (
        select(ProjectUpdate)
        .where(ProjectUpdate.project_id == project_id)
        .order_by(ProjectUpdate.created_at.desc())
    )
    return list(db.execute(query).unique().scalars())
