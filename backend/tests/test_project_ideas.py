import pytest

from app.models.project_idea import ProjectIdea, ProjectIdeaStatus
from app.models.user import UserRole
from app.schemas.project_idea import ProjectIdeaCreate
from app.schemas.user import UserCreate
from app.services.notification_service import list_notifications
from app.services.project_idea_service import (
    ProjectIdeaNotFoundError,
    create_project_idea,
    list_project_ideas,
    update_project_idea_status,
)
from app.services.user_service import create_user


def _create_user(db_session, username, role):
    return create_user(
        db_session, UserCreate(name=username.capitalize(), username=username, password="senha1234", role=role)
    )


def test_project_idea_model_persists_with_default_status(db_session):
    user = _create_user(db_session, "gestor_model", UserRole.GESTOR)

    idea = ProjectIdea(title="App de estoque", description="Controlar estoque pelo celular", created_by=user.id)
    db_session.add(idea)
    db_session.commit()
    db_session.refresh(idea)

    assert idea.id is not None
    assert idea.status == ProjectIdeaStatus.PENDENTE
    assert idea.author.username == "gestor_model"


def test_create_project_idea_notifies_admins(db_session):
    admin = _create_user(db_session, "admin_svc", UserRole.ADMIN)
    author = _create_user(db_session, "operador_svc", UserRole.OPERADOR)

    idea = create_project_idea(
        db_session, author.id, ProjectIdeaCreate(title="Portal do cliente", description="Ideia legal")
    )

    assert idea.status == ProjectIdeaStatus.PENDENTE
    notifications = list_notifications(db_session, admin.id)
    assert len(notifications) == 1
    assert "Portal do cliente" in notifications[0].title


def test_list_project_ideas_scoped_by_role(db_session):
    admin = _create_user(db_session, "admin_svc2", UserRole.ADMIN)
    gestor = _create_user(db_session, "gestor_svc2", UserRole.GESTOR)
    operador = _create_user(db_session, "operador_svc2", UserRole.OPERADOR)

    create_project_idea(db_session, gestor.id, ProjectIdeaCreate(title="Ideia A", description="desc"))
    create_project_idea(db_session, operador.id, ProjectIdeaCreate(title="Ideia B", description="desc"))

    admin_view = list_project_ideas(db_session, admin)
    gestor_view = list_project_ideas(db_session, gestor)

    assert len(admin_view) == 2
    assert len(gestor_view) == 1
    assert gestor_view[0].title == "Ideia A"


def test_update_project_idea_status_notifies_author(db_session):
    _create_user(db_session, "admin_svc3", UserRole.ADMIN)
    author = _create_user(db_session, "gestor_svc3", UserRole.GESTOR)
    idea = create_project_idea(db_session, author.id, ProjectIdeaCreate(title="Ideia C", description="desc"))

    updated = update_project_idea_status(db_session, idea.id, ProjectIdeaStatus.APROVADA)

    assert updated.status == ProjectIdeaStatus.APROVADA
    notifications = list_notifications(db_session, author.id)
    assert any("aprovada" in n.title for n in notifications)


def test_update_nonexistent_idea_raises(db_session):
    with pytest.raises(ProjectIdeaNotFoundError):
        update_project_idea_status(db_session, 9999, ProjectIdeaStatus.REJEITADA)


def _create_and_login(client, db_session, username, password, role):
    user = create_user(db_session, UserCreate(name=username, username=username, password=password, role=role))
    client.post("/api/auth/login", json={"username": username, "password": password})
    return user


def test_operador_can_submit_idea_via_api(client, db_session):
    _create_and_login(client, db_session, "operador_api", "senha1234", UserRole.OPERADOR)

    response = client.post("/api/project-ideas", json={"title": "App interno", "description": "Facilita o dia a dia"})

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "App interno"
    assert body["status"] == "pendente"
    assert body["author"]["username"] == "operador_api"


def test_non_admin_sees_only_own_ideas_via_api(client, db_session):
    _create_and_login(client, db_session, "gestor_api", "senha1234", UserRole.GESTOR)
    client.post("/api/project-ideas", json={"title": "Ideia do gestor", "description": "desc"})

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "operador_api2", "senha1234", UserRole.OPERADOR)
    client.post("/api/project-ideas", json={"title": "Ideia do operador", "description": "desc"})

    response = client.get("/api/project-ideas")

    assert response.status_code == 200
    titles = [idea["title"] for idea in response.json()]
    assert titles == ["Ideia do operador"]


def test_admin_sees_all_ideas_via_api(client, db_session):
    _create_and_login(client, db_session, "admin_api", "senha1234", UserRole.ADMIN)
    client.post("/api/project-ideas", json={"title": "Ideia 1", "description": "desc"})

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "gestor_api2", "senha1234", UserRole.GESTOR)
    client.post("/api/project-ideas", json={"title": "Ideia 2", "description": "desc"})

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "admin_api", "password": "senha1234"})
    response = client.get("/api/project-ideas")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_non_admin_cannot_change_idea_status(client, db_session):
    _create_and_login(client, db_session, "gestor_api3", "senha1234", UserRole.GESTOR)
    idea_id = client.post("/api/project-ideas", json={"title": "Ideia 3", "description": "desc"}).json()["id"]

    response = client.patch(f"/api/project-ideas/{idea_id}", json={"status": "aprovada"})

    assert response.status_code == 403


def test_admin_approves_idea_and_author_is_notified(client, db_session):
    _create_and_login(client, db_session, "admin_api2", "senha1234", UserRole.ADMIN)

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "operador_api3", "senha1234", UserRole.OPERADOR)
    idea_id = client.post("/api/project-ideas", json={"title": "Ideia 4", "description": "desc"}).json()["id"]

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "admin_api2", "password": "senha1234"})
    response = client.patch(f"/api/project-ideas/{idea_id}", json={"status": "aprovada"})
    assert response.status_code == 200
    assert response.json()["status"] == "aprovada"

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "operador_api3", "password": "senha1234"})
    titles = [n["title"] for n in client.get("/api/notifications").json()]
    assert any("aprovada" in t for t in titles)


def test_change_status_of_unknown_idea_returns_404(client, db_session):
    _create_and_login(client, db_session, "admin_api3", "senha1234", UserRole.ADMIN)

    response = client.patch("/api/project-ideas/9999", json={"status": "rejeitada"})

    assert response.status_code == 404
