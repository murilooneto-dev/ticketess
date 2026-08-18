from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession, joinedload

from app.models.notification import NotificationType
from app.models.project import Project, ProjectUpdate
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectProgressUpdateCreate, ProjectUpdateIn
from app.services.notification_service import notify_users


class ProjectNotFoundError(Exception):
    pass


class InvalidManagerError(Exception):
    pass


def _validate_manager(db: DbSession, manager_id: int | None) -> None:
    if manager_id is None:
        return
    manager = db.get(User, manager_id)
    if manager is None:
        raise InvalidManagerError(manager_id)


def list_projects(db: DbSession, manager_id: int | None = None) -> list[Project]:
    query = select(Project).options(joinedload(Project.manager)).order_by(Project.created_at.desc())
    if manager_id is not None:
        query = query.where(Project.manager_id == manager_id)
    return list(db.execute(query).unique().scalars())


def get_project(db: DbSession, project_id: int) -> Project | None:
    query = select(Project).options(joinedload(Project.manager)).where(Project.id == project_id)
    return db.execute(query).unique().scalar_one_or_none()


def create_project(db: DbSession, data: ProjectCreate) -> Project:
    _validate_manager(db, data.manager_id)

    project = Project(
        name=data.name,
        description=data.description,
        status=data.status,
        manager_id=data.manager_id,
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

    if data.manager_id is not None:
        _validate_manager(db, data.manager_id)

    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    if data.status is not None:
        project.status = data.status
    if "manager_id" in data.model_fields_set:
        project.manager_id = data.manager_id
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


def add_progress_update(
    db: DbSession, project_id: int, author_id: int, data: ProjectProgressUpdateCreate
) -> ProjectUpdate:
    project = db.get(Project, project_id)
    if project is None:
        raise ProjectNotFoundError(project_id)

    update = ProjectUpdate(project_id=project_id, author_id=author_id, message=data.message)
    db.add(update)
    db.commit()
    db.refresh(update)

    if project.manager_id is not None:
        manager = db.get(User, project.manager_id)
        if manager is not None:
            preview = data.message if len(data.message) <= 140 else f"{data.message[:140]}..."
            notify_users(
                db,
                [manager],
                NotificationType.PROJECT_UPDATE,
                title=f"Novo andamento em: {project.name}",
                message=preview,
                link=f"/projects/{project.id}",
                exclude_user_id=author_id,
            )

    return update


def list_progress_updates(db: DbSession, project_id: int) -> list[ProjectUpdate]:
    project = db.get(Project, project_id)
    if project is None:
        raise ProjectNotFoundError(project_id)

    query = (
        select(ProjectUpdate)
        .options(joinedload(ProjectUpdate.author))
        .where(ProjectUpdate.project_id == project_id)
        .order_by(ProjectUpdate.created_at.desc())
    )
    return list(db.execute(query).unique().scalars())
