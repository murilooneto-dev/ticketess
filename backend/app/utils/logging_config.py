import logging
from logging.handlers import RotatingFileHandler

from app.config import settings

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5


def _make_handler(filename: str, level: int) -> RotatingFileHandler:
    path = settings.logs_dir / filename
    handler = RotatingFileHandler(path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    return handler


def setup_logging() -> None:
    settings.logs_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    if root.handlers:
        return

    app_handler = _make_handler("app.log", logging.INFO)
    error_handler = _make_handler("error.log", logging.ERROR)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    root.addHandler(app_handler)
    root.addHandler(error_handler)
    root.addHandler(console_handler)

    for logger_name, filename in (
        ("app.github", "github.log"),
        ("app.scheduler", "scheduler.log"),
        ("app.security", "security.log"),
    ):
        logger = logging.getLogger(logger_name)
        logger.addHandler(_make_handler(filename, logging.INFO))
