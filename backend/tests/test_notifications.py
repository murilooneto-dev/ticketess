from app.config import settings
from app.models.user import UserRole
from app.schemas.project import ProjectCreate
from app.schemas.user import UserCreate
from app.services.project_service import create_project
from app.services.user_service import create_user


def _create_and_login(client, db_session, email, password, role):
    user = create_user(db_session, UserCreate(name=email.split("@")[0], username=email, password=password, role=role))
    client.post("/api/auth/login", json={"username": email, "password": password})
    return user


def test_ticket_created_notifies_admins(client, db_session):
    admin = _create_and_login(client, db_session, "admin", "senha1234", UserRole.ADMIN)
    project = create_project(db_session, ProjectCreate(name="Projeto Teste"))

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "gestor", "senha1234", UserRole.GESTOR)
    client.post("/api/tickets", json={"project_id": project.id, "title": "Erro no login"})

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "admin", "password": "senha1234"})

    response = client.get("/api/notifications")
    assert response.status_code == 200
    notifications = response.json()
    assert len(notifications) == 1
    assert "Erro no login" in notifications[0]["title"]
    assert notifications[0]["is_read"] is False
    assert notifications[0]["link"] == "/tickets/1"


def test_ticket_creator_not_notified_of_own_ticket(client, db_session):
    admin = _create_and_login(client, db_session, "admin2", "senha1234", UserRole.ADMIN)
    project = create_project(db_session, ProjectCreate(name="Projeto Teste 2"))
    client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket do próprio admin"})

    response = client.get("/api/notifications")
    assert response.status_code == 200
    assert response.json() == []


def test_ticket_status_update_notifies_author(client, db_session):
    _create_and_login(client, db_session, "admin3", "senha1234", UserRole.ADMIN)
    project = create_project(db_session, ProjectCreate(name="Projeto 3"))

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "gestor2", "senha1234", UserRole.GESTOR)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Bug X"}).json()["id"]

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "admin3", "password": "senha1234"})
    client.put(f"/api/tickets/{ticket_id}", json={"status": "em_andamento"})

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "gestor2", "password": "senha1234"})

    response = client.get("/api/notifications")
    assert response.status_code == 200
    titles = [n["title"] for n in response.json()]
    assert any("Solicitação atualizada" in t for t in titles)


def test_unread_count_and_mark_read(client, db_session):
    _create_and_login(client, db_session, "admin4", "senha1234", UserRole.ADMIN)
    project = create_project(db_session, ProjectCreate(name="Projeto 4"))

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "gestor3", "senha1234", UserRole.GESTOR)
    client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket A"})

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "admin4", "password": "senha1234"})

    count_response = client.get("/api/notifications/unread-count")
    assert count_response.status_code == 200
    assert count_response.json()["unread_count"] == 1

    notification_id = client.get("/api/notifications").json()[0]["id"]
    read_response = client.post(f"/api/notifications/{notification_id}/read")
    assert read_response.status_code == 200
    assert read_response.json()["is_read"] is True

    count_after = client.get("/api/notifications/unread-count").json()["unread_count"]
    assert count_after == 0


def test_mark_all_read(client, db_session):
    _create_and_login(client, db_session, "admin5", "senha1234", UserRole.ADMIN)
    project = create_project(db_session, ProjectCreate(name="Projeto 5"))

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "gestor4", "senha1234", UserRole.GESTOR)
    client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket B"})
    client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket C"})

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "admin5", "password": "senha1234"})

    assert client.get("/api/notifications/unread-count").json()["unread_count"] == 2

    mark_response = client.post("/api/notifications/read-all")
    assert mark_response.status_code == 200

    assert client.get("/api/notifications/unread-count").json()["unread_count"] == 0


def test_cannot_mark_others_notification_as_read(client, db_session):
    _create_and_login(client, db_session, "admin6", "senha1234", UserRole.ADMIN)
    project = create_project(db_session, ProjectCreate(name="Projeto 6"))

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "gestor5", "senha1234", UserRole.GESTOR)
    client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket D"})

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "admin6", "password": "senha1234"})
    notification_id = client.get("/api/notifications").json()[0]["id"]

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "gestor5", "password": "senha1234"})
    response = client.post(f"/api/notifications/{notification_id}/read")

    assert response.status_code == 404


def test_comment_by_gestor_notifies_admin(client, db_session):
    _create_and_login(client, db_session, "admin7", "senha1234", UserRole.ADMIN)
    project = create_project(db_session, ProjectCreate(name="Projeto 7"))

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "gestor6", "senha1234", UserRole.GESTOR)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket E"}).json()["id"]
    client.post(f"/api/tickets/{ticket_id}/comments", json={"message": "Preciso de ajuda urgente"})

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "admin7", "password": "senha1234"})

    response = client.get("/api/notifications")
    titles = [n["title"] for n in response.json()]
    assert any("Novo comentário" in t for t in titles)


def test_comment_by_admin_notifies_ticket_author(client, db_session):
    _create_and_login(client, db_session, "admin8", "senha1234", UserRole.ADMIN)
    project = create_project(db_session, ProjectCreate(name="Projeto 8"))

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "gestor7", "senha1234", UserRole.GESTOR)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket F"}).json()["id"]

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "admin8", "password": "senha1234"})
    client.post(f"/api/tickets/{ticket_id}/comments", json={"message": "Já estou verificando"})

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "gestor7", "password": "senha1234"})

    response = client.get("/api/notifications")
    titles = [n["title"] for n in response.json()]
    assert any("Novo comentário" in t for t in titles)


def test_project_update_notifies_manager(client, db_session):
    _create_and_login(client, db_session, "admin9", "senha1234", UserRole.ADMIN)
    gestor = create_user(
        db_session, UserCreate(name="Gestor Oito", username="gestor8", password="senha1234", role=UserRole.GESTOR)
    )
    project = create_project(db_session, ProjectCreate(name="Projeto 9", manager_id=gestor.id))

    client.post(f"/api/projects/{project.id}/updates", json={"message": "Entrega adiantada"})

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "gestor8", "password": "senha1234"})

    response = client.get("/api/notifications")
    assert response.status_code == 200
    titles = [n["title"] for n in response.json()]
    assert any("Novo andamento" in t for t in titles)


def test_gestor_comment_on_operador_ticket_notifies_both_admin_and_operador(client, db_session):
    _create_and_login(client, db_session, "admin11", "senha1234", UserRole.ADMIN)
    project = create_project(db_session, ProjectCreate(name="Projeto 11"))

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "operador1", "senha1234", UserRole.OPERADOR)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket do operador"}).json()["id"]

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "gestor11", "senha1234", UserRole.GESTOR)
    # gestor não é dono do ticket, mas vê todas as solicitações e pode comentar
    response = client.post(f"/api/tickets/{ticket_id}/comments", json={"message": "Vou verificar isso"})
    assert response.status_code == 201

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "admin11", "password": "senha1234"})
    admin_titles = [n["title"] for n in client.get("/api/notifications").json()]
    assert any("Novo comentário" in t for t in admin_titles)

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "operador1", "password": "senha1234"})
    operador_titles = [n["title"] for n in client.get("/api/notifications").json()]
    assert any("Novo comentário" in t for t in operador_titles)


def test_attachment_upload_by_operador_notifies_admin(client, db_session, monkeypatch, tmp_path):
    from app.config import Settings

    monkeypatch.setattr(Settings, "storage_dir", property(lambda self: tmp_path))

    _create_and_login(client, db_session, "admin12", "senha1234", UserRole.ADMIN)
    project = create_project(db_session, ProjectCreate(name="Projeto 12"))

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "operador2", "senha1234", UserRole.OPERADOR)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket com print"}).json()["id"]
    client.post(
        f"/api/tickets/{ticket_id}/attachments", files={"file": ("print.png", b"fake", "image/png")}
    )

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "admin12", "password": "senha1234"})

    titles = [n["title"] for n in client.get("/api/notifications").json()]
    assert any("Novo anexo" in t for t in titles)


def test_attachment_upload_by_admin_does_not_notify_admin(client, db_session, monkeypatch, tmp_path):
    from app.config import Settings

    monkeypatch.setattr(Settings, "storage_dir", property(lambda self: tmp_path))

    _create_and_login(client, db_session, "admin13", "senha1234", UserRole.ADMIN)
    project = create_project(db_session, ProjectCreate(name="Projeto 13"))
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket do admin"}).json()["id"]
    client.post(f"/api/tickets/{ticket_id}/attachments", files={"file": ("print.png", b"fake", "image/png")})

    titles = [n["title"] for n in client.get("/api/notifications").json()]
    assert not any("Novo anexo" in t for t in titles)


def test_email_not_sent_when_smtp_disabled(client, db_session, monkeypatch):
    calls = []
    monkeypatch.setattr("app.services.email_service.smtplib.SMTP", lambda *a, **kw: calls.append((a, kw)))
    monkeypatch.setattr(settings, "SMTP_ENABLED", False)

    _create_and_login(client, db_session, "admin10", "senha1234", UserRole.ADMIN)
    project = create_project(db_session, ProjectCreate(name="Projeto 10"))

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "gestor9", "senha1234", UserRole.GESTOR)
    client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket G"})

    assert calls == []
