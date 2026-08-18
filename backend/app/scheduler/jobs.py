import logging
import shutil
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models.project import Project
from app.services.github_service import (
    GithubApiError,
    GithubNotEnabledError,
    GithubRepoNotConfiguredError,
    sync_project,
)
from app.services.report_service import generate_reports

logger = logging.getLogger("app.scheduler")


def sync_all_github_repos() -> None:
    if not settings.GITHUB_ENABLED:
        return

    db = SessionLocal()
    try:
        projects = list(
            db.execute(select(Project).where(Project.github_repo.isnot(None))).scalars()
        )
        for project in projects:
            try:
                result = sync_project(db, project)
                logger.info(
                    "Sincronização GitHub concluída para '%s': %s commit(s), %s pull request(s)",
                    project.name,
                    result.commits_synced,
                    result.pull_requests_synced,
                )
            except (GithubApiError, GithubNotEnabledError, GithubRepoNotConfiguredError) as exc:
                logger.warning("Falha ao sincronizar GitHub do projeto '%s': %s", project.name, exc)
    finally:
        db.close()


def generate_weekly_reports() -> None:
    if not settings.REPORT_ENABLED:
        return

    db = SessionLocal()
    try:
        period_end = date.today()
        period_start = period_end - timedelta(days=6)
        technical, management = generate_reports(db, period_start, period_end, None)
        logger.info(
            "Relatórios semanais gerados automaticamente: técnico #%s, gerencial #%s",
            technical.id,
            management.id,
        )
    finally:
        db.close()


def _sqlite_db_path() -> Path | None:
    url = settings.resolved_database_url
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        return None
    return Path(url[len(prefix):])


def backup_database() -> None:
    if not settings.BACKUP_ENABLED:
        return

    db_path = _sqlite_db_path()
    if db_path is None or not db_path.is_file():
        logger.warning("Backup ignorado: banco de dados não encontrado em %s", db_path)
        return

    backup_dir = settings.backups_dir / "database"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    destination = backup_dir / f"devcontrol_{timestamp}.db"
    shutil.copy2(db_path, destination)
    logger.info("Backup do banco de dados criado em %s", destination)

    _cleanup_old_backups(backup_dir)


def _cleanup_old_backups(backup_dir: Path) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.BACKUP_RETENTION_DAYS)
    for backup_file in backup_dir.glob("devcontrol_*.db"):
        modified_at = datetime.fromtimestamp(backup_file.stat().st_mtime, tz=timezone.utc)
        if modified_at < cutoff:
            backup_file.unlink()
            logger.info("Backup expirado removido: %s", backup_file)
