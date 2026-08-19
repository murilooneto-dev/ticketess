# Ticket Finalization + Idea Approval Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let admins finalize completed/canceled tickets into a history view, and close the loop on project ideas — approving one auto-creates a ticket and notifies the author, rejecting one requires a reason and notifies the author, and decided ideas move to a history view.

**Architecture:** Two independent additive features sharing one pattern: a nullable timestamp/field on the existing SQLAlchemy model marks a record as "done", a new/extended service function does the state transition + notification, and the corresponding React page grows an "Ativas/Histórico" (or "Pendentes/Histórico") tab pair reusing the existing `data-table` markup. No new tables, no new pages/routes.

**Tech Stack:** FastAPI + SQLAlchemy + Alembic (backend), React + TanStack Query (frontend), pytest + `TestClient` (backend tests). Backend tests build schema via `Base.metadata.create_all` in `conftest.py`, so they don't depend on the Alembic migrations running — model changes alone make tests pass; migrations matter only for the real dev database.

## Global Constraints

- Portuguese (pt-BR) strings for all user-facing labels, notification titles/messages, and error details — copy the existing files' tone (see `STATUS_LABELS_PT` in `app/services/project_idea_service.py:11`).
- Status-changing endpoints stay admin-only via `require_admin` (see `app/security/dependencies.py:25`).
- Every new backend behavior needs a service-level test (direct function call) and, where it's reachable via HTTP, an API-level test using the `client`/`db_session` fixtures from `backend/tests/conftest.py`.
- Follow existing file conventions exactly: service functions return ORM objects (not schemas), routers translate service exceptions to `HTTPException`, frontend services are thin `fetch` wrappers in `frontend/src/services/*.js` that all funnel through `handleApiResponse`.

---

## Part 1 — Finalize tickets into history

### Task 1: `Ticket.finalized_at` column (model + migration)

**Files:**
- Modify: `backend/app/models/ticket.py:34-51` (add column)
- Create: `backend/migrations/versions/f47ac10b58cc_add_ticket_finalized_at.py`
- Test: `backend/tests/test_tickets.py` (new test at end of file)

**Interfaces:**
- Produces: `Ticket.finalized_at: datetime | None` — nullable column, `NULL` means active/not finalized.

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_tickets.py`:

```python
def test_new_ticket_has_no_finalized_at(client, db_session):
    _create_and_login(client, db_session, "admin_fin", "senha1234", UserRole.ADMIN)
    project = _create_project(db_session)

    response = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket Fin"})

    assert response.status_code == 201
    assert response.json()["finalized_at"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_tickets.py::test_new_ticket_has_no_finalized_at -v`
Expected: FAIL with `KeyError: 'finalized_at'` (field not in response yet).

- [ ] **Step 3: Add the column to the model**

In `backend/app/models/ticket.py`, inside `class Ticket`, right after the `status` column (currently line 46):

```python
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), nullable=False, default=TicketStatus.ABERTO)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

- [ ] **Step 4: Add `finalized_at` to the response schemas**

In `backend/app/schemas/ticket.py`, add the field to `TicketListItemOut` (so `TicketOut` inherits it too), right after `updated_at`:

```python
class TicketListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    type: TicketType
    priority: TicketPriority
    status: TicketStatus
    author: UserOut | None
    created_at: datetime
    updated_at: datetime
    finalized_at: datetime | None
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_tickets.py::test_new_ticket_has_no_finalized_at -v`
Expected: PASS

- [ ] **Step 6: Write the Alembic migration**

Create `backend/migrations/versions/f47ac10b58cc_add_ticket_finalized_at.py`:

```python
"""add ticket finalized_at

Revision ID: f47ac10b58cc
Revises: e8f1c3a9b6d2
Create Date: 2026-08-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f47ac10b58cc'
down_revision: Union[str, None] = 'e8f1c3a9b6d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tickets', sa.Column('finalized_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('tickets', 'finalized_at')
```

- [ ] **Step 7: Run the full ticket test file to check nothing else broke**

Run: `cd backend && python -m pytest tests/test_tickets.py -v`
Expected: all PASS

- [ ] **Step 8: Commit**

```bash
git add backend/app/models/ticket.py backend/app/schemas/ticket.py backend/migrations/versions/f47ac10b58cc_add_ticket_finalized_at.py backend/tests/test_tickets.py
git commit -m "feat: add finalized_at column to tickets"
```

---

### Task 2: Finalize service + `finalized` list filter

**Files:**
- Modify: `backend/app/services/ticket_service.py`
- Test: `backend/tests/test_tickets.py`

**Interfaces:**
- Consumes: `Ticket.finalized_at` (Task 1).
- Produces: `finalize_ticket(db, ticket_id: int) -> Ticket`; `TicketNotFinalizableError` (raised when status isn't `concluido`/`cancelado`); `TicketAlreadyFinalizedError`; `list_tickets(..., finalized: bool = False)` — extends the existing signature with a new keyword-only-by-convention param inserted before the return.

- [ ] **Step 1: Write the failing tests**

Add to `backend/tests/test_tickets.py`:

```python
from app.services.ticket_service import (
    TicketAlreadyFinalizedError,
    TicketNotFinalizableError,
    finalize_ticket,
)


def test_finalize_concluded_ticket_sets_finalized_at(client, db_session):
    admin = _create_and_login(client, db_session, "admin_fin2", "senha1234", UserRole.ADMIN)
    project = _create_project(db_session)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket Fin2"}).json()["id"]
    client.put(f"/api/tickets/{ticket_id}", json={"status": "concluido"})

    ticket = finalize_ticket(db_session, ticket_id)

    assert ticket.finalized_at is not None


def test_finalize_open_ticket_raises(client, db_session):
    admin = _create_and_login(client, db_session, "admin_fin3", "senha1234", UserRole.ADMIN)
    project = _create_project(db_session)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket Fin3"}).json()["id"]

    with pytest.raises(TicketNotFinalizableError):
        finalize_ticket(db_session, ticket_id)


def test_finalize_twice_raises(client, db_session):
    admin = _create_and_login(client, db_session, "admin_fin4", "senha1234", UserRole.ADMIN)
    project = _create_project(db_session)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket Fin4"}).json()["id"]
    client.put(f"/api/tickets/{ticket_id}", json={"status": "cancelado"})
    finalize_ticket(db_session, ticket_id)

    with pytest.raises(TicketAlreadyFinalizedError):
        finalize_ticket(db_session, ticket_id)


def test_list_tickets_excludes_finalized_by_default(db_session):
    from app.services.ticket_service import list_tickets, update_ticket
    from app.schemas.ticket import TicketUpdateIn

    admin = _create_user_direct(db_session)
    project = _create_project(db_session)
    from app.services.ticket_service import create_ticket
    from app.schemas.ticket import TicketCreate

    ticket = create_ticket(db_session, admin.id, TicketCreate(project_id=project.id, title="Ativo"))
    finalized_ticket = create_ticket(db_session, admin.id, TicketCreate(project_id=project.id, title="Encerrado"))
    update_ticket(db_session, finalized_ticket.id, admin.id, TicketUpdateIn(status="concluido"))
    finalize_ticket(db_session, finalized_ticket.id)

    active = list_tickets(db_session)
    history = list_tickets(db_session, finalized=True)

    assert [t.id for t in active] == [ticket.id]
    assert [t.id for t in history] == [finalized_ticket.id]


def _create_user_direct(db_session):
    from app.services.user_service import create_user
    from app.schemas.user import UserCreate

    return create_user(
        db_session, UserCreate(name="Admin Direto", username="admin_fin_direct", password="senha1234", role=UserRole.ADMIN)
    )
```

Add `import pytest` at the top of `backend/tests/test_tickets.py` if not already present (it isn't — check the current imports at the top of the file first).

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_tickets.py -k finalize -v`
Expected: FAIL with `ImportError: cannot import name 'finalize_ticket'`.

- [ ] **Step 3: Implement in `ticket_service.py`**

In `backend/app/services/ticket_service.py`, add two exception classes near the top (after `FileTooLargeError`, currently ending around line 32):

```python
class TicketNotFinalizableError(Exception):
    pass


class TicketAlreadyFinalizedError(Exception):
    pass
```

Change `list_tickets`'s signature and body (currently lines 50-66) to:

```python
def list_tickets(
    db: DbSession,
    project_id: int | None = None,
    mine_user_id: int | None = None,
    status: str | None = None,
    priority: str | None = None,
    finalized: bool = False,
) -> list[Ticket]:
    query = _ticket_query().order_by(Ticket.created_at.desc())
    if project_id is not None:
        query = query.where(Ticket.project_id == project_id)
    if mine_user_id is not None:
        query = query.where(Ticket.created_by == mine_user_id)
    if status is not None:
        query = query.where(Ticket.status == status)
    if priority is not None:
        query = query.where(Ticket.priority == priority)
    if finalized:
        query = query.where(Ticket.finalized_at.is_not(None))
    else:
        query = query.where(Ticket.finalized_at.is_(None))
    return list(db.execute(query).unique().scalars())
```

Add `finalize_ticket` after `update_ticket` (currently ending around line 160):

```python
def finalize_ticket(db: DbSession, ticket_id: int) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError(ticket_id)
    if ticket.status not in (TicketStatus.CONCLUIDO, TicketStatus.CANCELADO):
        raise TicketNotFinalizableError(ticket_id)
    if ticket.finalized_at is not None:
        raise TicketAlreadyFinalizedError(ticket_id)

    from datetime import datetime, timezone

    ticket.finalized_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ticket)
    return ticket
```

Add `TicketStatus` to the existing import from `app.models.ticket` at the top of the file (currently `from app.models.ticket import Ticket, TicketAttachment, TicketComment, TicketHistory`):

```python
from app.models.ticket import Ticket, TicketAttachment, TicketComment, TicketHistory, TicketStatus
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_tickets.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/ticket_service.py backend/tests/test_tickets.py
git commit -m "feat: add finalize_ticket service and finalized ticket list filter"
```

---

### Task 3: `POST /api/tickets/{id}/finalize` endpoint + `finalized` query param

**Files:**
- Modify: `backend/app/api/tickets.py`
- Test: `backend/tests/test_tickets.py`

**Interfaces:**
- Consumes: `finalize_ticket`, `list_tickets(..., finalized=...)`, `TicketNotFinalizableError`, `TicketAlreadyFinalizedError` (Task 2).
- Produces: `POST /api/tickets/{ticket_id}/finalize` → `TicketOut`; `GET /api/tickets?finalized=true` → history list.

- [ ] **Step 1: Write the failing tests**

Add to `backend/tests/test_tickets.py`:

```python
def test_finalize_endpoint_requires_admin(client, db_session):
    _create_and_login(client, db_session, "gestor_fin", "senha1234", UserRole.GESTOR)
    project = _create_project(db_session)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket Fin5"}).json()["id"]

    response = client.post(f"/api/tickets/{ticket_id}/finalize")

    assert response.status_code == 403


def test_finalize_endpoint_rejects_open_ticket(client, db_session):
    _create_and_login(client, db_session, "admin_fin5", "senha1234", UserRole.ADMIN)
    project = _create_project(db_session)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket Fin6"}).json()["id"]

    response = client.post(f"/api/tickets/{ticket_id}/finalize")

    assert response.status_code == 400


def test_finalize_endpoint_moves_ticket_to_history(client, db_session):
    _create_and_login(client, db_session, "admin_fin6", "senha1234", UserRole.ADMIN)
    project = _create_project(db_session)
    ticket_id = client.post("/api/tickets", json={"project_id": project.id, "title": "Ticket Fin7"}).json()["id"]
    client.put(f"/api/tickets/{ticket_id}", json={"status": "concluido"})

    finalize_response = client.post(f"/api/tickets/{ticket_id}/finalize")
    assert finalize_response.status_code == 200
    assert finalize_response.json()["finalized_at"] is not None

    active = client.get("/api/tickets").json()
    history = client.get("/api/tickets?finalized=true").json()
    assert ticket_id not in [t["id"] for t in active]
    assert ticket_id in [t["id"] for t in history]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_tickets.py -k finalize_endpoint -v`
Expected: FAIL with 404 (route doesn't exist yet).

- [ ] **Step 3: Implement the endpoint**

In `backend/app/api/tickets.py`, extend the import from `app.services.ticket_service` (currently lines 19-35) to add `TicketAlreadyFinalizedError`, `TicketNotFinalizableError`, `finalize_ticket`:

```python
from app.services.ticket_service import (
    FileTooLargeError,
    ProjectNotFoundError,
    TicketAlreadyFinalizedError,
    TicketNotFinalizableError,
    TicketNotFoundError,
    add_comment,
    can_view_ticket,
    create_ticket,
    finalize_ticket,
    get_attachment,
    get_ticket,
    list_attachments,
    list_comments,
    list_history,
    list_tickets,
    save_attachment,
    attachment_file_path,
    update_ticket,
)
```

Update `get_tickets` (currently lines 49-63) to accept and forward `finalized`:

```python
@router.get("", response_model=list[TicketListItemOut])
def get_tickets(
    project_id: int | None = Query(default=None),
    mine: bool = Query(default=False),
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    priority: TicketPriority | None = Query(default=None),
    finalized: bool = Query(default=False),
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # operador só enxerga as próprias solicitações, independentemente do filtro "mine"
    if current_user.role == UserRole.OPERADOR:
        mine_user_id = current_user.id
    else:
        mine_user_id = current_user.id if mine else None
    return list_tickets(
        db, project_id=project_id, mine_user_id=mine_user_id, status=status_filter, priority=priority, finalized=finalized
    )
```

Add the new route after `put_ticket` (currently ending around line 101):

```python
@router.post("/{ticket_id}/finalize", response_model=TicketOut)
def post_finalize_ticket(
    ticket_id: int,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        return finalize_ticket(db, ticket_id)
    except TicketNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    except TicketNotFinalizableError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Só é possível finalizar solicitações concluídas ou canceladas",
        )
    except TicketAlreadyFinalizedError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solicitação já finalizada")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_tickets.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/tickets.py backend/tests/test_tickets.py
git commit -m "feat: add finalize ticket endpoint and finalized query param"
```

---

### Task 4: Frontend — finalize action on ticket detail page

**Files:**
- Modify: `frontend/src/services/tickets.js`
- Modify: `frontend/src/pages/TicketDetailPage.jsx`

**Interfaces:**
- Consumes: `POST /api/tickets/{id}/finalize` (Task 3).
- Produces: `finalizeTicket(ticketId)` in `frontend/src/services/tickets.js`.

- [ ] **Step 1: Add the service function**

In `frontend/src/services/tickets.js`, add after `updateTicket` (currently ending at line 43):

```javascript
export async function finalizeTicket(ticketId) {
  const response = await fetch(`${API_BASE_URL}/tickets/${ticketId}/finalize`, {
    method: "POST",
    credentials: "include",
  });
  return handleApiResponse(response);
}
```

- [ ] **Step 2: Wire the button into `TicketDetailPage`**

In `frontend/src/pages/TicketDetailPage.jsx`:

Add `finalizeTicket` to the import from `../services/tickets.js` (currently lines 7-16):

```javascript
import {
  addComment,
  attachmentDownloadUrl,
  fetchAttachments,
  fetchComments,
  fetchHistory,
  fetchTicket,
  finalizeTicket,
  updateTicket,
  uploadAttachment,
} from "../services/tickets.js";
```

Add state and a handler, right after `const [uploading, setUploading] = useState(false);` (line 45):

```javascript
  const [finalizing, setFinalizing] = useState(false);
  const [finalizeError, setFinalizeError] = useState("");

  async function handleFinalize() {
    if (!window.confirm("Finalizar esta solicitação? Ela irá para o histórico e não poderá ser reaberta.")) {
      return;
    }
    setFinalizeError("");
    setFinalizing(true);
    try {
      await finalizeTicket(ticketId);
      invalidateTicket();
    } catch (err) {
      setFinalizeError(err.message || "Não foi possível finalizar a solicitação.");
    } finally {
      setFinalizing(false);
    }
  }
```

Replace the Status field block (currently lines 171-184):

```javascript
        <div>
          <span className="meta">Status</span>
          {isAdmin && !ticket.finalized_at ? (
            <select value={ticket.status} onChange={(e) => handleFieldChange("status", e.target.value)}>
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          ) : (
            <span className={`badge badge-status-${ticket.status}`}>{STATUS_LABELS[ticket.status]}</span>
          )}
        </div>
```

Also make Tipo/Prioridade read-only once finalized: in the Tipo block (lines 141-154) change the condition `isAdmin` to `isAdmin && !ticket.finalized_at`, and same for Prioridade (lines 156-169).

Right after the closing `</div>` of `.ticket-fields` (line 185), add the finalize control:

```javascript
      {isAdmin && !ticket.finalized_at && (ticket.status === "concluido" || ticket.status === "cancelado") && (
        <div className="page-actions">
          <button type="button" onClick={handleFinalize} disabled={finalizing}>
            {finalizing ? "Finalizando..." : "Finalizar"}
          </button>
        </div>
      )}
      {ticket.finalized_at && (
        <p className="meta">Finalizada em {new Date(ticket.finalized_at).toLocaleString("pt-BR")}</p>
      )}
      {finalizeError && <p className="error">{finalizeError}</p>}
```

- [ ] **Step 3: Manual check**

Run the app (`npm run dev` in `frontend/`, backend running), open a ticket, set status to "Concluído", confirm the "Finalizar" button appears, click it, confirm the badge "Finalizada em ..." replaces the button and the status select becomes read-only.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/services/tickets.js frontend/src/pages/TicketDetailPage.jsx
git commit -m "feat: add finalize action to ticket detail page"
```

---

### Task 5: Frontend — Ativas/Histórico tabs on `TicketsPage`

**Files:**
- Modify: `frontend/src/pages/TicketsPage.jsx`
- Modify: `frontend/src/services/tickets.js`
- Modify: `frontend/src/styles/global.css`

**Interfaces:**
- Consumes: `fetchTickets({ finalized })` extended below; `GET /api/tickets?finalized=true` (Task 3).

- [ ] **Step 1: Extend `fetchTickets` to accept `finalized`**

In `frontend/src/services/tickets.js`, replace `fetchTickets` (currently lines 5-16):

```javascript
export async function fetchTickets({ mine = false, projectId, status, priority, finalized = false } = {}) {
  const params = new URLSearchParams();
  if (mine) params.set("mine", "true");
  if (projectId) params.set("project_id", projectId);
  if (status) params.set("status", status);
  if (priority) params.set("priority", priority);
  if (finalized) params.set("finalized", "true");

  const response = await fetch(`${API_BASE_URL}/tickets?${params.toString()}`, {
    credentials: "include",
  });
  return handleApiResponse(response);
}
```

- [ ] **Step 2: Add tabs to `TicketsPage`**

In `frontend/src/pages/TicketsPage.jsx`, add tab state right after `const [priority, setPriority] = useState("");` (line 14):

```javascript
  const [tab, setTab] = useState("ativas");
```

Change the query (currently lines 16-19):

```javascript
  const { data: tickets, isLoading, isError } = useQuery({
    queryKey: ["tickets", onlyMine, status, priority, tab],
    queryFn: () =>
      fetchTickets({ mine: onlyMine, status: status || undefined, priority: priority || undefined, finalized: tab === "historico" }),
  });
```

Add the tab buttons right after the opening `<div className="page-header">` and before `<h1>Solicitações</h1>` — replace the header block (currently lines 22-52) with:

```javascript
      <div className="page-header">
        <h1>Solicitações</h1>
        <div className="page-actions">
          {!isOperador && (
            <label className="checkbox-label">
              <input type="checkbox" checked={onlyMine} onChange={(e) => setOnlyMine(e.target.checked)} />
              Ver apenas minhas solicitações
            </label>
          )}
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">Todos os status</option>
            {Object.entries(STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <select value={priority} onChange={(e) => setPriority(e.target.value)}>
            <option value="">Todas as prioridades</option>
            {Object.entries(PRIORITY_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          {tab === "ativas" && (
            <Link className="button-link" to="/tickets/new">
              Nova solicitação
            </Link>
          )}
        </div>
      </div>

      <div className="tabs">
        <button
          type="button"
          className={`tab-button ${tab === "ativas" ? "active" : ""}`}
          onClick={() => setTab("ativas")}
        >
          Ativas
        </button>
        <button
          type="button"
          className={`tab-button ${tab === "historico" ? "active" : ""}`}
          onClick={() => setTab("historico")}
        >
          Histórico
        </button>
      </div>
```

- [ ] **Step 3: Add tab CSS**

In `frontend/src/styles/global.css`, add after the `.danger-button` rule (find it around line 362, add right after its closing `}`):

```css
.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid var(--border);
}

.tab-button {
  background: none;
  color: var(--text-secondary);
  border-radius: 0;
  padding: 0.6rem 1rem;
  border-bottom: 2px solid transparent;
}

.tab-button:hover {
  background: none;
  color: var(--text-primary);
}

.tab-button.active {
  color: var(--brand-blue);
  border-bottom-color: var(--brand-blue);
}
```

- [ ] **Step 4: Manual check**

Run the app, open Solicitações, finalize a ticket (Task 4), confirm it disappears from "Ativas" and shows up under "Histórico", and that "Nova solicitação" is hidden on the Histórico tab.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/TicketsPage.jsx frontend/src/services/tickets.js frontend/src/styles/global.css
git commit -m "feat: add Ativas/Histórico tabs to tickets list"
```

---

## Part 2 — Idea approval creates a ticket, rejection requires a reason

### Task 6: `ProjectIdea.project_id` + `rejection_reason` (model + migration)

**Files:**
- Modify: `backend/app/models/project_idea.py`
- Create: `backend/migrations/versions/b2d9e6a1c4f7_add_idea_project_and_rejection_reason.py`
- Test: `backend/tests/test_project_ideas.py`

**Interfaces:**
- Produces: `ProjectIdea.project_id: int | None` (FK `projects.id`, `ondelete="SET NULL"`), `ProjectIdea.rejection_reason: str | None`, `ProjectIdea.project: Project | None` relationship.

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_project_ideas.py`:

```python
def test_project_idea_model_persists_project_and_rejection_reason(db_session):
    from app.models.project import Project

    user = _create_user(db_session, "gestor_proj_field", UserRole.GESTOR)
    project = Project(name="Projeto X")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    idea = ProjectIdea(
        title="Ideia com projeto",
        description="desc",
        created_by=user.id,
        project_id=project.id,
        rejection_reason="Fora do escopo atual",
    )
    db_session.add(idea)
    db_session.commit()
    db_session.refresh(idea)

    assert idea.project_id == project.id
    assert idea.project.name == "Projeto X"
    assert idea.rejection_reason == "Fora do escopo atual"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_project_ideas.py::test_project_idea_model_persists_project_and_rejection_reason -v`
Expected: FAIL with `TypeError: 'project_id' is an invalid keyword argument for ProjectIdea`.

- [ ] **Step 3: Add the columns and relationship**

In `backend/app/models/project_idea.py`, add the `ForeignKey` import is already present; update the class body (currently lines 16-31):

```python
class ProjectIdea(Base):
    __tablename__ = "project_ideas"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ProjectIdeaStatus] = mapped_column(
        Enum(ProjectIdeaStatus), nullable=False, default=ProjectIdeaStatus.PENDENTE
    )
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    author: Mapped["User"] = relationship(foreign_keys=[created_by])
    project: Mapped["Project | None"] = relationship()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_project_ideas.py::test_project_idea_model_persists_project_and_rejection_reason -v`
Expected: PASS

- [ ] **Step 5: Write the Alembic migration**

Create `backend/migrations/versions/b2d9e6a1c4f7_add_idea_project_and_rejection_reason.py`:

```python
"""add idea project and rejection reason

Revision ID: b2d9e6a1c4f7
Revises: f47ac10b58cc
Create Date: 2026-08-19 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2d9e6a1c4f7'
down_revision: Union[str, None] = 'f47ac10b58cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('project_ideas', sa.Column('project_id', sa.Integer(), nullable=True))
    op.add_column('project_ideas', sa.Column('rejection_reason', sa.Text(), nullable=True))
    op.create_foreign_key(
        'fk_project_ideas_project_id_projects',
        'project_ideas', 'projects',
        ['project_id'], ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_project_ideas_project_id_projects', 'project_ideas', type_='foreignkey')
    op.drop_column('project_ideas', 'rejection_reason')
    op.drop_column('project_ideas', 'project_id')
```

- [ ] **Step 6: Run the full idea test file to check nothing else broke**

Run: `cd backend && python -m pytest tests/test_project_ideas.py -v`
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/project_idea.py backend/migrations/versions/b2d9e6a1c4f7_add_idea_project_and_rejection_reason.py backend/tests/test_project_ideas.py
git commit -m "feat: add project_id and rejection_reason columns to project_ideas"
```

---

### Task 7: Idea schemas + require `project_id` on creation

**Files:**
- Modify: `backend/app/schemas/project_idea.py`
- Modify: `backend/app/services/project_idea_service.py`
- Modify: `backend/app/api/project_ideas.py`
- Test: `backend/tests/test_project_ideas.py` (update existing creation tests)

**Interfaces:**
- Consumes: `ProjectIdea.project_id`, `.project`, `.rejection_reason` (Task 6).
- Produces: `ProjectIdeaCreate.project_id: int` (required); `ProjectIdeaOut.project: ProjectIdeaProjectOut | None`, `.rejection_reason: str | None`; `create_project_idea(db, author_id, data)` now sets `project_id` and raises `ProjectNotFoundError` if invalid.

- [ ] **Step 1: Update the schemas**

Replace `backend/app/schemas/project_idea.py` in full:

```python
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.project_idea import ProjectIdeaStatus
from app.schemas.user import UserOut


class ProjectIdeaCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1)
    project_id: int


class ProjectIdeaStatusUpdate(BaseModel):
    status: ProjectIdeaStatus
    project_id: int | None = None
    rejection_reason: str | None = None


class ProjectIdeaProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ProjectIdeaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: ProjectIdeaStatus
    author: UserOut | None
    project: ProjectIdeaProjectOut | None
    rejection_reason: str | None
    created_at: datetime
    updated_at: datetime
```

- [ ] **Step 2: Write the failing test for required `project_id` on create**

Update `backend/tests/test_project_ideas.py`: every existing call that does `create_project_idea(db_session, <author>.id, ProjectIdeaCreate(title=..., description=...))` or posts to `POST /api/project-ideas` without `project_id` needs a project. Add this helper near the top, right after `_create_user`:

```python
def _create_project(db_session, name="Projeto Teste"):
    from app.models.project import Project

    project = Project(name=name)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project
```

Then update every `ProjectIdeaCreate(...)` call in the file to include `project_id=project.id` (creating a `project = _create_project(db_session)` first in each test that doesn't already have a project in scope), and every `client.post("/api/project-ideas", json={...})` call to include `"project_id": project.id`. For example, `test_project_idea_model_persists_with_default_status` stays as-is (it builds the ORM object directly, not through the schema, so it's unaffected). `test_create_project_idea_notifies_admins` becomes:

```python
def test_create_project_idea_notifies_admins(db_session):
    admin = _create_user(db_session, "admin_svc", UserRole.ADMIN)
    author = _create_user(db_session, "operador_svc", UserRole.OPERADOR)
    project = _create_project(db_session)

    idea = create_project_idea(
        db_session, author.id, ProjectIdeaCreate(title="Portal do cliente", description="Ideia legal", project_id=project.id)
    )

    assert idea.status == ProjectIdeaStatus.PENDENTE
    notifications = list_notifications(db_session, admin.id)
    assert len(notifications) == 1
    assert "Portal do cliente" in notifications[0].title
```

Apply the same pattern (add `project = _create_project(db_session)`, pass `project_id=project.id` to every `ProjectIdeaCreate`, add `"project_id": project.id` to every JSON payload posted to `/api/project-ideas`) to: `test_list_project_ideas_scoped_by_role`, `test_update_project_idea_status_notifies_author`, `test_repeated_status_update_does_not_duplicate_notification`, `test_admin_approving_own_idea_does_not_self_notify`, `test_operador_can_submit_idea_via_api`, `test_non_admin_sees_only_own_ideas_via_api`, `test_admin_sees_all_ideas_via_api`, `test_non_admin_cannot_change_idea_status`, `test_admin_approves_idea_and_author_is_notified`.

Also add a new test for the validation itself:

```python
def test_create_idea_with_invalid_project_fails(client, db_session):
    _create_and_login(client, db_session, "gestor_badproj", "senha1234", UserRole.GESTOR)

    response = client.post("/api/project-ideas", json={"title": "Ideia", "description": "desc", "project_id": 9999})

    assert response.status_code == 400
```

- [ ] **Step 3: Run tests to verify the new/changed ones fail**

Run: `cd backend && python -m pytest tests/test_project_ideas.py -v`
Expected: FAIL — `project_id` missing (422) on the untouched calls, and `test_create_idea_with_invalid_project_fails` fails because `create_project_idea` doesn't validate the project yet.

- [ ] **Step 4: Update `create_project_idea` to require and validate the project**

In `backend/app/services/project_idea_service.py`, add `ProjectNotFoundError` and use it; update the imports and `create_project_idea` (currently lines 1-42):

```python
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession, joinedload

from app.models.notification import NotificationType
from app.models.project import Project
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


class ProjectNotFoundError(Exception):
    pass


def _idea_query():
    return select(ProjectIdea).options(joinedload(ProjectIdea.author), joinedload(ProjectIdea.project))


def create_project_idea(db: DbSession, author_id: int, data: ProjectIdeaCreate) -> ProjectIdea:
    if db.get(Project, data.project_id) is None:
        raise ProjectNotFoundError(data.project_id)

    idea = ProjectIdea(title=data.title, description=data.description, created_by=author_id, project_id=data.project_id)
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
```

(Leave `update_project_idea_status` untouched for now — Tasks 8 and 9 rewrite it.)

- [ ] **Step 5: Wire `ProjectNotFoundError` in the router**

In `backend/app/api/project_ideas.py`, update the import and `post_project_idea`:

```python
from app.services.project_idea_service import (
    ProjectIdeaNotFoundError,
    ProjectNotFoundError,
    create_project_idea,
    list_project_ideas,
    update_project_idea_status,
)
```

```python
@router.post("", response_model=ProjectIdeaOut, status_code=status.HTTP_201_CREATED)
def post_project_idea(
    payload: ProjectIdeaCreate,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return create_project_idea(db, current_user.id, payload)
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Projeto informado não existe")
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_project_ideas.py -v`
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/project_idea.py backend/app/services/project_idea_service.py backend/app/api/project_ideas.py backend/tests/test_project_ideas.py
git commit -m "feat: require project_id when submitting a project idea"
```

---

### Task 8: Approving an idea creates a ticket and notifies the author

**Files:**
- Modify: `backend/app/services/project_idea_service.py`
- Modify: `backend/app/api/project_ideas.py`
- Test: `backend/tests/test_project_ideas.py`

**Interfaces:**
- Consumes: `ticket_service.create_ticket(db, author_id, TicketCreate)` (existing, `backend/app/services/ticket_service.py:74`), `ticket_service.ProjectNotFoundError` (existing).
- Produces: `update_project_idea_status(db, idea_id, status, actor_id, project_id=None, rejection_reason=None)`; `ProjectIdeaMissingProjectError`.

- [ ] **Step 1: Write the failing tests**

Add to `backend/tests/test_project_ideas.py`:

```python
def test_approving_idea_creates_ticket_and_notifies_author(db_session):
    admin = _create_user(db_session, "admin_approve1", UserRole.ADMIN)
    author = _create_user(db_session, "gestor_approve1", UserRole.GESTOR)
    project = _create_project(db_session)
    idea = create_project_idea(
        db_session, author.id, ProjectIdeaCreate(title="Ideia F", description="Descrição F", project_id=project.id)
    )

    updated = update_project_idea_status(db_session, idea.id, ProjectIdeaStatus.APROVADA, admin.id)

    from app.models.ticket import Ticket

    tickets = db_session.query(Ticket).filter(Ticket.project_id == project.id).all()
    assert len(tickets) == 1
    assert tickets[0].title == "Ideia F"
    assert tickets[0].description == "Descrição F"
    assert tickets[0].created_by == author.id

    notifications = list_notifications(db_session, author.id)
    approved_notifications = [n for n in notifications if "Ideia aprovada" in n.title]
    assert len(approved_notifications) == 1
    assert approved_notifications[0].link == f"/tickets/{tickets[0].id}"


def test_approving_idea_without_project_requires_project_id(db_session):
    from app.models.project_idea import ProjectIdea

    admin = _create_user(db_session, "admin_approve2", UserRole.ADMIN)
    author = _create_user(db_session, "gestor_approve2", UserRole.GESTOR)
    idea = ProjectIdea(title="Ideia legada", description="desc", created_by=author.id)
    db_session.add(idea)
    db_session.commit()
    db_session.refresh(idea)

    with pytest.raises(ProjectIdeaMissingProjectError):
        update_project_idea_status(db_session, idea.id, ProjectIdeaStatus.APROVADA, admin.id)


def test_approving_legacy_idea_with_supplied_project_id_succeeds(db_session):
    from app.models.project_idea import ProjectIdea

    admin = _create_user(db_session, "admin_approve3", UserRole.ADMIN)
    author = _create_user(db_session, "gestor_approve3", UserRole.GESTOR)
    project = _create_project(db_session)
    idea = ProjectIdea(title="Ideia legada 2", description="desc", created_by=author.id)
    db_session.add(idea)
    db_session.commit()
    db_session.refresh(idea)

    updated = update_project_idea_status(
        db_session, idea.id, ProjectIdeaStatus.APROVADA, admin.id, project_id=project.id
    )

    assert updated.project_id == project.id
```

Add the new imports at the top of the test file:

```python
from app.services.project_idea_service import (
    ProjectIdeaMissingProjectError,
    ProjectIdeaNotFoundError,
    create_project_idea,
    list_project_ideas,
    update_project_idea_status,
)
```

(replace the existing `from app.services.project_idea_service import (...)` block with this one).

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_project_ideas.py -k approve -v`
Expected: FAIL with `ImportError: cannot import name 'ProjectIdeaMissingProjectError'`.

- [ ] **Step 3: Rewrite `update_project_idea_status`**

In `backend/app/services/project_idea_service.py`, add the new exception and rewrite the function (this replaces the current `update_project_idea_status`, lines 52-75 of the original file):

```python
class ProjectIdeaMissingProjectError(Exception):
    pass


class ProjectIdeaRejectionReasonRequiredError(Exception):
    pass


def update_project_idea_status(
    db: DbSession,
    idea_id: int,
    status: ProjectIdeaStatus,
    actor_id: int,
    project_id: int | None = None,
    rejection_reason: str | None = None,
) -> ProjectIdea:
    idea = db.execute(_idea_query().where(ProjectIdea.id == idea_id)).unique().scalar_one_or_none()
    if idea is None:
        raise ProjectIdeaNotFoundError(idea_id)

    previous_status = idea.status
    if previous_status == status:
        return idea

    created_ticket = None
    if status == ProjectIdeaStatus.APROVADA:
        from app.schemas.ticket import TicketCreate
        from app.services.ticket_service import create_ticket

        resolved_project_id = idea.project_id or project_id
        if resolved_project_id is None:
            raise ProjectIdeaMissingProjectError(idea_id)
        idea.project_id = resolved_project_id
        created_ticket = create_ticket(
            db,
            idea.created_by,
            TicketCreate(project_id=resolved_project_id, title=idea.title, description=idea.description),
        )
    elif status == ProjectIdeaStatus.REJEITADA:
        if not rejection_reason or not rejection_reason.strip():
            raise ProjectIdeaRejectionReasonRequiredError(idea_id)
        idea.rejection_reason = rejection_reason.strip()

    idea.status = status
    db.commit()
    db.refresh(idea)

    if idea.author is not None:
        if status == ProjectIdeaStatus.APROVADA and created_ticket is not None:
            notify_users(
                db,
                [idea.author],
                NotificationType.PROJECT_IDEA_STATUS_CHANGED,
                title=f"Ideia aprovada: {idea.title}",
                message=f"Sua ideia \"{idea.title}\" foi aprovada e virou a solicitação \"{created_ticket.title}\".",
                link=f"/tickets/{created_ticket.id}",
                exclude_user_id=actor_id,
            )
        elif status == ProjectIdeaStatus.REJEITADA:
            notify_users(
                db,
                [idea.author],
                NotificationType.PROJECT_IDEA_STATUS_CHANGED,
                title=f"Ideia rejeitada: {idea.title}",
                message=f"Sua ideia \"{idea.title}\" foi rejeitada: {idea.rejection_reason}.",
                link="/project-ideas",
                exclude_user_id=actor_id,
            )
    return idea
```

Note: `test_update_project_idea_status_notifies_author` (existing test, already updated in Task 7 to pass `project_id`) now exercises this new path — it should still pass since it approves an idea that already has a `project_id` set at creation.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_project_ideas.py -v`
Expected: all PASS

- [ ] **Step 5: Wire `ProjectIdeaMissingProjectError` in the router**

In `backend/app/api/project_ideas.py`, update the import list to add `ProjectIdeaMissingProjectError`, and update `patch_project_idea_status` to pass through `project_id`/`rejection_reason` and translate the new error:

```python
from app.services.project_idea_service import (
    ProjectIdeaMissingProjectError,
    ProjectIdeaNotFoundError,
    ProjectNotFoundError,
    create_project_idea,
    list_project_ideas,
    update_project_idea_status,
)
```

```python
@router.patch("/{idea_id}", response_model=ProjectIdeaOut)
def patch_project_idea_status(
    idea_id: int,
    payload: ProjectIdeaStatusUpdate,
    db: DbSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        return update_project_idea_status(
            db,
            idea_id,
            payload.status,
            current_user.id,
            project_id=payload.project_id,
            rejection_reason=payload.rejection_reason,
        )
    except ProjectIdeaNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ideia não encontrada")
    except ProjectIdeaMissingProjectError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Selecione um projeto para aprovar esta ideia"
        )
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Projeto informado não existe")
```

(`ProjectIdeaRejectionReasonRequiredError` is wired in Task 9, together with its tests.)

- [ ] **Step 6: Run the full test file once more**

Run: `cd backend && python -m pytest tests/test_project_ideas.py -v`
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/project_idea_service.py backend/app/api/project_ideas.py backend/tests/test_project_ideas.py
git commit -m "feat: approving a project idea auto-creates a ticket and notifies the author"
```

---

### Task 9: Rejecting an idea requires a reason and notifies the author

**Files:**
- Modify: `backend/app/api/project_ideas.py`
- Test: `backend/tests/test_project_ideas.py`

**Interfaces:**
- Consumes: `ProjectIdeaRejectionReasonRequiredError`, `update_project_idea_status(..., rejection_reason=...)` (Task 8).

- [ ] **Step 1: Write the failing tests**

Add to `backend/tests/test_project_ideas.py`:

```python
def test_rejecting_idea_without_reason_raises(db_session):
    admin = _create_user(db_session, "admin_reject1", UserRole.ADMIN)
    author = _create_user(db_session, "gestor_reject1", UserRole.GESTOR)
    project = _create_project(db_session)
    idea = create_project_idea(
        db_session, author.id, ProjectIdeaCreate(title="Ideia G", description="desc", project_id=project.id)
    )

    with pytest.raises(ProjectIdeaRejectionReasonRequiredError):
        update_project_idea_status(db_session, idea.id, ProjectIdeaStatus.REJEITADA, admin.id)


def test_rejecting_idea_with_reason_notifies_author(db_session):
    admin = _create_user(db_session, "admin_reject2", UserRole.ADMIN)
    author = _create_user(db_session, "gestor_reject2", UserRole.GESTOR)
    project = _create_project(db_session)
    idea = create_project_idea(
        db_session, author.id, ProjectIdeaCreate(title="Ideia H", description="desc", project_id=project.id)
    )

    updated = update_project_idea_status(
        db_session, idea.id, ProjectIdeaStatus.REJEITADA, admin.id, rejection_reason="Fora do orçamento deste trimestre"
    )

    assert updated.rejection_reason == "Fora do orçamento deste trimestre"
    notifications = list_notifications(db_session, author.id)
    rejected = [n for n in notifications if "Ideia rejeitada" in n.title]
    assert len(rejected) == 1
    assert "Fora do orçamento deste trimestre" in rejected[0].message


def test_reject_endpoint_requires_reason(client, db_session):
    _create_and_login(client, db_session, "admin_reject3", "senha1234", UserRole.ADMIN)
    project = _create_project(db_session)
    idea_id = client.post(
        "/api/project-ideas", json={"title": "Ideia I", "description": "desc", "project_id": project.id}
    ).json()["id"]

    response = client.patch(f"/api/project-ideas/{idea_id}", json={"status": "rejeitada"})

    assert response.status_code == 400


def test_reject_endpoint_with_reason_succeeds(client, db_session):
    _create_and_login(client, db_session, "admin_reject4", "senha1234", UserRole.ADMIN)
    project = _create_project(db_session)
    idea_id = client.post(
        "/api/project-ideas", json={"title": "Ideia J", "description": "desc", "project_id": project.id}
    ).json()["id"]

    response = client.patch(
        f"/api/project-ideas/{idea_id}", json={"status": "rejeitada", "rejection_reason": "Duplicada"}
    )

    assert response.status_code == 200
    assert response.json()["rejection_reason"] == "Duplicada"
```

Add `ProjectIdeaRejectionReasonRequiredError` to the existing service import block at the top of the test file.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_project_ideas.py -k reject -v`
Expected: `test_rejecting_idea_without_reason_raises` and the two service-level tests PASS already (Task 8 implemented the raising logic); `test_reject_endpoint_requires_reason` FAILs because the router doesn't translate `ProjectIdeaRejectionReasonRequiredError` yet (currently an unhandled 500).

- [ ] **Step 3: Wire the error in the router**

In `backend/app/api/project_ideas.py`, add `ProjectIdeaRejectionReasonRequiredError` to the import and to the `except` chain in `patch_project_idea_status`:

```python
from app.services.project_idea_service import (
    ProjectIdeaMissingProjectError,
    ProjectIdeaNotFoundError,
    ProjectIdeaRejectionReasonRequiredError,
    ProjectNotFoundError,
    create_project_idea,
    list_project_ideas,
    update_project_idea_status,
)
```

```python
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Projeto informado não existe")
    except ProjectIdeaRejectionReasonRequiredError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe o motivo da rejeição")
```

(append this last `except` clause after the existing ones from Task 8).

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_project_ideas.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/project_ideas.py backend/tests/test_project_ideas.py
git commit -m "feat: require a reason when rejecting a project idea"
```

---

### Task 10: Frontend — idea service + project selector on idea creation

**Files:**
- Modify: `frontend/src/services/projectIdeas.js`
- Modify: `frontend/src/pages/ProjectIdeasPage.jsx`

**Interfaces:**
- Consumes: `POST /api/project-ideas` now requires `project_id`; `PATCH /api/project-ideas/{id}` now accepts `project_id`/`rejection_reason` (Tasks 7-9); `fetchProjects()` (existing, `frontend/src/services/projects.js:5`).
- Produces: `updateProjectIdeaStatus(ideaId, { status, project_id, rejection_reason })` — signature changes from `(ideaId, status)` to `(ideaId, payload)`.

This task only updates the create form and the service signature; Task 11 builds the approve/reject dialogs and history tab that use the new fields.

- [ ] **Step 1: Update `frontend/src/services/projectIdeas.js`**

Replace `createProjectIdea` is unchanged in shape (it already forwards whatever `data` it's given — no edit needed there). Replace `updateProjectIdeaStatus`:

```javascript
export async function updateProjectIdeaStatus(ideaId, payload) {
  const response = await fetch(`${API_BASE_URL}/project-ideas/${ideaId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  });
  return handleApiResponse(response);
}
```

- [ ] **Step 2: Add the project selector to the creation form**

In `frontend/src/pages/ProjectIdeasPage.jsx`, add the imports:

```javascript
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "../context/AuthContext.jsx";
import { fetchProjects } from "../services/projects.js";
import { createProjectIdea, fetchProjectIdeas, updateProjectIdeaStatus } from "../services/projectIdeas.js";
```

(replace the current `import { useQuery, useQueryClient } from "@tanstack/react-query";` + service import block, lines 2-5, with the above).

Add `projectId` state right after `const [description, setDescription] = useState("");` (line 19):

```javascript
  const [projectId, setProjectId] = useState("");
```

Add the projects query right after the `ideas` query (currently lines 24-27):

```javascript
  const { data: projects } = useQuery({ queryKey: ["projects"], queryFn: () => fetchProjects() });
```

Update `handleSubmit` (currently lines 29-43) to send `project_id` and reset it:

```javascript
  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await createProjectIdea({ title, description, project_id: Number(projectId) });
      setTitle("");
      setDescription("");
      setProjectId("");
      queryClient.invalidateQueries({ queryKey: ["project-ideas"] });
    } catch (err) {
      setError(err.message || "Não foi possível enviar a ideia.");
    } finally {
      setSubmitting(false);
    }
  }
```

Add the `<select>` to the form, right after the title field and before the description label (currently lines 63-65, between the title `<input>` and the description `<label>`):

```javascript
        <label htmlFor="idea_project">Projeto</label>
        <select id="idea_project" value={projectId} onChange={(e) => setProjectId(e.target.value)} required>
          <option value="" disabled>
            Selecione um projeto
          </option>
          {projects?.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
```

Update the submit button's `disabled` prop (currently line 77-79) to also require a project:

```javascript
        <button type="submit" disabled={submitting || !projectId}>
          {submitting ? "Enviando..." : "Enviar ideia"}
        </button>
```

- [ ] **Step 3: Manual check**

Run the app, open "Ideias de projeto", confirm the new project `<select>` appears and is required, submit an idea, confirm it's created with the chosen project.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/services/projectIdeas.js frontend/src/pages/ProjectIdeasPage.jsx
git commit -m "feat: require project selection when submitting a project idea"
```

---

### Task 11: Frontend — approve/reject dialogs + Pendentes/Histórico tabs

**Files:**
- Modify: `frontend/src/pages/ProjectIdeasPage.jsx`

**Interfaces:**
- Consumes: `updateProjectIdeaStatus(ideaId, { status, project_id, rejection_reason })` (Task 10); idea objects now carry `.project` (`{id, name} | null`) and `.rejection_reason` (Task 7).

This is the final task and produces the full user-facing flow described in the spec: an inline reason field on reject, an inline project picker on approve when the idea has none, and a Pendentes/Histórico tab split.

- [ ] **Step 1: Replace `ProjectIdeasPage.jsx` in full**

```javascript
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "../context/AuthContext.jsx";
import { fetchProjects } from "../services/projects.js";
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
  const [projectId, setProjectId] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [tab, setTab] = useState("pendentes");
  const [pendingIdeaId, setPendingIdeaId] = useState(null);
  const [actionIdeaId, setActionIdeaId] = useState(null);
  const [actionType, setActionType] = useState(null); // "aprovar" | "rejeitar"
  const [actionProjectId, setActionProjectId] = useState("");
  const [actionReason, setActionReason] = useState("");
  const [actionError, setActionError] = useState("");

  const { data: ideas, isLoading, isError } = useQuery({
    queryKey: ["project-ideas"],
    queryFn: fetchProjectIdeas,
  });

  const { data: projects } = useQuery({ queryKey: ["projects"], queryFn: () => fetchProjects() });

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await createProjectIdea({ title, description, project_id: Number(projectId) });
      setTitle("");
      setDescription("");
      setProjectId("");
      queryClient.invalidateQueries({ queryKey: ["project-ideas"] });
    } catch (err) {
      setError(err.message || "Não foi possível enviar a ideia.");
    } finally {
      setSubmitting(false);
    }
  }

  function openAction(idea, type) {
    setActionIdeaId(idea.id);
    setActionType(type);
    setActionProjectId(idea.project ? String(idea.project.id) : "");
    setActionReason("");
    setActionError("");
  }

  function cancelAction() {
    setActionIdeaId(null);
    setActionType(null);
    setActionError("");
  }

  async function confirmAction(idea) {
    setActionError("");
    const payload = { status: actionType === "aprovar" ? "aprovada" : "rejeitada" };
    if (actionType === "aprovar" && !idea.project) {
      if (!actionProjectId) {
        setActionError("Selecione um projeto.");
        return;
      }
      payload.project_id = Number(actionProjectId);
    }
    if (actionType === "rejeitar") {
      if (!actionReason.trim()) {
        setActionError("Informe o motivo da rejeição.");
        return;
      }
      payload.rejection_reason = actionReason.trim();
    }

    setPendingIdeaId(idea.id);
    try {
      await updateProjectIdeaStatus(idea.id, payload);
      queryClient.invalidateQueries({ queryKey: ["project-ideas"] });
      cancelAction();
    } catch (err) {
      setActionError(err.message || "Não foi possível atualizar o status da ideia.");
    } finally {
      setPendingIdeaId(null);
    }
  }

  const pendentes = ideas?.filter((idea) => idea.status === "pendente") ?? [];
  const historico = ideas?.filter((idea) => idea.status !== "pendente") ?? [];
  const visibleIdeas = tab === "pendentes" ? pendentes : historico;

  return (
    <main className="page">
      <h1>Ideias de projeto</h1>

      <form className="form" onSubmit={handleSubmit}>
        <label htmlFor="idea_title">Título</label>
        <input id="idea_title" value={title} onChange={(e) => setTitle(e.target.value)} required autoFocus />

        <label htmlFor="idea_project">Projeto</label>
        <select id="idea_project" value={projectId} onChange={(e) => setProjectId(e.target.value)} required>
          <option value="" disabled>
            Selecione um projeto
          </option>
          {projects?.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>

        <label htmlFor="idea_description">Descrição</label>
        <textarea
          id="idea_description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={4}
          required
        />

        {error && <p className="error">{error}</p>}

        <button type="submit" disabled={submitting || !projectId}>
          {submitting ? "Enviando..." : "Enviar ideia"}
        </button>
      </form>

      <div className="page-header">
        <h2>{isAdmin ? "Todas as ideias" : "Minhas ideias"}</h2>
      </div>

      <div className="tabs">
        <button
          type="button"
          className={`tab-button ${tab === "pendentes" ? "active" : ""}`}
          onClick={() => setTab("pendentes")}
        >
          Pendentes
        </button>
        <button
          type="button"
          className={`tab-button ${tab === "historico" ? "active" : ""}`}
          onClick={() => setTab("historico")}
        >
          Histórico
        </button>
      </div>

      {isLoading && <p>Carregando ideias...</p>}
      {isError && <p className="error">Não foi possível carregar as ideias.</p>}
      {ideas && visibleIdeas.length === 0 && <p>Nenhuma ideia encontrada.</p>}

      {ideas && visibleIdeas.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Título</th>
              <th>Descrição</th>
              {isAdmin && <th>Autor</th>}
              <th>Status</th>
              {tab === "historico" && <th>Detalhes</th>}
              {isAdmin && tab === "pendentes" && <th>Ações</th>}
            </tr>
          </thead>
          <tbody>
            {visibleIdeas.map((idea) => (
              <tr key={idea.id}>
                <td>{idea.title}</td>
                <td>{idea.description}</td>
                {isAdmin && <td>{idea.author ? idea.author.name : "—"}</td>}
                <td>
                  <span className={`badge badge-idea-${idea.status}`}>{STATUS_LABELS[idea.status]}</span>
                </td>
                {tab === "historico" && (
                  <td>
                    {idea.status === "aprovada" && idea.project && <span>Projeto: {idea.project.name}</span>}
                    {idea.status === "rejeitada" && idea.rejection_reason && <span>{idea.rejection_reason}</span>}
                  </td>
                )}
                {isAdmin && tab === "pendentes" && (
                  <td>
                    {actionIdeaId !== idea.id && (
                      <>
                        <button type="button" onClick={() => openAction(idea, "aprovar")} disabled={pendingIdeaId === idea.id}>
                          Aprovar
                        </button>{" "}
                        <button type="button" onClick={() => openAction(idea, "rejeitar")} disabled={pendingIdeaId === idea.id}>
                          Rejeitar
                        </button>
                      </>
                    )}
                    {actionIdeaId === idea.id && actionType === "aprovar" && (
                      <div className="form">
                        {!idea.project && (
                          <select value={actionProjectId} onChange={(e) => setActionProjectId(e.target.value)}>
                            <option value="" disabled>
                              Selecione um projeto
                            </option>
                            {projects?.map((project) => (
                              <option key={project.id} value={project.id}>
                                {project.name}
                              </option>
                            ))}
                          </select>
                        )}
                        {actionError && <p className="error">{actionError}</p>}
                        <button type="button" onClick={() => confirmAction(idea)} disabled={pendingIdeaId === idea.id}>
                          Confirmar aprovação
                        </button>{" "}
                        <button type="button" onClick={cancelAction}>
                          Cancelar
                        </button>
                      </div>
                    )}
                    {actionIdeaId === idea.id && actionType === "rejeitar" && (
                      <div className="form">
                        <textarea
                          value={actionReason}
                          onChange={(e) => setActionReason(e.target.value)}
                          rows={2}
                          placeholder="Motivo da rejeição"
                        />
                        {actionError && <p className="error">{actionError}</p>}
                        <button type="button" onClick={() => confirmAction(idea)} disabled={pendingIdeaId === idea.id}>
                          Confirmar rejeição
                        </button>{" "}
                        <button type="button" onClick={cancelAction}>
                          Cancelar
                        </button>
                      </div>
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

- [ ] **Step 2: Manual check**

Run the app (backend + `npm run dev` in `frontend/`):
1. As a non-admin, submit a new idea with a project — confirm it requires a project.
2. As admin, on "Pendentes", click "Aprovar" on an idea that has a project — confirm it moves to "Histórico" and a ticket with the same title/description now exists under that project's tickets.
3. As admin, click "Rejeitar" on another idea, try to confirm without typing a reason — confirm it's blocked; type a reason and confirm — check it moves to "Histórico" showing the reason.
4. Log in as the idea's author, check Notificações shows the approval/rejection message.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/ProjectIdeasPage.jsx
git commit -m "feat: add approve/reject dialogs and Pendentes/Histórico tabs to project ideas"
```

---

## Self-Review Notes

- **Spec coverage:** Part 1 (finalize → history) covered by Tasks 1-5; Part 2 (approve → auto-ticket + notify, reject → reason + notify, ideas history) covered by Tasks 6-11. "Fora de escopo" items (reopening, editing decided ideas, editing auto-ticket type/priority at approval time) are intentionally not implemented anywhere in this plan.
- **Type consistency:** `finalize_ticket`, `TicketNotFinalizableError`, `TicketAlreadyFinalizedError` (Task 2) match the names imported in Task 3's router and Task 4's frontend usage (`ticket.finalized_at`). `update_project_idea_status`'s new keyword args (`project_id`, `rejection_reason`) match what Task 8/9's router passes and what Task 11's frontend payload sends (`project_id`, `rejection_reason`, both snake_case matching the JSON body). `ProjectIdeaOut.project` (`ProjectIdeaProjectOut { id, name }`) matches how Task 11 reads `idea.project.name` / `idea.project.id`.
- **No placeholders:** every step has literal code, not a description of code.
