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
  cada evento individualmente.
- Tela única na home (`/`): projetos em cards recolhíveis (nome +
  contagem de solicitações), que expandem mostrando edição do
  projeto, GitHub, andamentos e as solicitações daquele projeto.
  Botões "Novo projeto", "Nova solicitação" e "Relatório" no topo
  (`frontend/src/pages/HomePage.jsx`,
  `frontend/src/components/ProjectCard.jsx`,
  `frontend/src/components/NewProjectForm.jsx`).

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
- Funcionalidade "Ideias de projeto" (tabela `project_ideas`, models,
  schemas, services, API e tela) — não usada.
- Relatório técnico — só sobra o relatório de acompanhamento; `Report`
  deixou de ter o campo `type` (migration `5ff54f1175de`).
- Dashboard (cards de estatística, gráficos de barra) e as telas
  separadas de Projetos/Novo Projeto/Detalhe de Projeto/Solicitações —
  substituídas pela tela única (`HomePage`/`ProjectCard`).

### Alterado
- Todos os endpoints da API deixaram de exigir autenticação/permissão
  por papel.
- Suíte de testes do backend reescrita para o modelo single-user
  (61 testes passando).
- `README.md` atualizado (removidas as seções de login/papéis,
  adicionada a seção "App desktop", refletida a tela única).

### Arquivos alterados
- `desktop/` — novo app Electron.
- `scripts/install-desktop.ps1` — novo script de instalação do app
  desktop.
- `backend/app/api/`, `backend/app/services/`, `backend/app/models/`,
  `backend/app/schemas/` — remoção de auth/papéis/notificações/ideias
  de projeto/dashboard/relatório técnico, simplificação de
  tickets/projetos.
- `backend/migrations/versions/c398ccb256a1_remove_auth_roles_single_user.py`
  e `backend/migrations/versions/5ff54f1175de_remove_project_ideas_and_technical_.py`
  — migrations de remoção das tabelas/colunas de autenticação, ideias
  de projeto e tipo de relatório.
- `backend/app/services/report_glossary.py`,
  `backend/app/services/report_service.py` — resumo consolidado do
  relatório de acompanhamento, sem mais branch técnico.
- `frontend/src/` — remoção de telas/contexto de login, papéis,
  notificações, dashboard, ideias de projeto e das telas separadas de
  projeto/ticket; nova tela única (`HomePage`, `ProjectCard`,
  `NewProjectForm`).
- `backend/tests/` — suíte reescrita sem fixtures de login/papel, sem
  testes de dashboard/ideias de projeto.
- `README.md`, `CHANGELOG.md`, `.gitignore`, `backend/requirements.txt`.
