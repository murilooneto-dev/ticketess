import pytest

from app.models.project_idea import ProjectIdea, ProjectIdeaStatus
from app.models.user import UserRole
from app.schemas.project_idea import ProjectIdeaCreate
from app.schemas.user import UserCreate
from app.services.notification_service import list_notifications
from app.services.project_idea_service import (
    ProjectIdeaMissingProjectError,
    ProjectIdeaNotFoundError,
    ProjectIdeaRejectionReasonRequiredError,
    create_project_idea,
    list_project_ideas,
    update_project_idea_status,
)
from app.services.user_service import create_user


def _create_user(db_session, username, role):
    return create_user(
        db_session, UserCreate(name=username.capitalize(), username=username, password="senha1234", role=role)
    )


def _create_project(db_session, name="Projeto Teste"):
    from app.models.project import Project

    project = Project(name=name)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


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
    project = _create_project(db_session)

    idea = create_project_idea(
        db_session, author.id, ProjectIdeaCreate(title="Portal do cliente", description="Ideia legal", project_id=project.id)
    )

    assert idea.status == ProjectIdeaStatus.PENDENTE
    notifications = list_notifications(db_session, admin.id)
    assert len(notifications) == 1
    assert "Portal do cliente" in notifications[0].title


def test_list_project_ideas_scoped_by_role(db_session):
    admin = _create_user(db_session, "admin_svc2", UserRole.ADMIN)
    gestor = _create_user(db_session, "gestor_svc2", UserRole.GESTOR)
    operador = _create_user(db_session, "operador_svc2", UserRole.OPERADOR)
    project = _create_project(db_session)

    create_project_idea(db_session, gestor.id, ProjectIdeaCreate(title="Ideia A", description="desc", project_id=project.id))
    create_project_idea(db_session, operador.id, ProjectIdeaCreate(title="Ideia B", description="desc", project_id=project.id))

    admin_view = list_project_ideas(db_session, admin)
    gestor_view = list_project_ideas(db_session, gestor)

    assert len(admin_view) == 2
    assert len(gestor_view) == 1
    assert gestor_view[0].title == "Ideia A"


def test_update_project_idea_status_notifies_author(db_session):
    admin = _create_user(db_session, "admin_svc3", UserRole.ADMIN)
    author = _create_user(db_session, "gestor_svc3", UserRole.GESTOR)
    project = _create_project(db_session)
    idea = create_project_idea(db_session, author.id, ProjectIdeaCreate(title="Ideia C", description="desc", project_id=project.id))

    updated = update_project_idea_status(db_session, idea.id, ProjectIdeaStatus.APROVADA, admin.id)

    assert updated.status == ProjectIdeaStatus.APROVADA
    notifications = list_notifications(db_session, author.id)
    assert any("aprovada" in n.title for n in notifications)


def test_update_nonexistent_idea_raises(db_session):
    admin = _create_user(db_session, "admin_svc4", UserRole.ADMIN)
    with pytest.raises(ProjectIdeaNotFoundError):
        update_project_idea_status(db_session, 9999, ProjectIdeaStatus.REJEITADA, admin.id)


def test_repeated_status_update_does_not_duplicate_notification(db_session):
    admin = _create_user(db_session, "admin_svc5", UserRole.ADMIN)
    author = _create_user(db_session, "gestor_svc5", UserRole.GESTOR)
    project = _create_project(db_session)
    idea = create_project_idea(db_session, author.id, ProjectIdeaCreate(title="Ideia D", description="desc", project_id=project.id))

    update_project_idea_status(db_session, idea.id, ProjectIdeaStatus.APROVADA, admin.id)
    update_project_idea_status(db_session, idea.id, ProjectIdeaStatus.APROVADA, admin.id)

    notifications = [n for n in list_notifications(db_session, author.id) if "aprovada" in n.title]
    assert len(notifications) == 1


def test_admin_approving_own_idea_does_not_self_notify(db_session):
    admin = _create_user(db_session, "admin_svc6", UserRole.ADMIN)
    project = _create_project(db_session)
    idea = create_project_idea(db_session, admin.id, ProjectIdeaCreate(title="Ideia E", description="desc", project_id=project.id))

    update_project_idea_status(db_session, idea.id, ProjectIdeaStatus.APROVADA, admin.id)

    notifications = [n for n in list_notifications(db_session, admin.id) if "aprovada" in n.title]
    assert notifications == []


def _create_and_login(client, db_session, username, password, role):
    user = create_user(db_session, UserCreate(name=username, username=username, password=password, role=role))
    client.post("/api/auth/login", json={"username": username, "password": password})
    return user


def test_operador_can_submit_idea_via_api(client, db_session):
    _create_and_login(client, db_session, "operador_api", "senha1234", UserRole.OPERADOR)
    project = _create_project(db_session)

    response = client.post(
        "/api/project-ideas",
        json={"title": "App interno", "description": "Facilita o dia a dia", "project_id": project.id},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "App interno"
    assert body["status"] == "pendente"
    assert body["author"]["username"] == "operador_api"


def test_non_admin_sees_only_own_ideas_via_api(client, db_session):
    project = _create_project(db_session)
    _create_and_login(client, db_session, "gestor_api", "senha1234", UserRole.GESTOR)
    client.post(
        "/api/project-ideas", json={"title": "Ideia do gestor", "description": "desc", "project_id": project.id}
    )

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "operador_api2", "senha1234", UserRole.OPERADOR)
    client.post(
        "/api/project-ideas", json={"title": "Ideia do operador", "description": "desc", "project_id": project.id}
    )

    response = client.get("/api/project-ideas")

    assert response.status_code == 200
    titles = [idea["title"] for idea in response.json()]
    assert titles == ["Ideia do operador"]


def test_admin_sees_all_ideas_via_api(client, db_session):
    project = _create_project(db_session)
    _create_and_login(client, db_session, "admin_api", "senha1234", UserRole.ADMIN)
    client.post("/api/project-ideas", json={"title": "Ideia 1", "description": "desc", "project_id": project.id})

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "gestor_api2", "senha1234", UserRole.GESTOR)
    client.post("/api/project-ideas", json={"title": "Ideia 2", "description": "desc", "project_id": project.id})

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "admin_api", "password": "senha1234"})
    response = client.get("/api/project-ideas")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_non_admin_cannot_change_idea_status(client, db_session):
    project = _create_project(db_session)
    _create_and_login(client, db_session, "gestor_api3", "senha1234", UserRole.GESTOR)
    idea_id = client.post(
        "/api/project-ideas", json={"title": "Ideia 3", "description": "desc", "project_id": project.id}
    ).json()["id"]

    response = client.patch(f"/api/project-ideas/{idea_id}", json={"status": "aprovada"})

    assert response.status_code == 403


def test_admin_approves_idea_and_author_is_notified(client, db_session):
    project = _create_project(db_session)
    _create_and_login(client, db_session, "admin_api2", "senha1234", UserRole.ADMIN)

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "operador_api3", "senha1234", UserRole.OPERADOR)
    idea_id = client.post(
        "/api/project-ideas", json={"title": "Ideia 4", "description": "desc", "project_id": project.id}
    ).json()["id"]

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


def test_project_idea_model_persists_project_and_rejection_reason(db_session):
    from app.models.project import Project

    user = _create_user(db_session, "gestor_proj_field", UserRole.GESTOR)
    project = Project(name="Projeto X")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    idea = ProjectIdea(
        title="Ideia com projeto",
        description="desc",
        created_by=user.id,
        project_id=project.id,
        rejection_reason="Fora do escopo atual",
    )
    db_session.add(idea)
    db_session.commit()
    db_session.refresh(idea)

    assert idea.project_id == project.id
    assert idea.project.name == "Projeto X"
    assert idea.rejection_reason == "Fora do escopo atual"


def test_create_idea_with_invalid_project_fails(client, db_session):
    _create_and_login(client, db_session, "gestor_badproj", "senha1234", UserRole.GESTOR)

    response = client.post("/api/project-ideas", json={"title": "Ideia", "description": "desc", "project_id": 9999})

    assert response.status_code == 400


def test_approving_idea_creates_ticket_and_notifies_author(db_session):
    admin = _create_user(db_session, "admin_approve1", UserRole.ADMIN)
    author = _create_user(db_session, "gestor_approve1", UserRole.GESTOR)
    project = _create_project(db_session)
    idea = create_project_idea(
        db_session, author.id, ProjectIdeaCreate(title="Ideia F", description="Descrição F", project_id=project.id)
    )

    updated = update_project_idea_status(db_session, idea.id, ProjectIdeaStatus.APROVADA, admin.id)

    from app.models.ticket import Ticket

    tickets = db_session.query(Ticket).filter(Ticket.project_id == project.id).all()
    assert len(tickets) == 1
    assert tickets[0].title == "Ideia F"
    assert tickets[0].description == "Descrição F"
    assert tickets[0].created_by == author.id

    notifications = list_notifications(db_session, author.id)
    approved_notifications = [n for n in notifications if "Ideia aprovada" in n.title]
    assert len(approved_notifications) == 1
    assert approved_notifications[0].link == f"/tickets/{tickets[0].id}"


def test_approving_idea_without_project_requires_project_id(db_session):
    from app.models.project_idea import ProjectIdea

    admin = _create_user(db_session, "admin_approve2", UserRole.ADMIN)
    author = _create_user(db_session, "gestor_approve2", UserRole.GESTOR)
    idea = ProjectIdea(title="Ideia legada", description="desc", created_by=author.id)
    db_session.add(idea)
    db_session.commit()
    db_session.refresh(idea)

    with pytest.raises(ProjectIdeaMissingProjectError):
        update_project_idea_status(db_session, idea.id, ProjectIdeaStatus.APROVADA, admin.id)


def test_approving_legacy_idea_with_supplied_project_id_succeeds(db_session):
    from app.models.project_idea import ProjectIdea

    admin = _create_user(db_session, "admin_approve3", UserRole.ADMIN)
    author = _create_user(db_session, "gestor_approve3", UserRole.GESTOR)
    project = _create_project(db_session)
    idea = ProjectIdea(title="Ideia legada 2", description="desc", created_by=author.id)
    db_session.add(idea)
    db_session.commit()
    db_session.refresh(idea)

    updated = update_project_idea_status(
        db_session, idea.id, ProjectIdeaStatus.APROVADA, admin.id, project_id=project.id
    )

    assert updated.project_id == project.id


def test_rejecting_idea_without_reason_raises(db_session):
    admin = _create_user(db_session, "admin_reject1", UserRole.ADMIN)
    author = _create_user(db_session, "gestor_reject1", UserRole.GESTOR)
    project = _create_project(db_session)
    idea = create_project_idea(
        db_session, author.id, ProjectIdeaCreate(title="Ideia G", description="desc", project_id=project.id)
    )

    with pytest.raises(ProjectIdeaRejectionReasonRequiredError):
        update_project_idea_status(db_session, idea.id, ProjectIdeaStatus.REJEITADA, admin.id)


def test_rejecting_idea_with_reason_notifies_author(db_session):
    admin = _create_user(db_session, "admin_reject2", UserRole.ADMIN)
    author = _create_user(db_session, "gestor_reject2", UserRole.GESTOR)
    project = _create_project(db_session)
    idea = create_project_idea(
        db_session, author.id, ProjectIdeaCreate(title="Ideia H", description="desc", project_id=project.id)
    )

    updated = update_project_idea_status(
        db_session, idea.id, ProjectIdeaStatus.REJEITADA, admin.id, rejection_reason="Fora do orçamento deste trimestre"
    )

    assert updated.rejection_reason == "Fora do orçamento deste trimestre"
    notifications = list_notifications(db_session, author.id)
    rejected = [n for n in notifications if "Ideia rejeitada" in n.title]
    assert len(rejected) == 1
    assert "Fora do orçamento deste trimestre" in rejected[0].message


def test_reject_endpoint_requires_reason(client, db_session):
    _create_and_login(client, db_session, "admin_reject3", "senha1234", UserRole.ADMIN)
    project = _create_project(db_session)
    idea_id = client.post(
        "/api/project-ideas", json={"title": "Ideia I", "description": "desc", "project_id": project.id}
    ).json()["id"]

    response = client.patch(f"/api/project-ideas/{idea_id}", json={"status": "rejeitada"})

    assert response.status_code == 400


def test_reject_endpoint_with_reason_succeeds(client, db_session):
    _create_and_login(client, db_session, "admin_reject4", "senha1234", UserRole.ADMIN)
    project = _create_project(db_session)
    idea_id = client.post(
        "/api/project-ideas", json={"title": "Ideia J", "description": "desc", "project_id": project.id}
    ).json()["id"]

    response = client.patch(
        f"/api/project-ideas/{idea_id}", json={"status": "rejeitada", "rejection_reason": "Duplicada"}
    )

    assert response.status_code == 200
    assert response.json()["rejection_reason"] == "Duplicada"


def test_approving_legacy_idea_with_nonexistent_project_returns_400(client, db_session):
    _create_and_login(client, db_session, "admin_badproj2", "senha1234", UserRole.ADMIN)
    author = _create_user(db_session, "gestor_badproj2", UserRole.GESTOR)
    idea = ProjectIdea(title="Ideia legada 3", description="desc", created_by=author.id)
    db_session.add(idea)
    db_session.commit()
    db_session.refresh(idea)

    response = client.patch(
        f"/api/project-ideas/{idea.id}", json={"status": "aprovada", "project_id": 9999}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Projeto informado não existe"


def test_approving_idea_sets_generated_ticket_id(client, db_session):
    _create_and_login(client, db_session, "admin_genticket", "senha1234", UserRole.ADMIN)
    author = _create_user(db_session, "gestor_genticket", UserRole.GESTOR)
    project = _create_project(db_session)
    idea = create_project_idea(
        db_session, author.id, ProjectIdeaCreate(title="Ideia K", description="desc", project_id=project.id)
    )

    updated = update_project_idea_status(db_session, idea.id, ProjectIdeaStatus.APROVADA, author.id)

    assert updated.generated_ticket_id is not None

    idea2 = create_project_idea(
        db_session, author.id, ProjectIdeaCreate(title="Ideia L", description="desc", project_id=project.id)
    )
    http_response = client.patch(f"/api/project-ideas/{idea2.id}", json={"status": "aprovada"})

    assert http_response.status_code == 200
    body = http_response.json()
    assert body["generated_ticket_id"] is not None
