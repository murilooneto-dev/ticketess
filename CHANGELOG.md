# Changelog

Todas as mudanças relevantes deste projeto estão documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/).

---

## [v1.0.0] - 2026-09-14

Virada do TickeTess de sistema multiusuário (LAN, login por
usuário/senha, papéis Admin/Gestor/Operador) para app desktop de uso
pessoal (single-user, sem login).

### Adicionado
- App desktop (Electron) — janela própria sem barra de endereço,
  reaproveitando o backend local existente (`desktop/main.js`,
  `desktop/loading.html`, `desktop/build/icon.ico`).
- Script `scripts/install-desktop.ps1` — instala as dependências do
  app desktop e cria atalho "TickeTess" na Área de Trabalho.
- Campo livre "quem pediu" (`requester_name`) e seleção de status na
  criação de ticket, substituindo o autor implícito do login.
- Resumo consolidado por projeto no relatório de acompanhamento
  ("N alterações realizadas entre DD/MM e DD/MM"), em vez de listar
  cada evento individualmente. O relatório técnico continua detalhado.

### Removido
- Login (usuário/senha, sessão por cookie), papéis de usuário
  (Admin/Gestor/Operador), tela de gestão de usuários e sistema de
  notificações — o sistema passou a ser de uso pessoal, sempre com
  acesso total.
- Tabelas `users`, `sessions` e `notifications`, e colunas de
  autor/gestor (`tickets.created_by`, `ticket_comments.author_id`,
  `ticket_attachments.uploaded_by`, `ticket_history.author_id`,
  `projects.manager_id`, `project_updates.author_id`,
  `project_ideas.created_by`, `reports.generated_by`) via migration
  Alembic (`c398ccb256a1`).
- Dependências `bcrypt` e `passlib`, sem uso após a remoção da
  autenticação.

### Alterado
- Todos os endpoints da API deixaram de exigir autenticação/permissão
  por papel.
- Suíte de testes do backend reescrita para o modelo single-user
  (80 testes passando).
- `README.md` atualizado (removidas as seções de login/papéis,
  adicionada a seção "App desktop").

### Arquivos alterados
- `desktop/` — novo app Electron.
- `scripts/install-desktop.ps1` — novo script de instalação do app
  desktop.
- `backend/app/api/`, `backend/app/services/`, `backend/app/models/`,
  `backend/app/schemas/` — remoção de auth/papéis/notificações,
  simplificação de tickets/projetos/ideias de projeto.
- `backend/migrations/versions/c398ccb256a1_remove_auth_roles_single_user.py`
  — migration de remoção das tabelas/colunas de autenticação.
- `backend/app/services/report_glossary.py`,
  `backend/app/services/report_service.py` — resumo consolidado do
  relatório de acompanhamento.
- `frontend/src/` — remoção de telas/contexto de login, papéis e
  notificações; formulário de novo ticket com "quem pediu" e status.
- `backend/tests/` — suíte reescrita sem fixtures de login/papel.
- `README.md`, `CHANGELOG.md`, `.gitignore`, `backend/requirements.txt`.
