# Ideias de Projeto Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let any logged-in user (admin, gestor, operador) submit a project idea (title + description); admin sees every idea and can approve/reject it, the author is notified when the status changes.

**Architecture:** Follows the existing Ticket feature's layering exactly: SQLAlchemy model → Pydantic schemas → service module (business logic + notifications) → FastAPI router → React service + single combined form/list page. Reuses the existing `notify_users`/`list_admins` helpers instead of building new notification plumbing.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 (SQLite), Alembic, Pydantic v2, pytest + FastAPI TestClient, React + `@tanstack/react-query`, plain CSS (`global.css`).

## Global Constraints

- Spec: `docs/superpowers/specs/2026-08-18-project-ideas-design.md`.
- Any authenticated user may submit an idea; only admin may change its status.
- Non-admin users only ever see their own ideas; admin sees all.
- No automatic conversion of an approved idea into a `Project` — status is a plain field, nothing more.
- Reuse `app.services.notification_service.notify_users` and `app.services.user_service.list_admins` — do not create parallel notification code.
- Follow existing file/module layout: one model file, one schema file, one service file, one API router file, one frontend service file, one frontend page — mirroring the Ticket feature's structure.
- Database is SQLite only (`backend/app/config.py:21`); SQLAlchemy `Enum` columns on SQLite are plain `VARCHAR` with no `CHECK` constraint (verified: `CreateTable(Notification.__table__)` renders no constraint), so adding new `NotificationType` members needs no migration — only new tables/columns do.

---

## File Structure

**Backend (new):**
- `backend/app/models/project_idea.py` — `ProjectIdea` model + `ProjectIdeaStatus` enum
- `backend/migrations/versions/<hash>_add_project_ideas.py` — creates `project_ideas` table
- `backend/app/schemas/project_idea.py` — `ProjectIdeaCreate`, `ProjectIdeaStatusUpdate`, `ProjectIdeaOut`
- `backend/app/services/project_idea_service.py` — `create_project_idea`, `list_project_ideas`, `update_project_idea_status`, `ProjectIdeaNotFoundError`
- `backend/app/api/project_ideas.py` — `GET/POST /api/project-ideas`, `PATCH /api/project-ideas/{id}`
- `backend/tests/test_project_ideas.py` — model, service, and API tests

**Backend (modified):**
- `backend/app/models/notification.py` — add `PROJECT_IDEA_CREATED`, `PROJECT_IDEA_STATUS_CHANGED` to `NotificationType`
- `backend/app/models/__init__.py` — register `ProjectIdea`, `ProjectIdeaStatus`
- `backend/app/main.py` — import and `include_router` for the new router

**Frontend (new):**
- `frontend/src/services/projectIdeas.js` — `fetchProjectIdeas`, `createProjectIdea`, `updateProjectIdeaStatus`
- `frontend/src/pages/ProjectIdeasPage.jsx` — form + list, role-aware

**Frontend (modified):**
- `frontend/src/routes/AppRoutes.jsx` — add `/project-ideas` route (any logged-in user)
- `frontend/src/components/NavBar.jsx` — add "Ideias" nav link
- `frontend/src/styles/global.css` — add `.badge-idea-pendente/aprovada/rejeitada`

---

### Task 1: Model, NotificationType values, and migration

**Files:**
- Create: `backend/app/models/project_idea.py`
- Modify: `backend/app/models/notification.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/migrations/versions/e8f1c3a9b6d2_add_project_ideas.py`
- Create: `backend/tests/test_project_ideas.py`

**Interfaces:**
- Produces: `ProjectIdea` (columns: `id`, `title: str`, `description: str`, `status: ProjectIdeaStatus`, `created_by: int`, `created_at: datetime`, `updated_at: datetime`, relationship `author: User`), `ProjectIdeaStatus` enum (`PENDENTE`, `APROVADA`, `REJEITADA`), and `NotificationType.PROJECT_IDEA_CREATED` / `NotificationType.PROJECT_IDEA_STATUS_CHANGED` — all consumed by Task 2's service module.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_project_ideas.py`:

```python
from app.models.project_idea import ProjectIdea, ProjectIdeaStatus
from app.models.user import UserRole
from app.schemas.user import UserCreate
from app.services.user_service import create_user


def _create_user(db_session, username, role):
    return create_user(
        db_session, UserCreate(name=username.capitalize(), username=username, password="senha1234", role=role)
    )


def test_project_idea_model_persists_with_default_status(db_session):
    user = _create_user(db_session, "gestor_model", UserRole.GESTOR)

    idea = ProjectIdea(title="App de estoque", description="Controlar estoque pelo celular", created_by=user.id)
    db_session.add(idea)
    db_session.commit()
    db_session.refresh(idea)

    assert idea.id is not None
    assert idea.status == ProjectIdeaStatus.PENDENTE
    assert idea.author.username == "gestor_model"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/Scripts/python.exe -m pytest tests/test_project_ideas.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.models.project_idea'`

- [ ] **Step 3: Create the model**

Create `backend/app/models/project_idea.py`:

```python
import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProjectIdeaStatus(str, enum.Enum):
    PENDENTE = "pendente"
    APROVADA = "aprovada"
    REJEITADA = "rejeitada"


class ProjectIdea(Base):
    __tablename__ = "project_ideas"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ProjectIdeaStatus] = mapped_column(
        Enum(ProjectIdeaStatus), nullable=False, default=ProjectIdeaStatus.PENDENTE
    )
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    author: Mapped["User"] = relationship(foreign_keys=[created_by])
```

- [ ] **Step 4: Register the model in `app/models/__init__.py`**

Modify `backend/app/models/__init__.py` — add the import and `__all__` entries:

```python
from app.models.github import GithubCommit, GithubPullRequest
from app.models.notification import Notification, NotificationType
from app.models.project import Project, ProjectStatus, ProjectUpdate
from app.models.project_idea import ProjectIdea, ProjectIdeaStatus
from app.models.report import Report, ReportType
```

And add `"ProjectIdea"`, `"ProjectIdeaStatus"` to the `__all__` list (anywhere alongside the other project-related entries).

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && .venv/Scripts/python.exe -m pytest tests/test_project_ideas.py -v`
Expected: PASS

- [ ] **Step 6: Add the new notification types**

Modify `backend/app/models/notification.py` — add two members to `NotificationType`:

```python
class NotificationType(str, enum.Enum):
    TICKET_CREATED = "ticket_created"
    TICKET_UPDATED = "ticket_updated"
    TICKET_COMMENT = "ticket_comment"
    PROJECT_UPDATE = "project_update"
    PROJECT_IDEA_CREATED = "project_idea_created"
    PROJECT_IDEA_STATUS_CHANGED = "project_idea_status_changed"
```

No migration needed for this change — see Global Constraints.

- [ ] **Step 7: Write the migration**

Create `backend/migrations/versions/e8f1c3a9b6d2_add_project_ideas.py`:

```python
"""add project ideas

Revision ID: e8f1c3a9b6d2
Revises: 021788129cb0
Create Date: 2026-08-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8f1c3a9b6d2'
down_revision: Union[str, None] = '021788129cb0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('project_ideas',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=160), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('status', sa.Enum('PENDENTE', 'APROVADA', 'REJEITADA', name='projectideastatus'), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('project_ideas')
```

- [ ] **Step 8: Verify the migration applies cleanly**

Run: `cd backend && .venv/Scripts/python.exe -m alembic upgrade head`
Expected: no errors; last printed line references revision `e8f1c3a9b6d2`.

- [ ] **Step 9: Run the full backend test suite to check for regressions**

Run: `cd backend && .venv/Scripts/python.exe -m pytest -q`
Expected: all tests pass (same count as before plus the one new test)

- [ ] **Step 10: Commit**

```bash
git add backend/app/models/project_idea.py backend/app/models/notification.py backend/app/models/__init__.py backend/migrations/versions/e8f1c3a9b6d2_add_project_ideas.py backend/tests/test_project_ideas.py
git commit -m "feat: add ProjectIdea model, migration, and notification types"
```

---

### Task 2: Schemas and service layer

**Files:**
- Create: `backend/app/schemas/project_idea.py`
- Create: `backend/app/services/project_idea_service.py`
- Modify: `backend/tests/test_project_ideas.py` (append tests)

**Interfaces:**
- Consumes: `ProjectIdea`, `ProjectIdeaStatus` (Task 1), `NotificationType.PROJECT_IDEA_CREATED`/`PROJECT_IDEA_STATUS_CHANGED` (Task 1), `app.services.notification_service.notify_users(db, users, notif_type, title, message, link=None, exclude_user_id=None)`, `app.services.user_service.list_admins(db) -> list[User]`.
- Produces:
  - `ProjectIdeaCreate(title: str, description: str)`, `ProjectIdeaStatusUpdate(status: ProjectIdeaStatus)`, `ProjectIdeaOut` (pydantic, `from_attributes=True`) — consumed by Task 3's router.
  - `create_project_idea(db: DbSession, author_id: int, data: ProjectIdeaCreate) -> ProjectIdea`
  - `list_project_ideas(db: DbSession, current_user: User) -> list[ProjectIdea]`
  - `update_project_idea_status(db: DbSession, idea_id: int, status: ProjectIdeaStatus) -> ProjectIdea`
  - `ProjectIdeaNotFoundError(Exception)`
  — all consumed by Task 3's router.

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_project_ideas.py`:

```python
import pytest

from app.schemas.project_idea import ProjectIdeaCreate
from app.services.notification_service import list_notifications
from app.services.project_idea_service import (
    ProjectIdeaNotFoundError,
    create_project_idea,
    list_project_ideas,
    update_project_idea_status,
)


def test_create_project_idea_notifies_admins(db_session):
    admin = _create_user(db_session, "admin_svc", UserRole.ADMIN)
    author = _create_user(db_session, "operador_svc", UserRole.OPERADOR)

    idea = create_project_idea(
        db_session, author.id, ProjectIdeaCreate(title="Portal do cliente", description="Ideia legal")
    )

    assert idea.status == ProjectIdeaStatus.PENDENTE
    notifications = list_notifications(db_session, admin.id)
    assert len(notifications) == 1
    assert "Portal do cliente" in notifications[0].title


def test_list_project_ideas_scoped_by_role(db_session):
    admin = _create_user(db_session, "admin_svc2", UserRole.ADMIN)
    gestor = _create_user(db_session, "gestor_svc2", UserRole.GESTOR)
    operador = _create_user(db_session, "operador_svc2", UserRole.OPERADOR)

    create_project_idea(db_session, gestor.id, ProjectIdeaCreate(title="Ideia A", description="desc"))
    create_project_idea(db_session, operador.id, ProjectIdeaCreate(title="Ideia B", description="desc"))

    admin_view = list_project_ideas(db_session, admin)
    gestor_view = list_project_ideas(db_session, gestor)

    assert len(admin_view) == 2
    assert len(gestor_view) == 1
    assert gestor_view[0].title == "Ideia A"


def test_update_project_idea_status_notifies_author(db_session):
    _create_user(db_session, "admin_svc3", UserRole.ADMIN)
    author = _create_user(db_session, "gestor_svc3", UserRole.GESTOR)
    idea = create_project_idea(db_session, author.id, ProjectIdeaCreate(title="Ideia C", description="desc"))

    updated = update_project_idea_status(db_session, idea.id, ProjectIdeaStatus.APROVADA)

    assert updated.status == ProjectIdeaStatus.APROVADA
    notifications = list_notifications(db_session, author.id)
    assert any("aprovada" in n.title for n in notifications)


def test_update_nonexistent_idea_raises(db_session):
    with pytest.raises(ProjectIdeaNotFoundError):
        update_project_idea_status(db_session, 9999, ProjectIdeaStatus.REJEITADA)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python.exe -m pytest tests/test_project_ideas.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.schemas.project_idea'`

- [ ] **Step 3: Write the schemas**

Create `backend/app/schemas/project_idea.py`:

```python
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.project_idea import ProjectIdeaStatus
from app.schemas.user import UserOut


class ProjectIdeaCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1)


class ProjectIdeaStatusUpdate(BaseModel):
    status: ProjectIdeaStatus


class ProjectIdeaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: ProjectIdeaStatus
    author: UserOut | None
    created_at: datetime
    updated_at: datetime
```

- [ ] **Step 4: Write the service**

Create `backend/app/services/project_idea_service.py`:

```python
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession, joinedload

from app.models.notification import NotificationType
from app.models.project_idea import ProjectIdea, ProjectIdeaStatus
from app.models.user import User, UserRole
from app.schemas.project_idea import ProjectIdeaCreate
from app.services.notification_service import notify_users
from app.services.user_service import list_admins

STATUS_LABELS_PT = {
    ProjectIdeaStatus.PENDENTE: "pendente",
    ProjectIdeaStatus.APROVADA: "aprovada",
    ProjectIdeaStatus.REJEITADA: "rejeitada",
}


class ProjectIdeaNotFoundError(Exception):
    pass


def _idea_query():
    return select(ProjectIdea).options(joinedload(ProjectIdea.author))


def create_project_idea(db: DbSession, author_id: int, data: ProjectIdeaCreate) -> ProjectIdea:
    idea = ProjectIdea(title=data.title, description=data.description, created_by=author_id)
    db.add(idea)
    db.commit()
    db.refresh(idea)

    admins = list_admins(db)
    notify_users(
        db,
        admins,
        NotificationType.PROJECT_IDEA_CREATED,
        title=f"Nova ideia de projeto: {idea.title}",
        message=f"{idea.author.name if idea.author else 'Alguém'} sugeriu o projeto \"{idea.title}\".",
        link="/project-ideas",
        exclude_user_id=author_id,
    )
    return idea


def list_project_ideas(db: DbSession, current_user: User) -> list[ProjectIdea]:
    query = _idea_query().order_by(ProjectIdea.created_at.desc())
    if current_user.role != UserRole.ADMIN:
        query = query.where(ProjectIdea.created_by == current_user.id)
    return list(db.execute(query).unique().scalars())


def update_project_idea_status(db: DbSession, idea_id: int, status: ProjectIdeaStatus) -> ProjectIdea:
    idea = db.execute(_idea_query().where(ProjectIdea.id == idea_id)).unique().scalar_one_or_none()
    if idea is None:
        raise ProjectIdeaNotFoundError(idea_id)

    idea.status = status
    db.commit()
    db.refresh(idea)

    if idea.author is not None:
        notify_users(
            db,
            [idea.author],
            NotificationType.PROJECT_IDEA_STATUS_CHANGED,
            title=f"Ideia de projeto {STATUS_LABELS_PT[status]}: {idea.title}",
            message=f"Sua ideia \"{idea.title}\" foi marcada como {STATUS_LABELS_PT[status]}.",
            link="/project-ideas",
        )
    return idea
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python.exe -m pytest tests/test_project_ideas.py -v`
Expected: PASS (5 tests total)

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/project_idea.py backend/app/services/project_idea_service.py backend/tests/test_project_ideas.py
git commit -m "feat: add project idea schemas and service layer"
```

---

### Task 3: API router

**Files:**
- Create: `backend/app/api/project_ideas.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_project_ideas.py` (append tests)

**Interfaces:**
- Consumes: `ProjectIdeaCreate`, `ProjectIdeaStatusUpdate`, `ProjectIdeaOut` (Task 2); `create_project_idea`, `list_project_ideas`, `update_project_idea_status`, `ProjectIdeaNotFoundError` (Task 2); `app.security.dependencies.get_current_user`, `require_admin`.
- Produces: `router` (FastAPI `APIRouter`, prefix `/api/project-ideas`) — mounted in `app/main.py`, exposing:
  - `GET /api/project-ideas` → `list[ProjectIdeaOut]`
  - `POST /api/project-ideas` → `ProjectIdeaOut`, 201
  - `PATCH /api/project-ideas/{idea_id}` → `ProjectIdeaOut` (admin only)

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_project_ideas.py`:

```python
def _create_and_login(client, db_session, username, password, role):
    user = create_user(db_session, UserCreate(name=username, username=username, password=password, role=role))
    client.post("/api/auth/login", json={"username": username, "password": password})
    return user


def test_operador_can_submit_idea_via_api(client, db_session):
    _create_and_login(client, db_session, "operador_api", "senha1234", UserRole.OPERADOR)

    response = client.post("/api/project-ideas", json={"title": "App interno", "description": "Facilita o dia a dia"})

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "App interno"
    assert body["status"] == "pendente"
    assert body["author"]["username"] == "operador_api"


def test_non_admin_sees_only_own_ideas_via_api(client, db_session):
    _create_and_login(client, db_session, "gestor_api", "senha1234", UserRole.GESTOR)
    client.post("/api/project-ideas", json={"title": "Ideia do gestor", "description": "desc"})

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "operador_api2", "senha1234", UserRole.OPERADOR)
    client.post("/api/project-ideas", json={"title": "Ideia do operador", "description": "desc"})

    response = client.get("/api/project-ideas")

    assert response.status_code == 200
    titles = [idea["title"] for idea in response.json()]
    assert titles == ["Ideia do operador"]


def test_admin_sees_all_ideas_via_api(client, db_session):
    _create_and_login(client, db_session, "admin_api", "senha1234", UserRole.ADMIN)
    client.post("/api/project-ideas", json={"title": "Ideia 1", "description": "desc"})

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "gestor_api2", "senha1234", UserRole.GESTOR)
    client.post("/api/project-ideas", json={"title": "Ideia 2", "description": "desc"})

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "admin_api", "password": "senha1234"})
    response = client.get("/api/project-ideas")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_non_admin_cannot_change_idea_status(client, db_session):
    _create_and_login(client, db_session, "gestor_api3", "senha1234", UserRole.GESTOR)
    idea_id = client.post("/api/project-ideas", json={"title": "Ideia 3", "description": "desc"}).json()["id"]

    response = client.patch(f"/api/project-ideas/{idea_id}", json={"status": "aprovada"})

    assert response.status_code == 403


def test_admin_approves_idea_and_author_is_notified(client, db_session):
    _create_and_login(client, db_session, "admin_api2", "senha1234", UserRole.ADMIN)

    client.post("/api/auth/logout")
    _create_and_login(client, db_session, "operador_api3", "senha1234", UserRole.OPERADOR)
    idea_id = client.post("/api/project-ideas", json={"title": "Ideia 4", "description": "desc"}).json()["id"]

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "admin_api2", "password": "senha1234"})
    response = client.patch(f"/api/project-ideas/{idea_id}", json={"status": "aprovada"})
    assert response.status_code == 200
    assert response.json()["status"] == "aprovada"

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "operador_api3", "password": "senha1234"})
    titles = [n["title"] for n in client.get("/api/notifications").json()]
    assert any("aprovada" in t for t in titles)


def test_change_status_of_unknown_idea_returns_404(client, db_session):
    _create_and_login(client, db_session, "admin_api3", "senha1234", UserRole.ADMIN)

    response = client.patch("/api/project-ideas/9999", json={"status": "rejeitada"})

    assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python.exe -m pytest tests/test_project_ideas.py -v`
Expected: FAIL with 404s (route not registered) on every new test

- [ ] **Step 3: Write the router**

Create `backend/app/api/project_ideas.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.models.user import User
from app.schemas.project_idea import ProjectIdeaCreate, ProjectIdeaOut, ProjectIdeaStatusUpdate
from app.security.dependencies import get_current_user, require_admin
from app.services.project_idea_service import (
    ProjectIdeaNotFoundError,
    create_project_idea,
    list_project_ideas,
    update_project_idea_status,
)

router = APIRouter(prefix="/api/project-ideas", tags=["project-ideas"])


@router.get("", response_model=list[ProjectIdeaOut])
def get_project_ideas(
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_project_ideas(db, current_user)


@router.post("", response_model=ProjectIdeaOut, status_code=status.HTTP_201_CREATED)
def post_project_idea(
    payload: ProjectIdeaCreate,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_project_idea(db, current_user.id, payload)


@router.patch("/{idea_id}", response_model=ProjectIdeaOut)
def patch_project_idea_status(
    idea_id: int,
    payload: ProjectIdeaStatusUpdate,
    db: DbSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    try:
        return update_project_idea_status(db, idea_id, payload.status)
    except ProjectIdeaNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ideia não encontrada")
```

- [ ] **Step 4: Register the router**

Modify `backend/app/main.py` — add the import next to the other `app.api.*` imports:

```python
from app.api.projects import router as projects_router
from app.api.project_ideas import router as project_ideas_router
from app.api.reports import router as reports_router
```

And add the include next to the other routers:

```python
app.include_router(projects_router)
app.include_router(project_ideas_router)
app.include_router(tickets_router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python.exe -m pytest tests/test_project_ideas.py -v`
Expected: PASS (11 tests total)

- [ ] **Step 6: Run the full backend test suite**

Run: `cd backend && .venv/Scripts/python.exe -m pytest -q`
Expected: all tests pass

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/project_ideas.py backend/app/main.py backend/tests/test_project_ideas.py
git commit -m "feat: add project ideas API endpoints"
```

---

### Task 4: Frontend service module

**Files:**
- Create: `frontend/src/services/projectIdeas.js`

**Interfaces:**
- Consumes: `handleApiResponse` from `frontend/src/utils/apiError.js`.
- Produces: `fetchProjectIdeas() -> Promise<Array>`, `createProjectIdea({title, description}) -> Promise<Object>`, `updateProjectIdeaStatus(ideaId, status) -> Promise<Object>` — consumed by Task 5's page.

- [ ] **Step 1: Write the service module**

Create `frontend/src/services/projectIdeas.js`:

```js
import { handleApiResponse } from "../utils/apiError.js";

const API_BASE_URL = "/api";

export async function fetchProjectIdeas() {
  const response = await fetch(`${API_BASE_URL}/project-ideas`, {
    credentials: "include",
  });
  return handleApiResponse(response);
}

export async function createProjectIdea(data) {
  const response = await fetch(`${API_BASE_URL}/project-ideas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  return handleApiResponse(response);
}

export async function updateProjectIdeaStatus(ideaId, status) {
  const response = await fetch(`${API_BASE_URL}/project-ideas/${ideaId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ status }),
  });
  return handleApiResponse(response);
}
```

- [ ] **Step 2: Verify the module has no syntax errors**

Run: `cd frontend && npx vite build`
Expected: build succeeds (this module isn't imported yet, so this only checks it parses when Task 5 wires it in — for now just confirm no existing build breakage)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/services/projectIdeas.js
git commit -m "feat: add frontend service for project ideas"
```

---

### Task 5: Frontend page, route, nav link, and badge styles

**Files:**
- Create: `frontend/src/pages/ProjectIdeasPage.jsx`
- Modify: `frontend/src/routes/AppRoutes.jsx`
- Modify: `frontend/src/components/NavBar.jsx`
- Modify: `frontend/src/styles/global.css`

**Interfaces:**
- Consumes: `fetchProjectIdeas`, `createProjectIdea`, `updateProjectIdeaStatus` (Task 4); `useAuth()` from `frontend/src/context/AuthContext.jsx` (provides `user.role`, one of `"admin" | "gestor" | "operador"`); existing CSS classes `.page`, `.form`, `.error`, `.page-header`, `.data-table`, `.badge`.
- Produces: `ProjectIdeasPage` default export, mounted at route `/project-ideas`.

- [ ] **Step 1: Add badge styles**

Modify `frontend/src/styles/global.css` — append after the `.badge-priority-urgente` block (around line 479):

```css
.badge-idea-pendente {
  background-color: var(--bg-panel-alt);
  color: var(--text-secondary);
}

.badge-idea-aprovada {
  background-color: #e3f6ea;
  color: #15803d;
}

.badge-idea-rejeitada {
  background-color: #fce9e9;
  color: #b91c1c;
}
```

- [ ] **Step 2: Write the page**

Create `frontend/src/pages/ProjectIdeasPage.jsx`:

```jsx
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "../context/AuthContext.jsx";
import { createProjectIdea, fetchProjectIdeas, updateProjectIdeaStatus } from "../services/projectIdeas.js";

const STATUS_LABELS = {
  pendente: "Pendente",
  aprovada: "Aprovada",
  rejeitada: "Rejeitada",
};

export default function ProjectIdeasPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const queryClient = useQueryClient();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const { data: ideas, isLoading, isError } = useQuery({
    queryKey: ["project-ideas"],
    queryFn: fetchProjectIdeas,
  });

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await createProjectIdea({ title, description });
      setTitle("");
      setDescription("");
      queryClient.invalidateQueries({ queryKey: ["project-ideas"] });
    } catch (err) {
      setError(err.message || "Não foi possível enviar a ideia.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleStatusChange(ideaId, nextStatus) {
    await updateProjectIdeaStatus(ideaId, nextStatus);
    queryClient.invalidateQueries({ queryKey: ["project-ideas"] });
  }

  return (
    <main className="page">
      <h1>Ideias de projeto</h1>

      <form className="form" onSubmit={handleSubmit}>
        <label htmlFor="idea_title">Título</label>
        <input id="idea_title" value={title} onChange={(e) => setTitle(e.target.value)} required autoFocus />

        <label htmlFor="idea_description">Descrição</label>
        <textarea
          id="idea_description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={4}
          required
        />

        {error && <p className="error">{error}</p>}

        <button type="submit" disabled={submitting}>
          {submitting ? "Enviando..." : "Enviar ideia"}
        </button>
      </form>

      <div className="page-header">
        <h2>{isAdmin ? "Todas as ideias" : "Minhas ideias"}</h2>
      </div>

      {isLoading && <p>Carregando ideias...</p>}
      {isError && <p className="error">Não foi possível carregar as ideias.</p>}
      {ideas && ideas.length === 0 && <p>Nenhuma ideia enviada ainda.</p>}

      {ideas && ideas.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Título</th>
              <th>Descrição</th>
              {isAdmin && <th>Autor</th>}
              <th>Status</th>
              {isAdmin && <th>Ações</th>}
            </tr>
          </thead>
          <tbody>
            {ideas.map((idea) => (
              <tr key={idea.id}>
                <td>{idea.title}</td>
                <td>{idea.description}</td>
                {isAdmin && <td>{idea.author ? idea.author.name : "—"}</td>}
                <td>
                  <span className={`badge badge-idea-${idea.status}`}>{STATUS_LABELS[idea.status]}</span>
                </td>
                {isAdmin && (
                  <td>
                    {idea.status === "pendente" && (
                      <>
                        <button type="button" onClick={() => handleStatusChange(idea.id, "aprovada")}>
                          Aprovar
                        </button>{" "}
                        <button type="button" onClick={() => handleStatusChange(idea.id, "rejeitada")}>
                          Rejeitar
                        </button>
                      </>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
```

- [ ] **Step 3: Wire up the route**

Modify `frontend/src/routes/AppRoutes.jsx` — add the import:

```jsx
import ProjectIdeasPage from "../pages/ProjectIdeasPage.jsx";
```

And add the route (any authenticated user, so `ProtectedRoute` not `AdminRoute`) after the `/projects/:projectId` route:

```jsx
      <Route
        path="/project-ideas"
        element={
          <ProtectedRoute>
            <ProjectIdeasPage />
          </ProtectedRoute>
        }
      />
```

- [ ] **Step 4: Add the nav link**

Modify `frontend/src/components/NavBar.jsx` — add a link after "Solicitações", visible to every role:

```jsx
        <Link to="/tickets">Solicitações</Link>
        <Link to="/project-ideas">Ideias</Link>
        <Link to="/reports">Relatórios</Link>
```

- [ ] **Step 5: Build the frontend**

Run: `cd frontend && npm run build`
Expected: build succeeds with no errors

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/ProjectIdeasPage.jsx frontend/src/routes/AppRoutes.jsx frontend/src/components/NavBar.jsx frontend/src/styles/global.css
git commit -m "feat: add project ideas page, route, and nav link"
```

---

### Task 6: End-to-end manual verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full backend test suite**

Run: `cd backend && .venv/Scripts/python.exe -m pytest -q`
Expected: all tests pass, including the 11 new tests in `test_project_ideas.py`

- [ ] **Step 2: Start the app and log in as a non-admin user**

Start the backend (`tray.py` or `run.py`), open the app in a browser, log in as a `gestor` or `operador` account.

- [ ] **Step 3: Submit an idea**

Click "Ideias" in the nav, fill in title + description, submit. Confirm the idea appears in "Minhas ideias" with a "Pendente" badge, and that there is no "Ações" column (non-admin can't approve/reject).

- [ ] **Step 4: Approve as admin**

Log out, log in as `admin`. Open "Ideias" — confirm the submitted idea is visible under "Todas as ideias" with the author's name, and an "Aprovar"/"Rejeitar" pair of buttons. Click "Aprovar". Confirm the badge changes to "Aprovada" and the buttons disappear.

- [ ] **Step 5: Confirm the author was notified**

Log out, log back in as the original non-admin user. Open the notification bell — confirm a notification mentioning "aprovada" and the idea's title is present, and that clicking it links to `/project-ideas`.

- [ ] **Step 6: No commit for this task** — it's verification only; if any step fails, fix the underlying task and re-run its tests before returning here.
