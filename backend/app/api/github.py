import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.schemas.github import (
    GithubCommitOut,
    GithubPullRequestOut,
    GithubSyncResult,
    TicketGithubActivityOut,
)
from app.services.github_service import (
    GithubApiError,
    GithubNotEnabledError,
    GithubRepoNotConfiguredError,
    list_commits,
    list_pull_requests,
    list_ticket_commits,
    list_ticket_pull_requests,
    sync_project,
)
from app.services.project_service import get_project
from app.services.ticket_service import get_ticket

router = APIRouter(tags=["github"])
logger = logging.getLogger("app.github")


@router.post("/api/projects/{project_id}/github/sync", response_model=GithubSyncResult)
def post_github_sync(project_id: int, db: DbSession = Depends(get_db)):
    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado")

    try:
        result = sync_project(db, project)
        logger.info(
            "Sincronização manual do projeto '%s': %s commit(s), %s pull request(s)",
            project.name,
            result.commits_synced,
            result.pull_requests_synced,
        )
        return result
    except GithubNotEnabledError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Integração com o GitHub está desabilitada"
        )
    except GithubRepoNotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Projeto não possui repositório GitHub configurado"
        )
    except GithubApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Falha ao consultar a API do GitHub: {exc}"
        )


@router.get("/api/projects/{project_id}/github/commits", response_model=list[GithubCommitOut])
def get_project_commits(project_id: int, db: DbSession = Depends(get_db)):
    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado")
    return list_commits(db, project_id)


@router.get("/api/projects/{project_id}/github/pull-requests", response_model=list[GithubPullRequestOut])
def get_project_pull_requests(project_id: int, db: DbSession = Depends(get_db)):
    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado")
    return list_pull_requests(db, project_id)


@router.get("/api/tickets/{ticket_id}/github", response_model=TicketGithubActivityOut)
def get_ticket_github_activity(ticket_id: int, db: DbSession = Depends(get_db)):
    ticket = get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")

    return TicketGithubActivityOut(
        commits=list_ticket_commits(db, ticket_id),
        pull_requests=list_ticket_pull_requests(db, ticket_id),
    )
