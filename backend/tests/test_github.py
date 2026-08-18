import httpx
import pytest

from app.config import settings
from app.models.user import UserRole
from app.schemas.project import ProjectCreate
from app.schemas.user import UserCreate
from app.services import github_service
from app.services.project_service import create_project
from app.services.user_service import create_user


def _create_and_login(client, db_session, email, password, role):
    user = create_user(db_session, UserCreate(name=email.split("@")[0], username=email, password=password, role=role))
    client.post("/api/auth/login", json={"username": email, "password": password})
    return user


def _sample_commits(message="Fix login bug (#1)"):
    return [
        {
            "sha": "abc123",
            "commit": {"message": message, "author": {"name": "Dev One", "date": "2026-01-10T12:00:00Z"}},
            "html_url": "https://github.com/org/repo/commit/abc123",
        }
    ]


def _sample_pull_requests(title="Fix login (#1)"):
    return [
        {
            "number": 5,
            "title": title,
            "body": "",
            "state": "closed",
            "merged_at": "2026-01-11T09:00:00Z",
            "closed_at": "2026-01-11T09:00:00Z",
            "created_at": "2026-01-10T08:00:00Z",
            "html_url": "https://github.com/org/repo/pull/5",
            "user": {"login": "devone"},
        }
    ]


@pytest.fixture(autouse=True)
def _enable_github(monkeypatch):
    monkeypatch.setattr(settings, "GITHUB_ENABLED", True)


def test_sync_fails_when_github_disabled(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "GITHUB_ENABLED", False)
    _create_and_login(client, db_session, "admin", "senha1234", UserRole.ADMIN)
    project = create_project(db_session, ProjectCreate(name="Projeto", github_repo="org/repo"))

    response = client.post(f"/api/projects/{project.id}/github/sync")

    assert response.status_code == 400


def test_sync_fails_when_repo_not_configured(client, db_session):
    _create_and_login(client, db_session, "admin2", "senha1234", UserRole.ADMIN)
    project = create_project(db_session, ProjectCreate(name="Projeto sem repo"))

    response = client.post(f"/api/projects/{project.id}/github/sync")

    assert response.status_code == 400


def test_gestor_cannot_trigger_sync(client, db_session):
    _create_and_login(client, db_session, "gestor", "senha1234", UserRole.GESTOR)
    project = create_project(db_session, ProjectCreate(name="Projeto", github_repo="org/repo"))

    response = client.post(f"/api/projects/{project.id}/github/sync")

    assert response.status_code == 403


def test_sync_imports_commits_and_prs_and_links_ticket(client, db_session, monkeypatch):
    admin = _create_and_login(client, db_session, "admin3", "senha1234", UserRole.ADMIN)
    project = create_project(db_session, ProjectCreate(name="Projeto", github_repo="org/repo"))
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Bug de login"}).json()["id"]

    monkeypatch.setattr(github_service, "fetch_commits", lambda owner, repo, token=None: _sample_commits(f"Fix login bug (#{ticket_id})"))
    monkeypatch.setattr(
        github_service, "fetch_pull_requests", lambda owner, repo, token=None: _sample_pull_requests(f"Fix login (#{ticket_id})")
    )

    response = client.post(f"/api/projects/{project.id}/github/sync")

    assert response.status_code == 200
    body = response.json()
    assert body["commits_synced"] == 1
    assert body["pull_requests_synced"] == 1

    commits_response = client.get(f"/api/projects/{project.id}/github/commits")
    assert commits_response.status_code == 200
    assert len(commits_response.json()) == 1
    assert commits_response.json()[0]["ticket_id"] == ticket_id

    prs_response = client.get(f"/api/projects/{project.id}/github/pull-requests")
    assert prs_response.status_code == 200
    assert len(prs_response.json()) == 1
    assert prs_response.json()[0]["ticket_id"] == ticket_id
    assert prs_response.json()[0]["state"] == "merged"

    ticket_activity = client.get(f"/api/tickets/{ticket_id}/github")
    assert ticket_activity.status_code == 200
    assert len(ticket_activity.json()["commits"]) == 1
    assert len(ticket_activity.json()["pull_requests"]) == 1


def test_gestor_can_view_synced_commits(client, db_session, monkeypatch):
    _create_and_login(client, db_session, "admin4", "senha1234", UserRole.ADMIN)
    project = create_project(db_session, ProjectCreate(name="Projeto", github_repo="org/repo"))

    monkeypatch.setattr(github_service, "fetch_commits", lambda owner, repo, token=None: _sample_commits())
    monkeypatch.setattr(github_service, "fetch_pull_requests", lambda owner, repo, token=None: [])
    client.post(f"/api/projects/{project.id}/github/sync")

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "gestor2", "senha1234", UserRole.GESTOR)

    response = client.get(f"/api/projects/{project.id}/github/commits")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_resync_does_not_duplicate_records(client, db_session, monkeypatch):
    _create_and_login(client, db_session, "admin5", "senha1234", UserRole.ADMIN)
    project = create_project(db_session, ProjectCreate(name="Projeto", github_repo="org/repo"))

    monkeypatch.setattr(github_service, "fetch_commits", lambda owner, repo, token=None: _sample_commits())
    monkeypatch.setattr(github_service, "fetch_pull_requests", lambda owner, repo, token=None: _sample_pull_requests())

    client.post(f"/api/projects/{project.id}/github/sync")
    client.post(f"/api/projects/{project.id}/github/sync")

    commits = client.get(f"/api/projects/{project.id}/github/commits").json()
    prs = client.get(f"/api/projects/{project.id}/github/pull-requests").json()
    assert len(commits) == 1
    assert len(prs) == 1


def test_sync_handles_github_api_error(client, db_session, monkeypatch):
    _create_and_login(client, db_session, "admin6", "senha1234", UserRole.ADMIN)
    project = create_project(db_session, ProjectCreate(name="Projeto", github_repo="org/repo"))

    def _raise(owner, repo):
        raise httpx.HTTPError("boom")

    monkeypatch.setattr(github_service.httpx, "get", lambda *a, **kw: (_ for _ in ()).throw(httpx.HTTPError("boom")))

    response = client.post(f"/api/projects/{project.id}/github/sync")

    assert response.status_code == 502


def test_sync_nonexistent_project_returns_404(client, db_session):
    _create_and_login(client, db_session, "admin7", "senha1234", UserRole.ADMIN)

    response = client.post("/api/projects/9999/github/sync")

    assert response.status_code == 404


def test_invalid_github_repo_format_rejected(client, db_session):
    _create_and_login(client, db_session, "admin8", "senha1234", UserRole.ADMIN)

    response = client.post("/api/projects", json={"name": "Projeto", "github_repo": "not-a-valid-repo"})

    assert response.status_code == 422


def test_project_specific_token_overrides_global_token(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "GITHUB_TOKEN", "token-global")
    _create_and_login(client, db_session, "admin9", "senha1234", UserRole.ADMIN)
    project = create_project(
        db_session, ProjectCreate(name="Projeto", github_repo="org/repo", github_token="token-do-projeto")
    )

    captured = {}

    def fake_commits(owner, repo, token=None):
        captured["commits_token"] = token
        return []

    def fake_prs(owner, repo, token=None):
        captured["prs_token"] = token
        return []

    monkeypatch.setattr(github_service, "fetch_commits", fake_commits)
    monkeypatch.setattr(github_service, "fetch_pull_requests", fake_prs)

    client.post(f"/api/projects/{project.id}/github/sync")

    assert captured["commits_token"] == "token-do-projeto"
    assert captured["prs_token"] == "token-do-projeto"


def test_project_without_specific_token_falls_back_to_global(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "GITHUB_TOKEN", "token-global")
    _create_and_login(client, db_session, "admin10", "senha1234", UserRole.ADMIN)
    project = create_project(db_session, ProjectCreate(name="Projeto", github_repo="org/repo"))

    captured = {}
    monkeypatch.setattr(
        github_service,
        "fetch_commits",
        lambda owner, repo, token=None: captured.setdefault("token", token) or [],
    )
    monkeypatch.setattr(github_service, "fetch_pull_requests", lambda owner, repo, token=None: [])

    client.post(f"/api/projects/{project.id}/github/sync")

    assert captured["token"] is None


def test_github_token_never_returned_by_api(client, db_session):
    _create_and_login(client, db_session, "admin11", "senha1234", UserRole.ADMIN)
    project = create_project(
        db_session, ProjectCreate(name="Projeto", github_repo="org/repo", github_token="segredo-super-secreto")
    )

    response = client.get(f"/api/projects/{project.id}")

    assert response.status_code == 200
    body = response.json()
    assert "github_token" not in body
    assert body["has_github_token"] is True
    assert "segredo-super-secreto" not in response.text


def test_can_clear_project_specific_token(client, db_session):
    _create_and_login(client, db_session, "admin12", "senha1234", UserRole.ADMIN)
    project = create_project(
        db_session, ProjectCreate(name="Projeto", github_repo="org/repo", github_token="algum-token")
    )

    response = client.put(f"/api/projects/{project.id}", json={"clear_github_token": True})

    assert response.status_code == 200
    assert response.json()["has_github_token"] is False
