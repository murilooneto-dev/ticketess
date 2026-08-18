import os
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.config import Settings, settings
from app.models.report import Report
from app.scheduler import jobs
from app.schemas.project import ProjectCreate
from app.services.project_service import create_project


def _bind_jobs_to_test_db(monkeypatch, db_session):
    monkeypatch.setattr(jobs, "SessionLocal", sessionmaker(bind=db_session.get_bind()))


def test_sqlite_db_path_parses_resolved_url():
    path = jobs._sqlite_db_path()
    assert path is not None
    assert str(path).endswith(".db")


def test_sync_all_github_repos_skips_when_disabled(db_session, monkeypatch):
    monkeypatch.setattr(settings, "GITHUB_ENABLED", False)
    called = []
    monkeypatch.setattr(jobs, "sync_project", lambda db, project: called.append(project.id))

    jobs.sync_all_github_repos()

    assert called == []


def test_sync_all_github_repos_only_syncs_projects_with_repo(db_session, monkeypatch):
    monkeypatch.setattr(settings, "GITHUB_ENABLED", True)
    _bind_jobs_to_test_db(monkeypatch, db_session)

    create_project(db_session, ProjectCreate(name="Sem repo"))
    with_repo = create_project(db_session, ProjectCreate(name="Com repo", github_repo="org/repo"))

    synced_ids = []

    class FakeResult:
        commits_synced = 1
        pull_requests_synced = 0

    def fake_sync(db, project):
        synced_ids.append(project.id)
        return FakeResult()

    monkeypatch.setattr(jobs, "sync_project", fake_sync)

    jobs.sync_all_github_repos()

    assert synced_ids == [with_repo.id]


def test_sync_all_github_repos_continues_after_error(db_session, monkeypatch):
    monkeypatch.setattr(settings, "GITHUB_ENABLED", True)
    _bind_jobs_to_test_db(monkeypatch, db_session)

    create_project(db_session, ProjectCreate(name="Repo A", github_repo="org/a"))
    create_project(db_session, ProjectCreate(name="Repo B", github_repo="org/b"))

    attempted = []

    class FakeResult:
        commits_synced = 0
        pull_requests_synced = 0

    def fake_sync(db, project):
        attempted.append(project.name)
        if project.name == "Repo A":
            from app.services.github_service import GithubApiError

            raise GithubApiError("boom")
        return FakeResult()

    monkeypatch.setattr(jobs, "sync_project", fake_sync)

    jobs.sync_all_github_repos()

    assert set(attempted) == {"Repo A", "Repo B"}


def test_generate_weekly_reports_skips_when_disabled(db_session, monkeypatch):
    monkeypatch.setattr(settings, "REPORT_ENABLED", False)
    _bind_jobs_to_test_db(monkeypatch, db_session)
    called = []
    monkeypatch.setattr(jobs, "generate_reports", lambda *a, **kw: called.append(1))

    jobs.generate_weekly_reports()

    assert called == []


def test_generate_weekly_reports_creates_both_reports(db_session, monkeypatch, tmp_path):
    monkeypatch.setattr(Settings, "reports_dir", property(lambda self: tmp_path))
    monkeypatch.setattr(settings, "REPORT_ENABLED", True)
    _bind_jobs_to_test_db(monkeypatch, db_session)

    jobs.generate_weekly_reports()

    reports = list(db_session.execute(select(Report)).scalars())
    assert len(reports) == 2
    assert {r.type.value for r in reports} == {"technical", "management"}
    assert all(r.period_end == date.today() for r in reports)
    assert all(r.generated_by is None for r in reports)


def test_backup_database_skips_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "BACKUP_ENABLED", False)
    jobs.backup_database()


def test_backup_database_creates_copy_and_cleans_expired(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "BACKUP_ENABLED", True)
    monkeypatch.setattr(Settings, "backups_dir", property(lambda self: tmp_path))
    monkeypatch.setattr(settings, "BACKUP_RETENTION_DAYS", 30)

    fake_db = tmp_path / "fake.db"
    fake_db.write_bytes(b"sqlite data")
    monkeypatch.setattr(jobs, "_sqlite_db_path", lambda: fake_db)

    jobs.backup_database()

    backups = list((tmp_path / "database").glob("devcontrol_*.db"))
    assert len(backups) == 1

    old_backup = tmp_path / "database" / "devcontrol_20200101_000000.db"
    old_backup.write_bytes(b"old")
    old_time = (datetime.now(timezone.utc) - timedelta(days=40)).timestamp()
    os.utime(old_backup, (old_time, old_time))

    jobs.backup_database()

    remaining = {f.name for f in (tmp_path / "database").glob("devcontrol_*.db")}
    assert old_backup.name not in remaining
