# Ideias de Projeto — Design

## Contexto

Hoje, criar um projeto no TickeTess é uma ação restrita ao admin (`POST /api/projects`, ver [projects.py](../../../backend/app/api/projects.py)). Não existe forma de um gestor ou operador sugerir uma ideia de projeto para o admin avaliar depois.

## Objetivo

Permitir que qualquer usuário logado (admin, gestor ou operador) registre uma ideia de projeto (título + descrição). O admin acompanha todas as ideias enviadas e pode marcá-las como aprovadas ou rejeitadas. Não há vínculo automático entre uma ideia aprovada e a criação de um projeto — a aprovação é só um controle de status; se o admin decidir seguir com a ideia, cria o projeto manualmente pela tela já existente.

## Modelo de dados

Nova tabela `project_ideas`:

| Campo | Tipo | Observação |
|---|---|---|
| `id` | int, PK | |
| `title` | string(160) | obrigatório |
| `description` | text | obrigatório |
| `status` | enum: `pendente`, `aprovada`, `rejeitada` | default `pendente` |
| `created_by` | FK `users.id` | autor da ideia |
| `created_at` | datetime | |
| `updated_at` | datetime | atualizado quando o status muda |

Segue o padrão dos models existentes (`Base`, `Mapped`, `mapped_column`) — ver [ticket.py](../../../backend/app/models/ticket.py) como referência de estilo.

## Permissões e visibilidade

- **Enviar ideia**: qualquer usuário autenticado (`get_current_user`), sem restrição de papel.
- **Listar ideias**:
  - Usuário não-admin: vê apenas as ideias que ele mesmo criou.
  - Admin: vê todas as ideias de todos os usuários.
- **Mudar status** (aprovar/rejeitar): apenas admin (`require_admin`, mesmo padrão de [projects.py:38-47](../../../backend/app/api/projects.py)).

## Notificações

Reaproveita o sistema de notificações existente ([notification.py](../../../backend/app/models/notification.py), `notify_users`/`list_admins` como usado em [ticket_service.py:91-100](../../../backend/app/services/ticket_service.py)).

Novos valores em `NotificationType`: `PROJECT_IDEA_CREATED`, `PROJECT_IDEA_STATUS_CHANGED`.

- **Ao criar uma ideia** → notifica todos os admins (exclui o próprio autor se ele for admin).
- **Ao admin mudar o status** → notifica o autor da ideia, com o novo status na mensagem.

## Backend

- `app/models/project_idea.py` — model `ProjectIdea` + enum `ProjectIdeaStatus`.
- `app/schemas/project_idea.py`:
  - `ProjectIdeaCreate` (title, description)
  - `ProjectIdeaOut` (todos os campos + autor)
  - `ProjectIdeaStatusUpdate` (status)
- `app/services/project_idea_service.py`:
  - `create_project_idea(db, author_id, data)` — cria e notifica admins
  - `list_project_ideas(db, current_user)` — retorna todas se admin, senão filtra por `created_by`
  - `update_project_idea_status(db, idea_id, status)` — muda status, notifica autor, levanta `ProjectIdeaNotFoundError` se não existir
- `app/api/project_ideas.py`:
  - `POST /api/project-ideas` — qualquer usuário autenticado
  - `GET /api/project-ideas` — qualquer usuário autenticado (filtragem feita no service)
  - `PATCH /api/project-ideas/{id}` — só admin
- Migration Alembic nova para a tabela `project_ideas`.
- Registrar o router novo em `app/main.py`, junto dos demais.

## Frontend

- Nova página `ProjectIdeasPage.jsx`, rota `/project-ideas`, item na navbar visível a todos os papéis.
- Formulário de envio: título + descrição (mesmo estilo de [NewProjectPage.jsx](../../../frontend/src/pages/NewProjectPage.jsx)).
- Lista abaixo do formulário:
  - Usuário comum: só as próprias ideias, com badge de status (pendente/aprovada/rejeitada).
  - Admin: lista de todas as ideias, com autor, e botões "Aprovar"/"Rejeitar" em ideias pendentes.
- `frontend/src/services/projectIdeas.js` — `createProjectIdea`, `fetchProjectIdeas`, `updateProjectIdeaStatus`, seguindo o padrão de [projects.js](../../../frontend/src/services/projects.js).

## Testes

- Backend: `backend/tests/test_project_ideas.py` cobrindo:
  - criação por usuário não-admin
  - listagem filtrada por autor vs. listagem completa do admin
  - admin aprova/rejeita, não-admin recebe 403 ao tentar
  - notificação criada para admins na criação, e para o autor na mudança de status

## Fora de escopo

- Conversão automática de ideia aprovada em projeto.
- Comentários/discussão na ideia.
- Edição da ideia pelo autor após o envio.
