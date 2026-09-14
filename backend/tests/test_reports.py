from datetime import date, timedelta

from app.config import Settings
from app.schemas.project import ProjectCreate
from app.services.project_service import create_project


def _patch_reports_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(Settings, "reports_dir", property(lambda self: tmp_path))


def test_generates_report_with_explicit_period(client, db_session, monkeypatch, tmp_path):
    _patch_reports_dir(monkeypatch, tmp_path)
    project = create_project(db_session, ProjectCreate(name="Projeto A"))
    ticket = client.post("/api/tickets", json={"project_id": project.id, "title": "Bug X", "type": "bug"}).json()
    client.put(f"/api/tickets/{ticket['id']}", json={"status": "concluido"})

    start = date.today().isoformat()
    end = date.today().isoformat()
    response = client.post("/api/reports/generate", json={"period_start": start, "period_end": end})

    assert response.status_code == 200
    body = response.json()
    assert body["period_start"] == start
    assert body["period_end"] == end

    report_files = list(tmp_path.glob("*.pdf"))
    assert len(report_files) == 1
    assert report_files[0].read_bytes().startswith(b"%PDF")


def test_default_period_is_last_seven_days(client, db_session, monkeypatch, tmp_path):
    _patch_reports_dir(monkeypatch, tmp_path)

    response = client.post("/api/reports/generate", json={})

    assert response.status_code == 200
    body = response.json()
    expected_start = (date.today() - timedelta(days=6)).isoformat()
    expected_end = date.today().isoformat()
    assert body["period_start"] == expected_start
    assert body["period_end"] == expected_end


def test_regenerating_same_period_does_not_duplicate(client, db_session, monkeypatch, tmp_path):
    _patch_reports_dir(monkeypatch, tmp_path)

    payload = {"period_start": "2026-01-01", "period_end": "2026-01-07"}
    client.post("/api/reports/generate", json=payload)
    client.post("/api/reports/generate", json=payload)

    response = client.get("/api/reports")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_download_report(client, db_session, monkeypatch, tmp_path):
    _patch_reports_dir(monkeypatch, tmp_path)
    result = client.post("/api/reports/generate", json={}).json()

    response = client.get(f"/api/reports/{result['id']}/download")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


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
