from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.models.user import User, UserRole
from app.services.auth_service import get_user_by_session_token

SESSION_COOKIE_NAME = "devcontrol_session"


def get_current_user(
    devcontrol_session: str | None = Cookie(default=None),
    db: DbSession = Depends(get_db),
) -> User:
    if devcontrol_session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado")

    user = get_user_by_session_token(db, devcontrol_session)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida ou expirada")

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito ao administrador")
    return current_user
