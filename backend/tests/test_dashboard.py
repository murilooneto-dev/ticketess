from app.schemas.project import ProjectCreate
from app.services.project_service import create_project


def test_dashboard_empty_state(client, db_session):
    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["total_projects"] == 0
    assert body["total_tickets"] == 0
    assert body["open_tickets"] == 0
    assert body["projects_by_status"] == {"ativo": 0, "pausado": 0, "concluido": 0, "cancelado": 0}
    assert set(body["tickets_by_status"].keys()) == {"aberto", "em_andamento", "aguardando", "concluido", "cancelado"}
    assert set(body["tickets_by_priority"].keys()) == {"baixa", "media", "alta", "urgente"}
    assert body["recent_tickets"] == []
    assert body["recent_commits"] == []
    assert body["recent_pull_requests"] == []


def test_dashboard_counts_reflect_data(client, db_session):
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
    # open_tickets exclui concluido/cancelado
    assert body["open_tickets"] == 1
