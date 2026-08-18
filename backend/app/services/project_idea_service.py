from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession, joinedload

from app.models.notification import NotificationType
from app.models.project_idea import ProjectIdea, ProjectIdeaStatus
from app.models.user import User, UserRole
from app.schemas.project_idea import ProjectIdeaCreate
from app.services.notification_service import notify_users
from app.services.user_service import list_admins

STATUS_LABELS_PT = {
    ProjectIdeaStatus.PENDENTE: "pendente",
    ProjectIdeaStatus.APROVADA: "aprovada",
    ProjectIdeaStatus.REJEITADA: "rejeitada",
}


class ProjectIdeaNotFoundError(Exception):
    pass


def _idea_query():
    return select(ProjectIdea).options(joinedload(ProjectIdea.author))


def create_project_idea(db: DbSession, author_id: int, data: ProjectIdeaCreate) -> ProjectIdea:
    idea = ProjectIdea(title=data.title, description=data.description, created_by=author_id)
    db.add(idea)
    db.commit()
    db.refresh(idea)

    admins = list_admins(db)
    notify_users(
        db,
        admins,
        NotificationType.PROJECT_IDEA_CREATED,
        title=f"Nova ideia de projeto: {idea.title}",
        message=f"{idea.author.name if idea.author else 'Alguém'} sugeriu o projeto \"{idea.title}\".",
        link="/project-ideas",
        exclude_user_id=author_id,
    )
    return idea


def list_project_ideas(db: DbSession, current_user: User) -> list[ProjectIdea]:
    query = _idea_query().order_by(ProjectIdea.created_at.desc())
    if current_user.role != UserRole.ADMIN:
        query = query.where(ProjectIdea.created_by == current_user.id)
    return list(db.execute(query).unique().scalars())


def update_project_idea_status(
    db: DbSession, idea_id: int, status: ProjectIdeaStatus, actor_id: int
) -> ProjectIdea:
    idea = db.execute(_idea_query().where(ProjectIdea.id == idea_id)).unique().scalar_one_or_none()
    if idea is None:
        raise ProjectIdeaNotFoundError(idea_id)

    previous_status = idea.status
    idea.status = status
    db.commit()
    db.refresh(idea)

    if previous_status != status and idea.author is not None:
        notify_users(
            db,
            [idea.author],
            NotificationType.PROJECT_IDEA_STATUS_CHANGED,
            title=f"Ideia de projeto {STATUS_LABELS_PT[status]}: {idea.title}",
            message=f"Sua ideia \"{idea.title}\" foi marcada como {STATUS_LABELS_PT[status]}.",
            link="/project-ideas",
            exclude_user_id=actor_id,
        )
    return idea
