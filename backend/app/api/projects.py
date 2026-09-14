from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdateIn
from app.services.project_service import (
    ProjectNotFoundError,
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
def get_projects(db: DbSession = Depends(get_db)):
    return list_projects(db)


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def post_project(payload: ProjectCreate, db: DbSession = Depends(get_db)):
    return create_project(db, payload)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project_detail(project_id: int, db: DbSession = Depends(get_db)):
    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado")
    return project


@router.put("/{project_id}", response_model=ProjectOut)
def put_project(project_id: int, payload: ProjectUpdateIn, db: DbSession = Depends(get_db)):
    try:
        return update_project(db, project_id, payload)
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado")


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_endpoint(project_id: int, db: DbSession = Depends(get_db)):
    try:
        delete_project(db, project_id)
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado")
