from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession, joinedload

from app.models.github import GithubCommit, GithubPullRequest
from app.models.project import Project, ProjectStatus
from app.models.ticket import Ticket, TicketPriority, TicketStatus
from app.schemas.dashboard import DashboardSummary

RECENT_LIMIT = 5


def _count_by(db: DbSession, column, enum_cls) -> dict[str, int]:
    counts = {member.value: 0 for member in enum_cls}
    query = select(column, func.count()).group_by(column)
    for value, count in db.execute(query):
        key = value.value if hasattr(value, "value") else value
        counts[key] = count
    return counts


def build_summary(db: DbSession, current_user_id: int) -> DashboardSummary:
    total_projects = db.execute(select(func.count()).select_from(Project)).scalar_one()
    total_tickets = db.execute(select(func.count()).select_from(Ticket)).scalar_one()

    my_open_tickets = db.execute(
        select(func.count())
        .select_from(Ticket)
        .where(
            Ticket.created_by == current_user_id,
            Ticket.status.notin_([TicketStatus.CONCLUIDO, TicketStatus.CANCELADO]),
        )
    ).scalar_one()

    my_managed_projects = db.execute(
        select(func.count()).select_from(Project).where(Project.manager_id == current_user_id)
    ).scalar_one()

    projects_by_status = _count_by(db, Project.status, ProjectStatus)
    tickets_by_status = _count_by(db, Ticket.status, TicketStatus)
    tickets_by_priority = _count_by(db, Ticket.priority, TicketPriority)

    recent_tickets = list(
        db.execute(
            select(Ticket).options(joinedload(Ticket.author)).order_by(Ticket.created_at.desc()).limit(RECENT_LIMIT)
        )
        .unique()
        .scalars()
    )

    recent_commits = list(
        db.execute(select(GithubCommit).order_by(GithubCommit.committed_at.desc()).limit(RECENT_LIMIT)).scalars()
    )

    recent_pull_requests = list(
        db.execute(
            select(GithubPullRequest).order_by(GithubPullRequest.opened_at.desc()).limit(RECENT_LIMIT)
        ).scalars()
    )

    return DashboardSummary(
        total_projects=total_projects,
        total_tickets=total_tickets,
        my_open_tickets=my_open_tickets,
        my_managed_projects=my_managed_projects,
        projects_by_status=projects_by_status,
        tickets_by_status=tickets_by_status,
        tickets_by_priority=tickets_by_priority,
        recent_tickets=recent_tickets,
        recent_commits=recent_commits,
        recent_pull_requests=recent_pull_requests,
    )
