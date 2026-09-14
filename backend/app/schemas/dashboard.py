from pydantic import BaseModel

from app.schemas.github import GithubCommitOut, GithubPullRequestOut
from app.schemas.ticket import TicketListItemOut


class DashboardSummary(BaseModel):
    total_projects: int
    total_tickets: int
    open_tickets: int
    projects_by_status: dict[str, int]
    tickets_by_status: dict[str, int]
    tickets_by_priority: dict[str, int]
    recent_tickets: list[TicketListItemOut]
    recent_commits: list[GithubCommitOut]
    recent_pull_requests: list[GithubPullRequestOut]
