from datetime import date, timedelta

from app.config import Settings
from app.schemas.project import ProjectCreate
from app.services.project_service import create_project


def _patch_reports_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(Settings, "reports_dir", property(lambda self: tmp_path))


def test_generates_reports_with_explicit_period(client, db_session, monkeypatch, tmp_path):
    _patch_reports_dir(monkeypatch, tmp_path)
    project = create_project(db_session, ProjectCreate(name="Projeto A"))
    ticket = client.post("/api/tickets", json={"project_id": project.id, "title": "Bug X", "type": "bug"}).json()
    client.put(f"/api/tickets/{ticket['id']}", json={"status": "concluido"})

    start = date.today().isoformat()
    end = date.today().isoformat()
    response = client.post("/api/reports/generate", json={"period_start": start, "period_end": end})

    assert response.status_code == 200
    body = response.json()
    assert body["technical"]["type"] == "technical"
    assert body["management"]["type"] == "management"
    assert body["technical"]["period_start"] == start
    assert body["management"]["period_end"] == end

    technical_files = list((tmp_path / "technical").glob("*.pdf"))
    management_files = list((tmp_path / "management").glob("*.pdf"))
    assert len(technical_files) == 1
    assert len(management_files) == 1
    assert technical_files[0].read_bytes().startswith(b"%PDF")
    assert management_files[0].read_bytes().startswith(b"%PDF")


def test_default_period_is_last_seven_days(client, db_session, monkeypatch, tmp_path):
    _patch_reports_dir(monkeypatch, tmp_path)

    response = client.post("/api/reports/generate", json={})

    assert response.status_code == 200
    body = response.json()
    expected_start = (date.today() - timedelta(days=6)).isoformat()
    expected_end = date.today().isoformat()
    assert body["technical"]["period_start"] == expected_start
    assert body["technical"]["period_end"] == expected_end


def test_regenerating_same_period_does_not_duplicate(client, db_session, monkeypatch, tmp_path):
    _patch_reports_dir(monkeypatch, tmp_path)

    payload = {"period_start": "2026-01-01", "period_end": "2026-01-07"}
    client.post("/api/reports/generate", json=payload)
    client.post("/api/reports/generate", json=payload)

    response = client.get("/api/reports")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_download_report(client, db_session, monkeypatch, tmp_path):
    _patch_reports_dir(monkeypatch, tmp_path)
    result = client.post("/api/reports/generate", json={}).json()

    technical_response = client.get(f"/api/reports/{result['technical']['id']}/download")
    management_response = client.get(f"/api/reports/{result['management']['id']}/download")

    assert technical_response.status_code == 200
    assert management_response.status_code == 200
    assert management_response.headers["content-type"] == "application/pdf"


def test_download_nonexistent_report_returns_404(client, db_session, monkeypatch, tmp_path):
    _patch_reports_dir(monkeypatch, tmp_path)

    response = client.get("/api/reports/9999/download")

    assert response.status_code == 404


def test_invalid_period_range_rejected(client, db_session, monkeypatch, tmp_path):
    _patch_reports_dir(monkeypatch, tmp_path)

    response = client.post(
        "/api/reports/generate", json={"period_start": "2026-02-01", "period_end": "2026-01-01"}
    )

    assert response.status_code == 422
