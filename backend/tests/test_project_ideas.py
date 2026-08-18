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
