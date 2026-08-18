import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.scheduler.jobs import backup_database, generate_weekly_reports, sync_all_github_repos

logger = logging.getLogger("app.scheduler")

_scheduler: BackgroundScheduler | None = None


def _parse_time(value: str) -> tuple[int, int]:
    hour_str, minute_str = value.split(":")
    return int(hour_str), int(minute_str)


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return

    scheduler = BackgroundScheduler(timezone=settings.TIMEZONE)

    if settings.GITHUB_ENABLED:
        scheduler.add_job(
            sync_all_github_repos,
            trigger=IntervalTrigger(minutes=settings.GITHUB_SYNC_INTERVAL),
            id="github_sync",
            replace_existing=True,
            max_instances=1,
        )
        logger.info("Job de sincronização GitHub agendado a cada %s minuto(s)", settings.GITHUB_SYNC_INTERVAL)

    if settings.REPORT_ENABLED:
        hour, minute = _parse_time(settings.REPORT_TIME)
        scheduler.add_job(
            generate_weekly_reports,
            trigger=CronTrigger(day_of_week=settings.REPORT_DAY, hour=hour, minute=minute),
            id="weekly_reports",
            replace_existing=True,
            max_instances=1,
        )
        logger.info(
            "Job de relatórios semanais agendado para o dia %s às %s", settings.REPORT_DAY, settings.REPORT_TIME
        )

    if settings.BACKUP_ENABLED:
        hour, minute = _parse_time(settings.BACKUP_TIME)
        scheduler.add_job(
            backup_database,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="daily_backup",
            replace_existing=True,
            max_instances=1,
        )
        logger.info("Job de backup diário agendado para %s", settings.BACKUP_TIME)

    scheduler.start()
    _scheduler = scheduler
    logger.info("Scheduler iniciado")


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler finalizado")
