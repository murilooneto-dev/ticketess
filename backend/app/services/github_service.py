import re
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.config import settings
from app.models.github import GithubCommit, GithubPullRequest
from app.models.project import Project
from app.models.ticket import Ticket
from app.schemas.github import GithubSyncResult

GITHUB_API_BASE = "https://api.github.com"
TICKET_REFERENCE_PATTERN = re.compile(r"#(\d+)")


class GithubNotEnabledError(Exception):
    pass


class GithubRepoNotConfiguredError(Exception):
    pass


class GithubApiError(Exception):
    pass


def _headers(token: str | None = None) -> dict:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    effective_token = token or settings.GITHUB_TOKEN
    if effective_token:
        headers["Authorization"] = f"Bearer {effective_token}"
    return headers


def fetch_commits(owner: str, repo: str, token: str | None = None) -> list[dict]:
    try:
        response = httpx.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits",
            headers=_headers(token),
            params={"per_page": 50},
            timeout=15,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise GithubApiError(str(exc)) from exc
    return response.json()


def fetch_pull_requests(owner: str, repo: str, token: str | None = None) -> list[dict]:
    try:
        response = httpx.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls",
            headers=_headers(token),
            params={"state": "all", "per_page": 50},
            timeout=15,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise GithubApiError(str(exc)) from exc
    return response.json()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _find_ticket_id(db: DbSession, project_id: int, text: str) -> int | None:
    for match in TICKET_REFERENCE_PATTERN.finditer(text or ""):
        candidate_id = int(match.group(1))
        ticket_id = db.execute(
            select(Ticket.id).where(Ticket.id == candidate_id, Ticket.project_id == project_id)
        ).scalar_one_or_none()
        if ticket_id is not None:
            return ticket_id
    return None


def sync_project(db: DbSession, project: Project) -> GithubSyncResult:
    if not settings.GITHUB_ENABLED:
        raise GithubNotEnabledError()
    if not project.github_repo:
        raise GithubRepoNotConfiguredError()

    owner, repo = project.github_repo.split("/", 1)

    commits_data = fetch_commits(owner, repo, project.github_token)
    prs_data = fetch_pull_requests(owner, repo, project.github_token)

    commits_synced = 0
    for item in commits_data:
        sha = item.get("sha")
        commit_info = item.get("commit", {}) or {}
        message = commit_info.get("message", "")
        author = commit_info.get("author", {}) or {}
        committed_at = _parse_datetime(author.get("date")) or datetime.now(timezone.utc)
        ticket_id = _find_ticket_id(db, project.id, message)

        existing = db.execute(
            select(GithubCommit).where(GithubCommit.project_id == project.id, GithubCommit.sha == sha)
        ).scalar_one_or_none()

        if existing is not None:
            existing.message = message
            existing.author_name = author.get("name")
            existing.committed_at = committed_at
            existing.ticket_id = ticket_id
        else:
            db.add(
                GithubCommit(
                    project_id=project.id,
                    sha=sha,
                    message=message,
                    author_name=author.get("name"),
                    url=item.get("html_url", ""),
                    committed_at=committed_at,
                    ticket_id=ticket_id,
                )
            )
        commits_synced += 1

    prs_synced = 0
    for item in prs_data:
        number = item.get("number")
        title = item.get("title", "")
        body = item.get("body") or ""
        merged_at = _parse_datetime(item.get("merged_at"))
        closed_at = _parse_datetime(item.get("closed_at"))
        opened_at = _parse_datetime(item.get("created_at")) or datetime.now(timezone.utc)
        state = "merged" if merged_at else item.get("state", "open")
        ticket_id = _find_ticket_id(db, project.id, f"{title}\n{body}")
        author_login = (item.get("user") or {}).get("login")

        existing = db.execute(
            select(GithubPullRequest).where(
                GithubPullRequest.project_id == project.id, GithubPullRequest.number == number
            )
        ).scalar_one_or_none()

        if existing is not None:
            existing.title = title
            existing.state = state
            existing.author_login = author_login
            existing.merged_at = merged_at
            existing.closed_at = closed_at
            existing.ticket_id = ticket_id
        else:
            db.add(
                GithubPullRequest(
                    project_id=project.id,
                    number=number,
                    title=title,
                    state=state,
                    url=item.get("html_url", ""),
                    author_login=author_login,
                    opened_at=opened_at,
                    merged_at=merged_at,
                    closed_at=closed_at,
                    ticket_id=ticket_id,
                )
            )
        prs_synced += 1

    synced_at = datetime.now(timezone.utc)
    project.github_synced_at = synced_at
    db.commit()

    return GithubSyncResult(commits_synced=commits_synced, pull_requests_synced=prs_synced, synced_at=synced_at)


def list_commits(db: DbSession, project_id: int) -> list[GithubCommit]:
    query = select(GithubCommit).where(GithubCommit.project_id == project_id).order_by(GithubCommit.committed_at.desc())
    return list(db.execute(query).scalars())


def list_pull_requests(db: DbSession, project_id: int) -> list[GithubPullRequest]:
    query = (
        select(GithubPullRequest)
        .where(GithubPullRequest.project_id == project_id)
        .order_by(GithubPullRequest.opened_at.desc())
    )
    return list(db.execute(query).scalars())


def list_ticket_commits(db: DbSession, ticket_id: int) -> list[GithubCommit]:
    query = select(GithubCommit).where(GithubCommit.ticket_id == ticket_id).order_by(GithubCommit.committed_at.desc())
    return list(db.execute(query).scalars())


def list_ticket_pull_requests(db: DbSession, ticket_id: int) -> list[GithubPullRequest]:
    query = (
        select(GithubPullRequest)
        .where(GithubPullRequest.ticket_id == ticket_id)
        .order_by(GithubPullRequest.opened_at.desc())
    )
    return list(db.execute(query).scalars())
