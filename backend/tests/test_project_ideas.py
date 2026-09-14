import pytest

from app.models.project import Project
from app.models.project_idea import ProjectIdea, ProjectIdeaStatus
from app.schemas.project_idea import ProjectIdeaCreate
from app.services.project_idea_service import (
    ProjectIdeaMissingProjectError,
    ProjectIdeaNotFoundError,
    ProjectIdeaRejectionReasonRequiredError,
    create_project_idea,
    list_project_ideas,
    update_project_idea_status,
)


def _create_project(db_session, name="Projeto Teste"):
    project = Project(name=name)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


def test_project_idea_model_persists_with_default_status(db_session):
    idea = ProjectIdea(title="App de estoque", description="Controlar estoque pelo celular")
    db_session.add(idea)
    db_session.commit()
    db_session.refresh(idea)

    assert idea.id is not None
    assert idea.status == ProjectIdeaStatus.PENDENTE


def test_create_project_idea(db_session):
    project = _create_project(db_session)

    idea = create_project_idea(
        db_session, ProjectIdeaCreate(title="Portal do cliente", description="Ideia legal", project_id=project.id)
    )

    assert idea.status == ProjectIdeaStatus.PENDENTE
    assert idea.title == "Portal do cliente"


def test_list_project_ideas(db_session):
    project = _create_project(db_session)
    create_project_idea(db_session, ProjectIdeaCreate(title="Ideia A", description="desc", project_id=project.id))
    create_project_idea(db_session, ProjectIdeaCreate(title="Ideia B", description="desc", project_id=project.id))

    ideas = list_project_ideas(db_session)

    assert len(ideas) == 2


def test_update_nonexistent_idea_raises(db_session):
    with pytest.raises(ProjectIdeaNotFoundError):
        update_project_idea_status(db_session, 9999, ProjectIdeaStatus.REJEITADA)


def test_create_idea_with_invalid_project_fails(client, db_session):
    response = client.post("/api/project-ideas", json={"title": "Ideia", "description": "desc", "project_id": 9999})

    assert response.status_code == 400


def test_submit_idea_via_api(client, db_session):
    project = _create_project(db_session)

    response = client.post(
        "/api/project-ideas",
        json={"title": "App interno", "description": "Facilita o dia a dia", "project_id": project.id},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "App interno"
    assert body["status"] == "pendente"


def test_change_status_of_unknown_idea_returns_404(client, db_session):
    response = client.patch("/api/project-ideas/9999", json={"status": "rejeitada"})

    assert response.status_code == 404


def test_project_idea_model_persists_project_and_rejection_reason(db_session):
    project = Project(name="Projeto X")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    idea = ProjectIdea(
        title="Ideia com projeto",
        description="desc",
        project_id=project.id,
        rejection_reason="Fora do escopo atual",
    )
    db_session.add(idea)
    db_session.commit()
    db_session.refresh(idea)

    assert idea.project_id == project.id
    assert idea.project.name == "Projeto X"
    assert idea.rejection_reason == "Fora do escopo atual"


def test_approving_idea_creates_ticket(db_session):
    project = _create_project(db_session)
    idea = create_project_idea(
        db_session, ProjectIdeaCreate(title="Ideia F", description="Descrição F", project_id=project.id)
    )

    update_project_idea_status(db_session, idea.id, ProjectIdeaStatus.APROVADA)

    from app.models.ticket import Ticket

    tickets = db_session.query(Ticket).filter(Ticket.project_id == project.id).all()
    assert len(tickets) == 1
    assert tickets[0].title == "Ideia F"
    assert tickets[0].description == "Descrição F"


def test_approving_idea_without_project_requires_project_id(db_session):
    idea = ProjectIdea(title="Ideia legada", description="desc")
    db_session.add(idea)
    db_session.commit()
    db_session.refresh(idea)

    with pytest.raises(ProjectIdeaMissingProjectError):
        update_project_idea_status(db_session, idea.id, ProjectIdeaStatus.APROVADA)


def test_approving_legacy_idea_with_supplied_project_id_succeeds(db_session):
    project = _create_project(db_session)
    idea = ProjectIdea(title="Ideia legada 2", description="desc")
    db_session.add(idea)
    db_session.commit()
    db_session.refresh(idea)

    updated = update_project_idea_status(db_session, idea.id, ProjectIdeaStatus.APROVADA, project_id=project.id)

    assert updated.project_id == project.id


def test_rejecting_idea_without_reason_raises(db_session):
    project = _create_project(db_session)
    idea = create_project_idea(db_session, ProjectIdeaCreate(title="Ideia G", description="desc", project_id=project.id))

    with pytest.raises(ProjectIdeaRejectionReasonRequiredError):
        update_project_idea_status(db_session, idea.id, ProjectIdeaStatus.REJEITADA)


def test_rejecting_idea_with_reason(db_session):
    project = _create_project(db_session)
    idea = create_project_idea(db_session, ProjectIdeaCreate(title="Ideia H", description="desc", project_id=project.id))

    updated = update_project_idea_status(
        db_session, idea.id, ProjectIdeaStatus.REJEITADA, rejection_reason="Fora do orçamento deste trimestre"
    )

    assert updated.rejection_reason == "Fora do orçamento deste trimestre"


def test_reject_endpoint_requires_reason(client, db_session):
    project = _create_project(db_session)
    idea_id = client.post(
        "/api/project-ideas", json={"title": "Ideia I", "description": "desc", "project_id": project.id}
    ).json()["id"]

    response = client.patch(f"/api/project-ideas/{idea_id}", json={"status": "rejeitada"})

    assert response.status_code == 400


def test_reject_endpoint_with_reason_succeeds(client, db_session):
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
    idea = ProjectIdea(title="Ideia legada 3", description="desc")
    db_session.add(idea)
    db_session.commit()
    db_session.refresh(idea)

    response = client.patch(f"/api/project-ideas/{idea.id}", json={"status": "aprovada", "project_id": 9999})

    assert response.status_code == 400
    assert response.json()["detail"] == "Projeto informado não existe"


def test_approving_idea_sets_generated_ticket_id(client, db_session):
    project = _create_project(db_session)
    idea = create_project_idea(db_session, ProjectIdeaCreate(title="Ideia K", description="desc", project_id=project.id))

    updated = update_project_idea_status(db_session, idea.id, ProjectIdeaStatus.APROVADA)

    assert updated.generated_ticket_id is not None

    idea2 = create_project_idea(db_session, ProjectIdeaCreate(title="Ideia L", description="desc", project_id=project.id))
    http_response = client.patch(f"/api/project-ideas/{idea2.id}", json={"status": "aprovada"})

    assert http_response.status_code == 200
    body = http_response.json()
    assert body["generated_ticket_id"] is not None
