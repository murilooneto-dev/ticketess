import logging

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session as DbSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.user import UserOut
from app.security.dependencies import SESSION_COOKIE_NAME, get_current_user
from app.services.auth_service import (
    InactiveUserError,
    InvalidCredentialsError,
    authenticate,
    create_session,
    invalidate_session,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger("app.security")


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response, db: DbSession = Depends(get_db)):
    try:
        user = authenticate(db, payload.username, payload.password)
    except (InvalidCredentialsError, InactiveUserError):
        logger.warning("Falha de login para %s", payload.username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha inválidos")

    token = create_session(db, user)

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.SESSION_EXPIRE_DAYS * 24 * 60 * 60,
    )

    logger.info("Login bem-sucedido para %s", user.username)
    return LoginResponse(user=UserOut.model_validate(user))


@router.post("/logout")
def logout(
    response: Response,
    devcontrol_session: str | None = Cookie(default=None),
    db: DbSession = Depends(get_db),
):
    if devcontrol_session:
        invalidate_session(db, devcontrol_session)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"detail": "Logout realizado"}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
