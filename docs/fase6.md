# DevControl — Fase 6

## O que foi implementado

- Campo `github_repo` (formato `owner/repo`) no `Project`, mais
  `github_synced_at` para saber quando foi a última sincronização.
- Modelos `GithubCommit` e `GithubPullRequest`, vinculados ao projeto e,
  quando aplicável, a um ticket.
- **Associação automática com tickets**: ao sincronizar, mensagens de
  commit e título/corpo de pull requests são varridos em busca de um
  padrão `#<numero>`; se existir um ticket com esse ID no mesmo projeto,
  o commit/PR é vinculado a ele.
- `github_service.py` usa HTTPX para consultar a API REST do GitHub
  (`/repos/{owner}/{repo}/commits` e `/pulls`), respeitando
  `GITHUB_ENABLED` e `GITHUB_TOKEN` do `.env`. A sincronização é
  **manual** nesta fase (disparada pelo admin); a sincronização
  automática por agendamento fica para a Fase 10, como já estava previsto
  no plano.
- Endpoints:
  - `POST /api/projects/{id}/github/sync` — dispara a sincronização
    (somente admin); faz upsert de commits/PRs (sem duplicar em
    resincronizações).
  - `GET /api/projects/{id}/github/commits` — lista commits sincronizados
    do projeto.
  - `GET /api/projects/{id}/github/pull-requests` — lista PRs
    sincronizados do projeto.
  - `GET /api/tickets/{id}/github` — commits e PRs vinculados a um
    ticket específico.
- Frontend:
  - Campo de repositório no formulário de novo projeto e editável na
    página de detalhe do projeto (admin).
  - Botão "Sincronizar agora" com resumo do resultado (quantos
    commits/PRs foram importados).
  - Listas de commits e pull requests na página do projeto, com link
    para o ticket vinculado quando existir.
  - Seção "Atividade no GitHub" na página do ticket, mostrando os
    commits/PRs relacionados a ele.

## Testes

61 testes automatizados (`pytest -q`), incluindo 9 novos para GitHub:
sincronização desabilitada, repositório não configurado, permissão
(somente admin sincroniza, mas qualquer autenticado visualiza),
importação e associação correta com ticket via `#numero`, idempotência
ao resincronizar (sem duplicar registros), tratamento de erro da API do
GitHub (502), projeto inexistente (404) e validação do formato
`owner/repo`.

Testado manualmente no navegador com um repositório público real
(`octocat/Hello-World`): configurei o repositório no projeto, cliquei em
"Sincronizar agora" e a integração trouxe corretamente 3 commits e 50
pull requests da API real do GitHub.

## Atualização: token do GitHub por projeto

Como tokens do GitHub (principalmente os *fine-grained*) costumam ser
escopados por repositório, o `GITHUB_TOKEN` do `.env` passou a ser
apenas um **token padrão/fallback**. Cada projeto pode ter seu próprio
token configurado na tela de detalhe do projeto (admin), sobrepondo o
token global para aquele repositório específico.

- Coluna `github_token` no `Project` (nunca retornada pela API — o
  endpoint só expõe `has_github_token: bool`, calculado a partir do
  valor salvo, sem nunca serializar o token em si).
- `github_service.sync_project` usa `project.github_token` quando
  presente; senão cai para `settings.GITHUB_TOKEN`.
- `PUT /api/projects/{id}` aceita `github_token` (define/substitui) e
  `clear_github_token: true` (remove o token específico, voltando a
  usar o padrão global).
- Frontend: campo de token (tipo senha, nunca pré-preenchido) tanto na
  criação quanto na edição do projeto, com indicação se já existe um
  token configurado e botão para removê-lo.
- 4 novos testes: token do projeto sobrepõe o global, sem token do
  projeto cai no global, o valor nunca aparece em nenhuma resposta da
  API, e remoção do token funciona. Suíte completa: 92 testes.
