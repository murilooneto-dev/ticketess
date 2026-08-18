from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.security.dependencies import require_admin
from app.services.user_service import (
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
    UserNotFoundError,
    create_user,
    list_users,
    update_user,
)

router = APIRouter(prefix="/api/users", tags=["users"], dependencies=[Depends(require_admin)])


@router.get("", response_model=list[UserOut])
def get_users(db: DbSession = Depends(get_db)):
    return list_users(db)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def post_user(payload: UserCreate, db: DbSession = Depends(get_db)):
    try:
        return create_user(db, payload)
    except UsernameAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nome de usuário já cadastrado")
    except EmailAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado")


@router.put("/{user_id}", response_model=UserOut)
def put_user(user_id: int, payload: UserUpdate, db: DbSession = Depends(get_db)):
    try:
        return update_user(db, user_id, payload)
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    except UsernameAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nome de usuário já cadastrado")
    except EmailAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado")
