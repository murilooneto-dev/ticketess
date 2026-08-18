from app.models.project_idea import ProjectIdea, ProjectIdeaStatus
from app.models.user import UserRole
from app.schemas.user import UserCreate
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
