# DevControl — Fase 3

## O que foi implementado

- Modelos `Project` (com `status`: ativo/pausado/concluído/cancelado, e
  `manager_id` opcional apontando para um usuário gestor) e `ProjectUpdate`
  (registros de andamento, com autor e data).
- Endpoints:
  - `GET /api/projects` — lista todos os projetos; aceita `?mine=true` para
    filtrar apenas os projetos em que o usuário logado é o gestor
    responsável.
  - `POST /api/projects` — cria projeto (somente admin).
  - `GET /api/projects/{id}` — detalhe do projeto.
  - `PUT /api/projects/{id}` — atualiza nome/descrição/status/gestor
    (somente admin).
  - `GET /api/projects/{id}/updates` — lista o histórico de andamento
    (qualquer usuário autenticado).
  - `POST /api/projects/{id}/updates` — registra um novo andamento
    (somente admin).
- Regra de negócio "todos os gestores veem todos os projetos, com filtro
  para os próprios" implementada via o parâmetro `mine`.
- Permissões reforçadas no backend (admin cria/edita projetos e andamentos;
  gestor só visualiza).
- Frontend:
  - `/projects` — lista de projetos com filtro "meus projetos" e badge de
    status.
  - `/projects/new` — formulário de criação (somente admin; gestor é
    redirecionado se tentar acessar).
  - `/projects/:id` — detalhe do projeto, histórico de andamento, campo
    para registrar novo andamento (somente admin) e seletor de status
    (somente admin; gestor vê como badge somente leitura).
  - Barra de navegação com link para Projetos e botão de sair.

## Testes

30 testes automatizados (`pytest -q`), incluindo 11 novos para projetos:
listagem, filtro `mine`, permissões de criação/atualização, gestor
inválido, criação/listagem de andamentos e permissões de acesso.

Testado manualmente no navegador (via requestSubmit por conta de um
problema de composição de frames do painel de preview, não do app):
login → criar projeto com admin → registrar andamento → alterar status →
logout → login como gestor → confirmar que "Novo projeto" some, status
vira somente leitura e o formulário de andamento não aparece, mas o
histórico continua visível.
