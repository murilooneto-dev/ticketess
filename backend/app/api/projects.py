from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.project import (
    ProjectCreate,
    ProjectOut,
    ProjectProgressUpdateCreate,
    ProjectProgressUpdateOut,
    ProjectUpdateIn,
)
from app.security.dependencies import get_current_user, require_admin
from app.services.project_service import (
    InvalidManagerError,
    ProjectNotFoundError,
    add_progress_update,
    create_project,
    delete_project,
    get_project,
    list_progress_updates,
    list_projects,
    update_project,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
def get_projects(
    mine: bool = Query(default=False),
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    manager_id = current_user.id if mine else None
    return list_projects(db, manager_id=manager_id)


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def post_project(
    payload: ProjectCreate,
    db: DbSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    try:
        return create_project(db, payload)
    except InvalidManagerError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gestor informado não existe")


@router.get("/{project_id}", response_model=ProjectOut)
def get_project_detail(
    project_id: int,
    db: DbSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado")
    return project


@router.put("/{project_id}", response_model=ProjectOut)
def put_project(
    project_id: int,
    payload: ProjectUpdateIn,
    db: DbSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    try:
        return update_project(db, project_id, payload)
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado")
    except InvalidManagerError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gestor informado não existe")


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_endpoint(
    project_id: int,
    db: DbSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    try:
        delete_project(db, project_id)
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado")


@router.get("/{project_id}/updates", response_model=list[ProjectProgressUpdateOut])
def get_project_updates(
    project_id: int,
    db: DbSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        return list_progress_updates(db, project_id)
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado")


@router.post("/{project_id}/updates", response_model=ProjectProgressUpdateOut, status_code=status.HTTP_201_CREATED)
def post_project_update(
    project_id: int,
    payload: ProjectProgressUpdateCreate,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        return add_progress_update(db, project_id, current_user.id, payload)
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado")
