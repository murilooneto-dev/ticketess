from app.models.user import UserRole
from app.schemas.project import ProjectCreate
from app.schemas.user import UserCreate
from app.services.project_service import create_project
from app.services.user_service import create_user


def _create_and_login(client, db_session, email, password, role):
    user = create_user(db_session, UserCreate(name=email.split("@")[0], username=email, password=password, role=role))
    client.post("/api/auth/login", json={"username": email, "password": password})
    return user


def test_dashboard_requires_authentication(client, db_session):
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 401


def test_dashboard_empty_state(client, db_session):
    _create_and_login(client, db_session, "admin", "senha1234", UserRole.ADMIN)

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["total_projects"] == 0
    assert body["total_tickets"] == 0
    assert body["my_open_tickets"] == 0
    assert body["projects_by_status"] == {"ativo": 0, "pausado": 0, "concluido": 0, "cancelado": 0}
    assert set(body["tickets_by_status"].keys()) == {"aberto", "em_andamento", "aguardando", "concluido", "cancelado"}
    assert set(body["tickets_by_priority"].keys()) == {"baixa", "media", "alta", "urgente"}
    assert body["recent_tickets"] == []
    assert body["recent_commits"] == []
    assert body["recent_pull_requests"] == []


def test_dashboard_counts_reflect_data(client, db_session):
    admin = _create_and_login(client, db_session, "admin2", "senha1234", UserRole.ADMIN)
    project = create_project(db_session, ProjectCreate(name="Projeto A", status="ativo"))
    create_project(db_session, ProjectCreate(name="Projeto B", status="pausado"))

    ticket1 = client.post(
        "/api/tickets", json={"project_id": project.id, "title": "Ticket 1", "priority": "alta"}
    ).json()
    client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket 2", "priority": "urgente"})
    client.put(f"/api/tickets/{ticket1['id']}", json={"status": "concluido"})

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["total_projects"] == 2
    assert body["total_tickets"] == 2
    assert body["projects_by_status"]["ativo"] == 1
    assert body["projects_by_status"]["pausado"] == 1
    assert body["tickets_by_status"]["concluido"] == 1
    assert body["tickets_by_status"]["aberto"] == 1
    assert body["tickets_by_priority"]["alta"] == 1
    assert body["tickets_by_priority"]["urgente"] == 1
    assert len(body["recent_tickets"]) == 2
    # my_open_tickets excludes concluido/cancelado
    assert body["my_open_tickets"] == 1


def test_dashboard_my_managed_projects(client, db_session):
    admin = _create_and_login(client, db_session, "admin3", "senha1234", UserRole.ADMIN)
    gestor = create_user(
        db_session, UserCreate(name="Gestor", username="gestor", password="senha1234", role=UserRole.GESTOR)
    )
    create_project(db_session, ProjectCreate(name="Projeto C", manager_id=gestor.id))

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "gestor", "password": "senha1234"})

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    assert response.json()["my_managed_projects"] == 1
