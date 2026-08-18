# DevControl — Fase 7

## O que foi implementado

- Endpoint `GET /api/dashboard/summary`, agregando:
  - Total de projetos e de solicitações (tickets).
  - Minhas solicitações em aberto (do usuário logado, excluindo
    concluído/cancelado).
  - Projetos que eu gerencio (relevante para gestores).
  - Projetos por status, solicitações por status e por prioridade
    (contagens completas, incluindo zero).
  - As 5 solicitações mais recentes.
  - Os 5 commits e 5 pull requests do GitHub mais recentes (entre todos
    os projetos sincronizados).
- A antiga página inicial estática (`HomePage`) foi substituída pelo
  dashboard real (`DashboardPage`), continuando em `/`.
- Sem novas dependências: os gráficos são barras simples em CSS
  (`StatBarList`), reutilizando as mesmas cores dos badges já usados no
  resto do sistema — sem adicionar biblioteca de gráficos à stack.

## Testes

65 testes automatizados (`pytest -q`), incluindo 4 novos para o
dashboard: autenticação obrigatória, estado vazio (todas as contagens
zeradas mas com todas as chaves presentes), contagens refletindo dados
reais criados (projetos/tickets por status e prioridade), e projetos
gerenciados por um gestor específico.
