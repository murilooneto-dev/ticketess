from datetime import date, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.schemas.report import ReportGenerateRequest, ReportGenerateResponse, ReportOut
from app.services.report_service import generate_reports, get_report, list_reports

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/generate", response_model=ReportGenerateResponse)
def post_generate_reports(payload: ReportGenerateRequest, db: DbSession = Depends(get_db)):
    period_end = payload.period_end or date.today()
    period_start = payload.period_start or (period_end - timedelta(days=6))

    technical, management = generate_reports(db, period_start, period_end)
    return ReportGenerateResponse(technical=technical, management=management)


@router.get("", response_model=list[ReportOut])
def get_reports(db: DbSession = Depends(get_db)):
    return list_reports(db)


@router.get("/{report_id}/download")
def download_report(report_id: int, db: DbSession = Depends(get_db)):
    report = get_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relatório não encontrado")

    file_path = Path(report.file_path)
    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo do relatório não encontrado")

    return FileResponse(file_path, filename=file_path.name, media_type="application/pdf")
