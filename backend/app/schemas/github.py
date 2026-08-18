from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GithubCommitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sha: str
    message: str
    author_name: str | None
    url: str
    committed_at: datetime
    ticket_id: int | None


class GithubPullRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: int
    title: str
    state: str
    url: str
    author_login: str | None
    opened_at: datetime
    merged_at: datetime | None
    closed_at: datetime | None
    ticket_id: int | None


class GithubSyncResult(BaseModel):
    commits_synced: int
    pull_requests_synced: int
    synced_at: datetime


class TicketGithubActivityOut(BaseModel):
    commits: list[GithubCommitOut]
    pull_requests: list[GithubPullRequestOut]
