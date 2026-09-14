def test_list_projects_empty(client, db_session):
    response = client.get("/api/projects")

    assert response.status_code == 200
    assert response.json() == []


def test_create_project(client, db_session):
    response = client.post(
        "/api/projects",
        json={"name": "Sistema Financeiro", "description": "Controle de contas"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Sistema Financeiro"
    assert body["status"] == "ativo"


def test_update_project_status(client, db_session):
    create_response = client.post("/api/projects", json={"name": "Projeto Y"})
    project_id = create_response.json()["id"]

    response = client.put(f"/api/projects/{project_id}", json={"status": "concluido"})

    assert response.status_code == 200
    assert response.json()["status"] == "concluido"


def test_update_nonexistent_project_returns_404(client, db_session):
    response = client.put("/api/projects/9999", json={"status": "concluido"})

    assert response.status_code == 404


def test_rename_project(client, db_session):
    project_id = client.post("/api/projects", json={"name": "Nome Antigo"}).json()["id"]

    response = client.put(f"/api/projects/{project_id}", json={"name": "Nome Novo"})

    assert response.status_code == 200
    assert response.json()["name"] == "Nome Novo"


def test_delete_project(client, db_session):
    project_id = client.post("/api/projects", json={"name": "Projeto Descartável"}).json()["id"]

    response = client.delete(f"/api/projects/{project_id}")

    assert response.status_code == 204
    assert client.get(f"/api/projects/{project_id}").status_code == 404


def test_deleting_project_cascades_tickets(client, db_session):
    project_id = client.post("/api/projects", json={"name": "Projeto Com Tickets"}).json()["id"]
    ticket_id = client.post("/api/tickets", json={"project_id": project_id, "title": "Ticket órfão"}).json()["id"]

    response = client.delete(f"/api/projects/{project_id}")

    assert response.status_code == 204
    assert client.get(f"/api/tickets/{ticket_id}").status_code == 404


def test_delete_nonexistent_project_returns_404(client, db_session):
    response = client.delete("/api/projects/9999")

    assert response.status_code == 404
