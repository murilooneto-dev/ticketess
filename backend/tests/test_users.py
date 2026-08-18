from app.models.user import UserRole
from app.schemas.user import UserCreate
from app.services.user_service import create_user


def _create_and_login(client, db_session, email, password, role):
    create_user(db_session, UserCreate(name="Test", username=email, password=password, role=role))
    client.post("/api/auth/login", json={"username": email, "password": password})


def test_gestor_cannot_list_users(client, db_session):
    _create_and_login(client, db_session, "gestor", "senha1234", UserRole.GESTOR)

    response = client.get("/api/users")

    assert response.status_code == 403


def test_admin_can_list_users(client, db_session):
    _create_and_login(client, db_session, "admin", "senha1234", UserRole.ADMIN)

    response = client.get("/api/users")

    assert response.status_code == 200
    emails = [u["username"] for u in response.json()]
    assert "admin" in emails


def test_admin_can_create_user(client, db_session):
    _create_and_login(client, db_session, "admin2", "senha1234", UserRole.ADMIN)

    response = client.post(
        "/api/users",
        json={"name": "Novo Gestor", "username": "novo", "password": "outrasenha", "role": "gestor"},
    )

    assert response.status_code == 201
    assert response.json()["username"] == "novo"


def test_admin_cannot_create_user_with_duplicate_email(client, db_session):
    _create_and_login(client, db_session, "admin3", "senha1234", UserRole.ADMIN)

    response = client.post(
        "/api/users",
        json={"name": "Duplicado", "username": "admin3", "password": "outrasenha", "role": "gestor"},
    )

    assert response.status_code == 409


def test_unauthenticated_user_cannot_access_users_endpoint(client, db_session):
    response = client.get("/api/users")
    assert response.status_code == 401
