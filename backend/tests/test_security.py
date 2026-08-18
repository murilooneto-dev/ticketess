from app.models.user import UserRole
from app.schemas.user import UserCreate
from app.services.user_service import create_user


def _create_and_login(client, db_session, email, password, role):
    user = create_user(db_session, UserCreate(name=email.split("@")[0], username=email, password=password, role=role))
    client.post("/api/auth/login", json={"username": email, "password": password})
    return user


def test_security_headers_present(client, db_session):
    response = client.get("/api/system/health")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "same-origin"


def test_login_cookie_is_httponly_and_samesite(client, db_session):
    create_user(db_session, UserCreate(name="User", username="cookie", password="senha1234", role=UserRole.GESTOR))

    response = client.post("/api/auth/login", json={"username": "cookie", "password": "senha1234"})

    set_cookie = response.headers.get("set-cookie", "")
    assert "httponly" in set_cookie.lower()
    assert "samesite=lax" in set_cookie.lower()


def test_deactivated_user_session_stops_working_immediately(client, db_session):
    admin = _create_and_login(client, db_session, "admin", "senha1234", UserRole.ADMIN)
    user = create_user(
        db_session, UserCreate(name="Alvo", username="alvo", password="senha1234", role=UserRole.GESTOR)
    )

    # segunda sessão (outro "navegador") loga como o usuário que será desativado
    from fastapi.testclient import TestClient
    from app.main import app

    other_client = TestClient(app)
    other_client.post("/api/auth/login", json={"username": "alvo", "password": "senha1234"})
    assert other_client.get("/api/auth/me").status_code == 200

    client.put(f"/api/users/{user.id}", json={"is_active": False})

    response = other_client.get("/api/auth/me")
    assert response.status_code == 401


def test_password_shorter_than_minimum_is_rejected(client, db_session):
    _create_and_login(client, db_session, "admin2", "senha1234", UserRole.ADMIN)

    response = client.post(
        "/api/users", json={"name": "Curto", "username": "curto", "password": "123", "role": "gestor"}
    )

    assert response.status_code == 422


def test_session_token_not_reused_after_logout(client, db_session):
    create_user(db_session, UserCreate(name="User2", username="logout", password="senha1234", role=UserRole.GESTOR))
    client.post("/api/auth/login", json={"username": "logout", "password": "senha1234"})
    assert client.get("/api/auth/me").status_code == 200

    client.post("/api/auth/logout")

    assert client.get("/api/auth/me").status_code == 401
