from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.security.passwords import hash_password


class UsernameAlreadyExistsError(Exception):
    pass


class EmailAlreadyExistsError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


def list_users(db: DbSession) -> list[User]:
    return list(db.execute(select(User).order_by(User.name)).scalars())


def get_user_by_id(db: DbSession, user_id: int) -> User | None:
    return db.get(User, user_id)


def list_admins(db: DbSession) -> list[User]:
    query = select(User).where(User.role == UserRole.ADMIN, User.is_active.is_(True))
    return list(db.execute(query).scalars())


def get_user_by_username(db: DbSession, username: str) -> User | None:
    return db.execute(select(User).where(User.username == username.lower())).scalar_one_or_none()


def get_user_by_email(db: DbSession, email: str) -> User | None:
    return db.execute(select(User).where(User.email == email.lower())).scalar_one_or_none()


def create_user(db: DbSession, data: UserCreate) -> User:
    if get_user_by_username(db, data.username):
        raise UsernameAlreadyExistsError(data.username)
    if data.email and get_user_by_email(db, data.email):
        raise EmailAlreadyExistsError(data.email)

    user = User(
        name=data.name,
        username=data.username.lower(),
        email=data.email.lower() if data.email else None,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: DbSession, user_id: int, data: UserUpdate) -> User:
    user = get_user_by_id(db, user_id)
    if user is None:
        raise UserNotFoundError(user_id)

    if data.username is not None and data.username.lower() != user.username:
        if get_user_by_username(db, data.username):
            raise UsernameAlreadyExistsError(data.username)
        user.username = data.username.lower()

    if data.email is not None and data.email.lower() != user.email:
        if get_user_by_email(db, data.email):
            raise EmailAlreadyExistsError(data.email)
        user.email = data.email.lower()

    if data.name is not None:
        user.name = data.name
    if data.password is not None:
        user.password_hash = hash_password(data.password)
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active

    db.commit()
    db.refresh(user)
    return user


def ensure_admin_exists(db: DbSession, name: str, username: str, password: str) -> None:
    has_admin = db.execute(select(User).where(User.role == UserRole.ADMIN)).first()
    if has_admin:
        return
    if get_user_by_username(db, username):
        return

    admin = User(
        name=name,
        username=username.lower(),
        password_hash=hash_password(password),
        role=UserRole.ADMIN,
    )
    db.add(admin)
    db.commit()
