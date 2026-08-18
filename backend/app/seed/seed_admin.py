import logging

from app.config import settings
from app.database import SessionLocal
from app.services.user_service import ensure_admin_exists

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("app.security")

DEFAULT_ADMIN_PASSWORD = "changeme123"


def run() -> None:
    db = SessionLocal()
    try:
        ensure_admin_exists(db, settings.ADMIN_NAME, settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD)
    finally:
        db.close()
    logger.info("Verificação de administrador inicial concluída (username=%s)", settings.ADMIN_USERNAME)

    if settings.ADMIN_PASSWORD == DEFAULT_ADMIN_PASSWORD:
        level = logging.ERROR if settings.APP_ENV == "production" else logging.WARNING
        security_logger.log(
            level,
            "ADMIN_PASSWORD ainda está com o valor padrão de exemplo. Troque a senha do "
            "administrador (via .env ou pela tela de usuários) antes de usar em produção.",
        )
