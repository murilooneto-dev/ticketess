# Finalização de solicitações + Aprovação/rejeição de ideias

Data: 2026-08-19

## Contexto

Hoje o sistema tem dois fluxos separados:

- **Solicitações (Tickets)**: `TicketStatus` já inclui `concluido` e `cancelado`, mas não existe nenhuma forma de "arquivar" uma solicitação terminada — ela permanece misturada com as ativas na mesma lista para sempre.
- **Ideias de projeto (`ProjectIdea`)**: admin aprova ou rejeita uma ideia (`pendente` → `aprovada`/`rejeitada`), mas isso não gera nenhuma ação de acompanhamento — a ideia aprovada não vira trabalho real, e uma rejeição não registra motivo.

Este documento cobre duas mudanças relacionadas: dar um destino final ("Finalizar" → Histórico) às solicitações concluídas/canceladas, e fechar o ciclo das ideias aprovadas (virando solicitação) e rejeitadas (com motivo registrado).

## Parte 1 — Finalizar solicitações

### Modelo

- `Ticket.finalized_at: datetime | None` (nullable, default `NULL`). Migration Alembic adiciona a coluna.

### Backend

- `POST /api/tickets/{id}/finalize` (admin only, via `require_admin`):
  - 400 se `ticket.status` não for `concluido` nem `cancelado`.
  - 400 se `finalized_at` já estiver preenchido.
  - Seta `finalized_at = now()`. Não altera status, não apaga nem move comentários/anexos/histórico — a finalização é só um carimbo; tudo que já existia continua acessível na página de detalhes.
  - Ação é **definitiva**: não existe endpoint de "reabrir".
- `list_tickets` ganha parâmetro `finalized: bool = False`:
  - `False` (padrão): `WHERE finalized_at IS NULL` — comportamento atual, é a lista ativa.
  - `True`: `WHERE finalized_at IS NOT NULL` — histórico.
- `TicketOut` / `TicketListItemOut` incluem `finalized_at`.

### Frontend

- `TicketsPage`: abas "Ativas" / "Histórico" acima da tabela (state local + parâmetro na query). Na aba Histórico não aparece o botão "Nova solicitação".
- `TicketDetailPage`:
  - Quando `status` é `concluido` ou `cancelado` e `finalized_at` é nulo: mostra botão **Finalizar** perto dos campos de Tipo/Prioridade/Status. Confirma via `window.confirm` (ou modal simples) — "Finalizar esta solicitação? Ela irá para o histórico e não poderá ser reaberta." — e chama o endpoint novo.
  - Quando já finalizada: mostra badge "Finalizada em dd/mm/aaaa" no lugar do botão; os selects de Tipo/Prioridade/Status viram texto somente-leitura (não fazem sentido editar algo finalizado).
  - Todo o resto da página (comentários, anexos, histórico de campos, atividade GitHub) continua normalmente — é aí que fica "tudo registrado" quando a solicitação está no histórico.

## Parte 2 — Aprovação/rejeição de ideias

### Modelo

- `ProjectIdea.project_id: int | None` (FK `projects.id`, nullable — ideias antigas sem projeto continuam válidas).
- `ProjectIdea.rejection_reason: str | None` (Text).
- Migration Alembic adiciona as duas colunas.

### Criação de ideia (frontend)

- `ProjectIdeasPage`, no formulário de nova ideia, ganha um `<select>` de projeto **obrigatório** (mesmo padrão do `NewTicketPage`), enviado como `project_id` no `ProjectIdeaCreate`.

### Aprovar

- Se a ideia já tem `project_id`, aprovação segue direto.
- Se não tem (ideia antiga), o diálogo de aprovação exige escolher um projeto antes de confirmar — esse `project_id` é enviado junto no payload de aprovação e persistido na ideia.
- Ao confirmar (`status = aprovada`):
  1. Cria um `Ticket`: `title`/`description` iguais aos da ideia, `project_id` da ideia, `created_by` = autor da ideia, `type = outro`, `priority = media` (mesmo default de quando um não-admin abre solicitação).
  2. A notificação padrão de "nova solicitação" para os demais admins (já existente em `create_ticket`) dispara normalmente.
  3. Notifica o autor da ideia: título "Ideia aprovada: {title}", mensagem "Sua ideia '{title}' foi aprovada e virou a solicitação '{title}'.", link para `/tickets/{novo_id}`.

### Rejeitar

- O diálogo de rejeição exige preencher **Motivo da rejeição** (texto, obrigatório) antes de confirmar.
- Ao confirmar (`status = rejeitada`): salva em `rejection_reason` e notifica o autor: título "Ideia rejeitada: {title}", mensagem "Sua ideia '{title}' foi rejeitada: {motivo}.", link para `/project-ideas`.

### Backend

- `ProjectIdeaStatusUpdate` ganha `project_id: int | None` e `rejection_reason: str | None`.
  - Validação de serviço (não só de schema): se `status == REJEITADA`, `rejection_reason` é obrigatório (não vazio); se `status == APROVADA` e a ideia não tem `project_id` nem o payload trouxe um, erro 400.
- `update_project_idea_status` implementa a lógica de aprovar (cria ticket + notifica) e rejeitar (salva motivo + notifica) descrita acima, usando `ticket_service.create_ticket`.

### Frontend — Histórico de ideias

- `ProjectIdeasPage` ganha abas "Pendentes" / "Histórico", no mesmo padrão da Parte 1:
  - Pendentes: `status == pendente` (comportamento atual da tabela, com os botões Aprovar/Rejeitar).
  - Histórico: `status in (aprovada, rejeitada)`, mostrando o motivo de rejeição quando houver, e link para a solicitação gerada quando aprovada.

## Fora de escopo

- Reabrir solicitação finalizada ou ideia já decidida.
- Editar ideia depois de decidida.
- Mudar o tipo/prioridade da solicitação auto-gerada no momento da aprovação (admin edita depois, normalmente, na tela de detalhes).
