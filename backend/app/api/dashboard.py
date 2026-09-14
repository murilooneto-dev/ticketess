from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import build_summary

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: DbSession = Depends(get_db)):
    return build_summary(db)
