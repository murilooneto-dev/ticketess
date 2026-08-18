from app.models.user import UserRole
from app.services.user_service import create_user
from app.schemas.user import UserCreate


def _create_user(db_session, username="user", password="senha1234", role=UserRole.GESTOR):
    return create_user(
        db_session,
        UserCreate(name="Test User", username=username, password=password, role=role),
    )


def test_login_with_valid_credentials_sets_cookie(client, db_session):
    _create_user(db_session)

    response = client.post("/api/auth/login", json={"username": "user", "password": "senha1234"})

    assert response.status_code == 200
    assert "devcontrol_session" in response.cookies
    assert response.json()["user"]["username"] == "user"


def test_login_with_invalid_password_fails(client, db_session):
    _create_user(db_session)

    response = client.post("/api/auth/login", json={"username": "user", "password": "wrongpass"})

    assert response.status_code == 401


def test_login_with_unknown_email_fails(client, db_session):
    response = client.post("/api/auth/login", json={"username": "nobody", "password": "senha1234"})

    assert response.status_code == 401


def test_me_requires_authentication(client, db_session):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user_after_login(client, db_session):
    _create_user(db_session)
    client.post("/api/auth/login", json={"username": "user", "password": "senha1234"})

    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json()["username"] == "user"


def test_logout_invalidates_session(client, db_session):
    _create_user(db_session)
    client.post("/api/auth/login", json={"username": "user", "password": "senha1234"})

    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 200

    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 401


def test_inactive_user_cannot_login(client, db_session):
    user = _create_user(db_session, username="inactive")
    user.is_active = False
    db_session.commit()

    response = client.post("/api/auth/login", json={"username": "inactive", "password": "senha1234"})

    assert response.status_code == 401
