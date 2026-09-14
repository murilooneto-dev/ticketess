import pytest

from app.config import Settings, settings
from app.schemas.project import ProjectCreate
from app.services.project_service import create_project
from app.services.ticket_service import (
    TicketAlreadyFinalizedError,
    TicketNotFinalizableError,
    create_ticket,
    finalize_ticket,
    list_tickets,
    update_ticket,
)
from app.schemas.ticket import TicketCreate, TicketUpdateIn


def _create_project(db_session, name="Projeto Teste"):
    return create_project(db_session, ProjectCreate(name=name))


def test_create_ticket(client, db_session):
    project = _create_project(db_session)

    response = client.post(
        "/api/tickets",
        json={
            "project_id": project.id,
            "title": "Botão quebrado",
            "type": "bug",
            "priority": "alta",
            "requester_name": "Maria",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Botão quebrado"
    assert body["status"] == "aberto"
    assert body["requester_name"] == "Maria"
    assert body["finalized_at"] is None


def test_create_ticket_with_custom_status(client, db_session):
    project = _create_project(db_session)

    response = client.post(
        "/api/tickets",
        json={"project_id": project.id, "title": "Já em andamento", "status": "em_andamento"},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "em_andamento"


def test_create_ticket_with_invalid_project_fails(client, db_session):
    response = client.post("/api/tickets", json={"project_id": 999, "title": "Ticket X"})

    assert response.status_code == 400


def test_update_ticket_status_and_history_is_recorded(client, db_session):
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


def test_project_filter_returns_only_matching_tickets(client, db_session):
    project_a = _create_project(db_session, "Projeto A")
    project_b = _create_project(db_session, "Projeto B")
    client.post("/api/tickets", json={"project_id": project_a.id, "title": "Ticket A"})
    client.post("/api/tickets", json={"project_id": project_b.id, "title": "Ticket B"})

    response = client.get(f"/api/tickets?project_id={project_a.id}")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Ticket A"


def test_comment_flow(client, db_session):
    project = _create_project(db_session)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket C"}).json()["id"]

    post_response = client.post(f"/api/tickets/{ticket_id}/comments", json={"message": "Analisando o problema"})
    assert post_response.status_code == 201

    get_response = client.get(f"/api/tickets/{ticket_id}/comments")
    assert get_response.status_code == 200
    assert len(get_response.json()) == 1
    assert get_response.json()[0]["message"] == "Analisando o problema"


def test_comment_on_nonexistent_ticket_returns_404(client, db_session):
    response = client.post("/api/tickets/9999/comments", json={"message": "oi"})

    assert response.status_code == 404


def test_attachment_upload_and_download(client, db_session, monkeypatch, tmp_path):
    monkeypatch.setattr(Settings, "storage_dir", property(lambda self: tmp_path))

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

    project = _create_project(db_session)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket E"}).json()["id"]

    response = client.post(
        f"/api/tickets/{ticket_id}/attachments",
        files={"file": ("grande.txt", b"x" * 1024, "text/plain")},
    )

    assert response.status_code == 413


def test_ticket_not_found_returns_404(client, db_session):
    response = client.get("/api/tickets/9999")

    assert response.status_code == 404


def test_new_ticket_has_no_finalized_at(client, db_session):
    project = _create_project(db_session)

    response = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket Fin"})

    assert response.status_code == 201
    assert response.json()["finalized_at"] is None


def test_finalize_concluded_ticket_sets_finalized_at(db_session):
    project = _create_project(db_session)
    ticket = create_ticket(db_session, TicketCreate(project_id=project.id, title="Ticket Fin2"))
    update_ticket(db_session, ticket.id, TicketUpdateIn(status="concluido"))

    ticket = finalize_ticket(db_session, ticket.id)

    assert ticket.finalized_at is not None


def test_finalize_open_ticket_raises(db_session):
    project = _create_project(db_session)
    ticket = create_ticket(db_session, TicketCreate(project_id=project.id, title="Ticket Fin3"))

    with pytest.raises(TicketNotFinalizableError):
        finalize_ticket(db_session, ticket.id)


def test_finalize_twice_raises(db_session):
    project = _create_project(db_session)
    ticket = create_ticket(db_session, TicketCreate(project_id=project.id, title="Ticket Fin4"))
    update_ticket(db_session, ticket.id, TicketUpdateIn(status="cancelado"))
    finalize_ticket(db_session, ticket.id)

    with pytest.raises(TicketAlreadyFinalizedError):
        finalize_ticket(db_session, ticket.id)


def test_list_tickets_excludes_finalized_by_default(db_session):
    project = _create_project(db_session)

    ticket = create_ticket(db_session, TicketCreate(project_id=project.id, title="Ativo"))
    finalized_ticket = create_ticket(db_session, TicketCreate(project_id=project.id, title="Encerrado"))
    update_ticket(db_session, finalized_ticket.id, TicketUpdateIn(status="concluido"))
    finalize_ticket(db_session, finalized_ticket.id)

    active = list_tickets(db_session)
    history = list_tickets(db_session, finalized=True)

    assert [t.id for t in active] == [ticket.id]
    assert [t.id for t in history] == [finalized_ticket.id]


def test_finalize_endpoint_rejects_open_ticket(client, db_session):
    project = _create_project(db_session)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket Fin6"}).json()["id"]

    response = client.post(f"/api/tickets/{ticket_id}/finalize")

    assert response.status_code == 400


def test_finalize_endpoint_moves_ticket_to_history(client, db_session):
    project = _create_project(db_session)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket Fin7"}).json()["id"]
    client.put(f"/api/tickets/{ticket_id}", json={"status": "concluido"})

    finalize_response = client.post(f"/api/tickets/{ticket_id}/finalize")
    assert finalize_response.status_code == 200
    assert finalize_response.json()["finalized_at"] is not None

    active = client.get("/api/tickets").json()
    history = client.get("/api/tickets?finalized=true").json()
    assert ticket_id not in [t["id"] for t in active]
    assert ticket_id in [t["id"] for t in history]


def test_cannot_update_finalized_ticket(client, db_session):
    project = _create_project(db_session)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket Fin8"}).json()["id"]
    client.put(f"/api/tickets/{ticket_id}", json={"status": "concluido"})
    client.post(f"/api/tickets/{ticket_id}/finalize")

    response = client.put(f"/api/tickets/{ticket_id}", json={"status": "cancelado"})

    assert response.status_code == 400
