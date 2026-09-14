from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.schemas.project_idea import ProjectIdeaCreate, ProjectIdeaOut, ProjectIdeaStatusUpdate
from app.services.project_idea_service import (
    ProjectIdeaMissingProjectError,
    ProjectIdeaNotFoundError,
    ProjectIdeaRejectionReasonRequiredError,
    ProjectNotFoundError,
    create_project_idea,
    list_project_ideas,
    update_project_idea_status,
)
from app.services.ticket_service import ProjectNotFoundError as TicketProjectNotFoundError

router = APIRouter(prefix="/api/project-ideas", tags=["project-ideas"])


@router.get("", response_model=list[ProjectIdeaOut])
def get_project_ideas(db: DbSession = Depends(get_db)):
    return list_project_ideas(db)


@router.post("", response_model=ProjectIdeaOut, status_code=status.HTTP_201_CREATED)
def post_project_idea(payload: ProjectIdeaCreate, db: DbSession = Depends(get_db)):
    try:
        return create_project_idea(db, payload)
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Projeto informado não existe")


@router.patch("/{idea_id}", response_model=ProjectIdeaOut)
def patch_project_idea_status(idea_id: int, payload: ProjectIdeaStatusUpdate, db: DbSession = Depends(get_db)):
    try:
        return update_project_idea_status(
            db,
            idea_id,
            payload.status,
            project_id=payload.project_id,
            rejection_reason=payload.rejection_reason,
        )
    except ProjectIdeaNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ideia não encontrada")
    except ProjectIdeaMissingProjectError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Selecione um projeto para aprovar esta ideia"
        )
    except (ProjectNotFoundError, TicketProjectNotFoundError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Projeto informado não existe")
    except ProjectIdeaRejectionReasonRequiredError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe o motivo da rejeição")
