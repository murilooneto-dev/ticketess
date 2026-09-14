from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "TickeTess"
    APP_ENV: str = "development"

    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    DATABASE_URL: str = "sqlite:///./data/devcontrol.db"

    @property
    def resolved_database_url(self) -> str:
        prefix = "sqlite:///./"
        if self.DATABASE_URL.startswith(prefix):
            relative_path = self.DATABASE_URL[len(prefix):]
            absolute_path = (BASE_DIR / relative_path).resolve()
            return f"sqlite:///{absolute_path.as_posix()}"
        return self.DATABASE_URL

    TIMEZONE: str = "America/Fortaleza"

    GITHUB_ENABLED: bool = True
    GITHUB_TOKEN: str = ""
    GITHUB_SYNC_INTERVAL: int = 15

    REPORT_ENABLED: bool = True
    REPORT_DAY: int = 5
    REPORT_TIME: str = "17:30"

    BACKUP_ENABLED: bool = True
    BACKUP_TIME: str = "02:00"
    BACKUP_RETENTION_DAYS: int = 30

    UPLOAD_MAX_SIZE_MB: int = 20

    @property
    def data_dir(self) -> Path:
        return BASE_DIR / "data"

    @property
    def storage_dir(self) -> Path:
        return BASE_DIR / "storage"

    @property
    def reports_dir(self) -> Path:
        return BASE_DIR / "reports"

    @property
    def backups_dir(self) -> Path:
        return BASE_DIR / "backups"

    @property
    def logs_dir(self) -> Path:
        return BASE_DIR / "logs"

    @property
    def frontend_dist_dir(self) -> Path:
        return BASE_DIR / "frontend" / "dist"


settings = Settings()
