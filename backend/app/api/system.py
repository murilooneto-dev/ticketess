import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

router = APIRouter(prefix="/api/system", tags=["system"])
logger = logging.getLogger(__name__)


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Database health check failed")
        db_status = "error"

    storage_status = "ok" if settings.storage_dir.exists() else "error"

    return {
        "status": "ok" if db_status == "ok" and storage_status == "ok" else "error",
        "database": db_status,
        "storage": storage_status,
    }
