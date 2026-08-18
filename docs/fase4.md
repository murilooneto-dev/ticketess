# DevControl — Fase 4

## O que foi implementado

- Modelos `Ticket` (vinculado a um projeto, com `type`, `priority`,
  `status` e autor), `TicketComment`, `TicketAttachment` e
  `TicketHistory` (log automático de mudanças de tipo/prioridade/status).
- Classificação (`type`): nova funcionalidade, alteração, melhoria,
  correção de bug, suporte, outro.
- Prioridade (`priority`): baixa, média, alta, urgente.
- Status (`status`): aberto, em andamento, aguardando, concluído,
  cancelado.
- Endpoints:
  - `GET /api/tickets` — lista com filtros `project_id`, `mine`, `status`,
    `priority`.
  - `POST /api/tickets` — abre uma solicitação (qualquer usuário
    autenticado, admin ou gestor).
  - `GET /api/tickets/{id}` — detalhe.
  - `PUT /api/tickets/{id}` — altera classificação/prioridade/status
    (somente admin); toda mudança gera um registro em `TicketHistory`
    automaticamente.
  - `GET/POST /api/tickets/{id}/comments` — comentários (qualquer usuário
    autenticado).
  - `GET/POST /api/tickets/{id}/attachments` — anexos, armazenados em
    `storage/tickets/{id}/`, com limite de tamanho (`UPLOAD_MAX_SIZE_MB`).
  - `GET /api/tickets/{id}/attachments/{attachment_id}/download` —
    download do arquivo.
  - `GET /api/tickets/{id}/history` — histórico de alterações.
- Regra de negócio: gestores abrem solicitações e comentam; o
  administrador controla classificação, prioridade e status (conforme
  "o administrador controlará o desenvolvimento dessas solicitações").
- Frontend:
  - `/tickets` — lista com filtros (minhas solicitações, status,
    prioridade).
  - `/tickets/new` — formulário de abertura (projeto, título, descrição,
    tipo, prioridade).
  - `/tickets/{id}` — detalhe: campos editáveis (admin) ou badges
    (gestor), lista de anexos com upload, comentários e histórico de
    alterações.

## Testes

42 testes automatizados (`pytest -q`), incluindo 13 novos para tickets:
criação, projeto inválido, permissão de atualização (admin vs. gestor),
histórico automático em mudanças de status/prioridade, filtros `mine` e
`project_id`, comentários, upload/download de anexo, limite de tamanho de
arquivo e ticket inexistente.

Testado manualmente no navegador: login → criar projeto → abrir
solicitação (bug, prioridade alta) → mudar status para "em andamento"
(gera histórico) → comentar → anexar arquivo → baixar anexo → logout →
login como gestor → confirmar que os campos viram somente leitura mas a
criação de solicitações, comentários, anexos e histórico continuam
acessíveis.
