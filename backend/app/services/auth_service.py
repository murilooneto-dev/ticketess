from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.config import settings
from app.models.session import Session
from app.models.user import User
from app.security.passwords import verify_password
from app.security.tokens import generate_session_token, hash_token
from app.services.user_service import get_user_by_username


class InvalidCredentialsError(Exception):
    pass


class InactiveUserError(Exception):
    pass


def authenticate(db: DbSession, username: str, password: str) -> User:
    user = get_user_by_username(db, username)
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()
    if not user.is_active:
        raise InactiveUserError()
    return user


def create_session(db: DbSession, user: User) -> str:
    token = generate_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.SESSION_EXPIRE_DAYS)

    session = Session(user_id=user.id, token_hash=hash_token(token), expires_at=expires_at)
    db.add(session)
    db.commit()

    return token


def get_user_by_session_token(db: DbSession, token: str) -> User | None:
    token_hash = hash_token(token)
    session = db.execute(
        select(Session).where(Session.token_hash == token_hash)
    ).scalar_one_or_none()

    if session is None:
        return None

    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        db.delete(session)
        db.commit()
        return None

    user = db.get(User, session.user_id)
    if user is None or not user.is_active:
        return None

    return user


def invalidate_session(db: DbSession, token: str) -> None:
    token_hash = hash_token(token)
    session = db.execute(
        select(Session).where(Session.token_hash == token_hash)
    ).scalar_one_or_none()
    if session is not None:
        db.delete(session)
        db.commit()
