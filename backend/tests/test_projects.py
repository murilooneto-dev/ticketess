from app.models.user import UserRole
from app.schemas.user import UserCreate
from app.services.user_service import create_user


def _create_and_login(client, db_session, email, password, role):
    user = create_user(db_session, UserCreate(name="Test", username=email, password=password, role=role))
    client.post("/api/auth/login", json={"username": email, "password": password})
    return user


def test_gestor_can_list_projects(client, db_session):
    _create_and_login(client, db_session, "gestor", "senha1234", UserRole.GESTOR)

    response = client.get("/api/projects")

    assert response.status_code == 200
    assert response.json() == []


def test_gestor_cannot_create_project(client, db_session):
    _create_and_login(client, db_session, "gestor2", "senha1234", UserRole.GESTOR)

    response = client.post("/api/projects", json={"name": "Novo Projeto"})

    assert response.status_code == 403


def test_admin_can_create_project_with_manager(client, db_session):
    admin = _create_and_login(client, db_session, "admin", "senha1234", UserRole.ADMIN)
    gestor = create_user(
        db_session, UserCreate(name="Gestor Um", username="gestor3", password="senha1234", role=UserRole.GESTOR)
    )

    response = client.post(
        "/api/projects",
        json={"name": "Sistema Financeiro", "description": "Controle de contas", "manager_id": gestor.id},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Sistema Financeiro"
    assert body["manager"]["id"] == gestor.id
    assert body["status"] == "ativo"


def test_admin_cannot_create_project_with_invalid_manager(client, db_session):
    _create_and_login(client, db_session, "admin2", "senha1234", UserRole.ADMIN)

    response = client.post("/api/projects", json={"name": "Projeto X", "manager_id": 999})

    assert response.status_code == 400


def test_mine_filter_returns_only_own_projects(client, db_session):
    admin = _create_and_login(client, db_session, "admin3", "senha1234", UserRole.ADMIN)
    gestor_a = create_user(
        db_session, UserCreate(name="Gestor A", username="gestora", password="senha1234", role=UserRole.GESTOR)
    )
    gestor_b = create_user(
        db_session, UserCreate(name="Gestor B", username="gestorb", password="senha1234", role=UserRole.GESTOR)
    )

    client.post("/api/projects", json={"name": "Projeto A", "manager_id": gestor_a.id})
    client.post("/api/projects", json={"name": "Projeto B", "manager_id": gestor_b.id})

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "gestora", "password": "senha1234"})

    response_all = client.get("/api/projects")
    response_mine = client.get("/api/projects?mine=true")

    assert len(response_all.json()) == 2
    assert len(response_mine.json()) == 1
    assert response_mine.json()[0]["name"] == "Projeto A"


def test_admin_can_update_project_status(client, db_session):
    _create_and_login(client, db_session, "admin4", "senha1234", UserRole.ADMIN)
    create_response = client.post("/api/projects", json={"name": "Projeto Y"})
    project_id = create_response.json()["id"]

    response = client.put(f"/api/projects/{project_id}", json={"status": "concluido"})

    assert response.status_code == 200
    assert response.json()["status"] == "concluido"


def test_update_nonexistent_project_returns_404(client, db_session):
    _create_and_login(client, db_session, "admin5", "senha1234", UserRole.ADMIN)

    response = client.put("/api/projects/9999", json={"status": "concluido"})

    assert response.status_code == 404


def test_admin_can_add_progress_update(client, db_session):
    _create_and_login(client, db_session, "admin6", "senha1234", UserRole.ADMIN)
    project_id = client.post("/api/projects", json={"name": "Projeto Z"}).json()["id"]

    response = client.post(f"/api/projects/{project_id}/updates", json={"message": "Início do desenvolvimento"})

    assert response.status_code == 201
    assert response.json()["message"] == "Início do desenvolvimento"


def test_gestor_cannot_add_progress_update(client, db_session):
    admin = _create_and_login(client, db_session, "admin7", "senha1234", UserRole.ADMIN)
    project_id = client.post("/api/projects", json={"name": "Projeto W"}).json()["id"]

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "gestor4", "senha1234", UserRole.GESTOR)

    response = client.post(f"/api/projects/{project_id}/updates", json={"message": "Tentando atualizar"})

    assert response.status_code == 403


def test_gestor_can_view_progress_updates(client, db_session):
    _create_and_login(client, db_session, "admin8", "senha1234", UserRole.ADMIN)
    project_id = client.post("/api/projects", json={"name": "Projeto V"}).json()["id"]
    client.post(f"/api/projects/{project_id}/updates", json={"message": "Etapa concluída"})

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "gestor5", "senha1234", UserRole.GESTOR)

    response = client.get(f"/api/projects/{project_id}/updates")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["message"] == "Etapa concluída"


def test_updates_for_nonexistent_project_returns_404(client, db_session):
    _create_and_login(client, db_session, "admin9", "senha1234", UserRole.ADMIN)

    response = client.get("/api/projects/9999/updates")

    assert response.status_code == 404
