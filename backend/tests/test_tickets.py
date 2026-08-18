from app.config import Settings, settings
from app.models.user import UserRole
from app.schemas.project import ProjectCreate
from app.schemas.user import UserCreate
from app.services.project_service import create_project
from app.services.user_service import create_user


def _create_and_login(client, db_session, email, password, role):
    user = create_user(db_session, UserCreate(name="Test", username=email, password=password, role=role))
    client.post("/api/auth/login", json={"username": email, "password": password})
    return user


def _create_project(db_session, name="Projeto Teste"):
    return create_project(db_session, ProjectCreate(name=name))


def test_gestor_can_create_ticket(client, db_session):
    _create_and_login(client, db_session, "gestor", "senha1234", UserRole.GESTOR)
    project = _create_project(db_session)

    response = client.post(
        "/api/tickets",
        json={"project_id": project.id, "title": "Botão quebrado", "type": "bug", "priority": "alta"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Botão quebrado"
    assert body["status"] == "aberto"
    assert body["author"]["username"] == "gestor"


def test_create_ticket_with_invalid_project_fails(client, db_session):
    _create_and_login(client, db_session, "gestor2", "senha1234", UserRole.GESTOR)

    response = client.post("/api/tickets", json={"project_id": 999, "title": "Ticket X"})

    assert response.status_code == 400


def test_gestor_cannot_update_ticket(client, db_session):
    _create_and_login(client, db_session, "gestor3", "senha1234", UserRole.GESTOR)
    project = _create_project(db_session)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket Y"}).json()["id"]

    response = client.put(f"/api/tickets/{ticket_id}", json={"status": "em_andamento"})

    assert response.status_code == 403


def test_admin_can_update_ticket_status_and_history_is_recorded(client, db_session):
    _create_and_login(client, db_session, "admin", "senha1234", UserRole.ADMIN)
    project = _create_project(db_session)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket Z"}).json()["id"]

    update_response = client.put(f"/api/tickets/{ticket_id}", json={"status": "em_andamento", "priority": "alta"})
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "em_andamento"
    assert update_response.json()["priority"] == "alta"

    history_response = client.get(f"/api/tickets/{ticket_id}/history")
    assert history_response.status_code == 200
    fields_changed = {entry["field"] for entry in history_response.json()}
    assert fields_changed == {"status", "priority"}


def test_mine_filter_returns_only_own_tickets(client, db_session):
    _create_and_login(client, db_session, "admin2", "senha1234", UserRole.ADMIN)
    project = _create_project(db_session)
    client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket Admin"})

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "gestor4", "senha1234", UserRole.GESTOR)
    client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket Gestor"})

    response_all = client.get("/api/tickets")
    response_mine = client.get("/api/tickets?mine=true")

    assert len(response_all.json()) == 2
    assert len(response_mine.json()) == 1
    assert response_mine.json()[0]["title"] == "Ticket Gestor"


def test_project_filter_returns_only_matching_tickets(client, db_session):
    _create_and_login(client, db_session, "admin3", "senha1234", UserRole.ADMIN)
    project_a = _create_project(db_session, "Projeto A")
    project_b = _create_project(db_session, "Projeto B")
    client.post("/api/tickets", json={"project_id": project_a.id, "title": "Ticket A"})
    client.post("/api/tickets", json={"project_id": project_b.id, "title": "Ticket B"})

    response = client.get(f"/api/tickets?project_id={project_a.id}")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Ticket A"


def test_comment_flow(client, db_session):
    _create_and_login(client, db_session, "admin4", "senha1234", UserRole.ADMIN)
    project = _create_project(db_session)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket C"}).json()["id"]

    post_response = client.post(f"/api/tickets/{ticket_id}/comments", json={"message": "Analisando o problema"})
    assert post_response.status_code == 201

    get_response = client.get(f"/api/tickets/{ticket_id}/comments")
    assert get_response.status_code == 200
    assert len(get_response.json()) == 1
    assert get_response.json()[0]["message"] == "Analisando o problema"


def test_comment_on_nonexistent_ticket_returns_404(client, db_session):
    _create_and_login(client, db_session, "admin5", "senha1234", UserRole.ADMIN)

    response = client.post("/api/tickets/9999/comments", json={"message": "oi"})

    assert response.status_code == 404


def test_attachment_upload_and_download(client, db_session, monkeypatch, tmp_path):
    monkeypatch.setattr(Settings, "storage_dir", property(lambda self: tmp_path))

    _create_and_login(client, db_session, "admin6", "senha1234", UserRole.ADMIN)
    project = _create_project(db_session)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket D"}).json()["id"]

    upload_response = client.post(
        f"/api/tickets/{ticket_id}/attachments",
        files={"file": ("nota.txt", b"conteudo do arquivo", "text/plain")},
    )
    assert upload_response.status_code == 201
    attachment_id = upload_response.json()["id"]
    assert upload_response.json()["original_filename"] == "nota.txt"

    list_response = client.get(f"/api/tickets/{ticket_id}/attachments")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    download_response = client.get(f"/api/tickets/{ticket_id}/attachments/{attachment_id}/download")
    assert download_response.status_code == 200
    assert download_response.content == b"conteudo do arquivo"


def test_attachment_too_large_is_rejected(client, db_session, monkeypatch, tmp_path):
    monkeypatch.setattr(Settings, "storage_dir", property(lambda self: tmp_path))
    monkeypatch.setattr(settings, "UPLOAD_MAX_SIZE_MB", 0)

    _create_and_login(client, db_session, "admin7", "senha1234", UserRole.ADMIN)
    project = _create_project(db_session)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket E"}).json()["id"]

    response = client.post(
        f"/api/tickets/{ticket_id}/attachments",
        files={"file": ("grande.txt", b"x" * 1024, "text/plain")},
    )

    assert response.status_code == 413


def test_ticket_not_found_returns_404(client, db_session):
    _create_and_login(client, db_session, "admin8", "senha1234", UserRole.ADMIN)

    response = client.get("/api/tickets/9999")

    assert response.status_code == 404


def test_unauthenticated_cannot_create_ticket(client, db_session):
    response = client.post("/api/tickets", json={"project_id": 1, "title": "Sem login"})

    assert response.status_code == 401


def test_gestor_cannot_set_type_or_priority_on_creation(client, db_session):
    _create_and_login(client, db_session, "gestor9", "senha1234", UserRole.GESTOR)
    project = _create_project(db_session)

    response = client.post(
        "/api/tickets",
        json={"project_id": project.id, "title": "Tentando definir tipo", "type": "bug", "priority": "urgente"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "outro"
    assert body["priority"] == "media"


def test_operador_can_create_ticket(client, db_session):
    _create_and_login(client, db_session, "operador1", "senha1234", UserRole.OPERADOR)
    project = _create_project(db_session)

    response = client.post("/api/tickets", json={"project_id": project.id, "title": "Impressora não funciona"})

    assert response.status_code == 201


def test_operador_only_sees_own_tickets_in_list(client, db_session):
    _create_and_login(client, db_session, "admin9", "senha1234", UserRole.ADMIN)
    project = _create_project(db_session)
    client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket do admin"})

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "operador2", "senha1234", UserRole.OPERADOR)
    client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket do operador"})

    response = client.get("/api/tickets")

    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert titles == ["Ticket do operador"]


def test_operador_mine_query_param_ignored_still_scoped(client, db_session):
    _create_and_login(client, db_session, "admin10", "senha1234", UserRole.ADMIN)
    project = _create_project(db_session)
    client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket do admin 2"})

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "operador3", "senha1234", UserRole.OPERADOR)
    client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket do operador 2"})

    response = client.get("/api/tickets?mine=false")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Ticket do operador 2"


def test_gestor_sees_tickets_from_operadores_and_gestores(client, db_session):
    _create_and_login(client, db_session, "admin11", "senha1234", UserRole.ADMIN)
    project = _create_project(db_session)

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "operador4", "senha1234", UserRole.OPERADOR)
    client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket operador 4"})

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "gestor10", "senha1234", UserRole.GESTOR)
    client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket gestor 10"})

    response = client.get("/api/tickets")

    assert response.status_code == 200
    titles = {t["title"] for t in response.json()}
    assert titles == {"Ticket operador 4", "Ticket gestor 10"}


def test_operador_cannot_view_others_ticket_detail(client, db_session):
    _create_and_login(client, db_session, "admin12", "senha1234", UserRole.ADMIN)
    project = _create_project(db_session)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket sigiloso"}).json()["id"]

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "operador5", "senha1234", UserRole.OPERADOR)

    response = client.get(f"/api/tickets/{ticket_id}")

    assert response.status_code == 403


def test_operador_can_view_own_ticket_detail(client, db_session):
    _create_and_login(client, db_session, "operador6", "senha1234", UserRole.OPERADOR)
    project = _create_project(db_session)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Meu ticket"}).json()["id"]

    response = client.get(f"/api/tickets/{ticket_id}")

    assert response.status_code == 200


def test_operador_cannot_comment_on_others_ticket(client, db_session):
    _create_and_login(client, db_session, "admin13", "senha1234", UserRole.ADMIN)
    project = _create_project(db_session)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket alheio"}).json()["id"]

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "operador7", "senha1234", UserRole.OPERADOR)

    response = client.post(f"/api/tickets/{ticket_id}/comments", json={"message": "Posso comentar?"})

    assert response.status_code == 403


def test_operador_cannot_download_attachment_from_others_ticket(client, db_session, monkeypatch, tmp_path):
    from app.config import Settings

    monkeypatch.setattr(Settings, "storage_dir", property(lambda self: tmp_path))

    _create_and_login(client, db_session, "admin14", "senha1234", UserRole.ADMIN)
    project = _create_project(db_session)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket com anexo"}).json()["id"]
    attachment_id = client.post(
        f"/api/tickets/{ticket_id}/attachments",
        files={"file": ("nota.txt", b"conteudo", "text/plain")},
    ).json()["id"]

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "operador8", "senha1234", UserRole.OPERADOR)

    response = client.get(f"/api/tickets/{ticket_id}/attachments/{attachment_id}/download")

    assert response.status_code == 403
