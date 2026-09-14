from dataclasses import dataclass, field
from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.models.github import GithubCommit, GithubPullRequest
from app.models.project import Project
from app.models.ticket import Ticket, TicketHistory, TicketStatus


@dataclass
class ProjectPeriodData:
    project: Project
    tickets_opened: list[Ticket] = field(default_factory=list)
    tickets_resolved: list[Ticket] = field(default_factory=list)
    commits: list[GithubCommit] = field(default_factory=list)
    pull_requests: list[GithubPullRequest] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not (
            self.tickets_opened
            or self.tickets_resolved
            or self.commits
            or self.pull_requests
        )


def _bounds(start: date, end: date) -> tuple[datetime, datetime]:
    return datetime.combine(start, time.min), datetime.combine(end, time.max)


def collect_period_data(db: DbSession, start: date, end: date) -> list[ProjectPeriodData]:
    start_dt, end_dt = _bounds(start, end)
    projects = list(db.execute(select(Project).order_by(Project.name)).scalars())

    resolved_ticket_ids = set(
        db.execute(
            select(TicketHistory.ticket_id).where(
                TicketHistory.field == "status",
                TicketHistory.new_value.in_([TicketStatus.CONCLUIDO.value, TicketStatus.CANCELADO.value]),
                TicketHistory.created_at.between(start_dt, end_dt),
            )
        ).scalars()
    )

    result = []
    for project in projects:
        data = ProjectPeriodData(project=project)

        data.tickets_opened = list(
            db.execute(
                select(Ticket).where(Ticket.project_id == project.id, Ticket.created_at.between(start_dt, end_dt))
            ).scalars()
        )

        if resolved_ticket_ids:
            data.tickets_resolved = list(
                db.execute(
                    select(Ticket).where(Ticket.project_id == project.id, Ticket.id.in_(resolved_ticket_ids))
                ).scalars()
            )

        data.commits = list(
            db.execute(
                select(GithubCommit).where(
                    GithubCommit.project_id == project.id, GithubCommit.committed_at.between(start_dt, end_dt)
                )
            ).scalars()
        )

        data.pull_requests = list(
            db.execute(
                select(GithubPullRequest).where(
                    GithubPullRequest.project_id == project.id,
                    GithubPullRequest.opened_at.between(start_dt, end_dt),
                )
            ).scalars()
        )

        if not data.is_empty():
            result.append(data)

    return result
