from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession, joinedload

from app.models.project import Project
from app.models.project_idea import ProjectIdea, ProjectIdeaStatus
from app.schemas.project_idea import ProjectIdeaCreate


class ProjectIdeaNotFoundError(Exception):
    pass


class ProjectNotFoundError(Exception):
    pass


class ProjectIdeaMissingProjectError(Exception):
    pass


class ProjectIdeaRejectionReasonRequiredError(Exception):
    pass


def _idea_query():
    return select(ProjectIdea).options(joinedload(ProjectIdea.project))


def create_project_idea(db: DbSession, data: ProjectIdeaCreate) -> ProjectIdea:
    if db.get(Project, data.project_id) is None:
        raise ProjectNotFoundError(data.project_id)

    idea = ProjectIdea(title=data.title, description=data.description, project_id=data.project_id)
    db.add(idea)
    db.commit()
    db.refresh(idea)
    return idea


def list_project_ideas(db: DbSession) -> list[ProjectIdea]:
    query = _idea_query().order_by(ProjectIdea.created_at.desc())
    return list(db.execute(query).unique().scalars())


def update_project_idea_status(
    db: DbSession,
    idea_id: int,
    status: ProjectIdeaStatus,
    project_id: int | None = None,
    rejection_reason: str | None = None,
) -> ProjectIdea:
    idea = db.execute(_idea_query().where(ProjectIdea.id == idea_id)).unique().scalar_one_or_none()
    if idea is None:
        raise ProjectIdeaNotFoundError(idea_id)

    previous_status = idea.status
    if previous_status == status:
        return idea

    if status == ProjectIdeaStatus.APROVADA:
        from app.schemas.ticket import TicketCreate
        from app.services.ticket_service import create_ticket

        resolved_project_id = idea.project_id or project_id
        if resolved_project_id is None:
            raise ProjectIdeaMissingProjectError(idea_id)
        idea.project_id = resolved_project_id
        created_ticket = create_ticket(
            db,
            TicketCreate(project_id=resolved_project_id, title=idea.title, description=idea.description),
        )
        idea.generated_ticket_id = created_ticket.id
    elif status == ProjectIdeaStatus.REJEITADA:
        if not rejection_reason or not rejection_reason.strip():
            raise ProjectIdeaRejectionReasonRequiredError(idea_id)
        idea.rejection_reason = rejection_reason.strip()

    idea.status = status
    db.commit()
    db.refresh(idea)
    return idea
