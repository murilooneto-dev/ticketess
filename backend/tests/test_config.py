from app.config import settings


def test_settings_load_defaults():
    assert settings.APP_NAME == "TickeTess"
    assert settings.APP_PORT == 8000
    assert settings.DATABASE_URL.startswith("sqlite:///")


def test_resolved_database_url_is_absolute():
    resolved = settings.resolved_database_url
    assert resolved.startswith("sqlite:///")
    assert "devcontrol.db" in resolved


def test_directory_properties_point_inside_project_root():
    assert settings.data_dir.name == "data"
    assert settings.storage_dir.name == "storage"
    assert settings.reports_dir.name == "reports"
    assert settings.backups_dir.name == "backups"
    assert settings.logs_dir.name == "logs"
