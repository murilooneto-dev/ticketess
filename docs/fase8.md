# DevControl — Fase 8

## O que foi implementado

Relatórios técnico e gerencial gerados a partir dos mesmos dados, sem IA
(conforme decidido — ver [MEMORY] Fase 8 reports scope), usando um
glossário determinístico para traduzir termos técnicos em linguagem
simples.

- Modelo `Report` (tipo, período, caminho do arquivo, quem gerou).
- `report_data.py` — agrega, por projeto e por período: solicitações
  abertas, solicitações concluídas/canceladas (via `TicketHistory`),
  commits, pull requests e andamentos registrados.
- `report_glossary.py` — mapeamento de tipo/status/prioridade de ticket
  para frases em linguagem comum, e funções que descrevem eventos
  (abertura de ticket, conclusão, PR revisado/incorporado, contagem de
  commits) tanto em versão técnica quanto em versão simples.
- `report_service.py` — monta os dois PDFs (ReportLab) a partir da mesma
  coleta de dados:
  - **Técnico** (`reports/technical/`): IDs de ticket, tipo/prioridade,
    SHAs de commit, números de PR.
  - **Acompanhamento** (`reports/management/`): mesmas informações
    reescritas pelo glossário — ex. "Está concluída: a correção de um
    problema — 'Login não funciona no Safari'." em vez de
    "#12 [bug] Login não funciona no Safari (status final: concluido)".
- Reprocessar o mesmo período faz *upsert* (substitui o PDF e atualiza o
  registro, sem duplicar).
- Endpoints:
  - `POST /api/reports/generate` — gera os dois relatórios para um
    período (`period_start`/`period_end` opcionais; padrão: últimos 7
    dias). Somente admin.
  - `GET /api/reports` — lista relatórios gerados; admin vê os dois
    tipos, gestor só vê o de acompanhamento.
  - `GET /api/reports/{id}/download` — baixa o PDF; gestor não pode
    baixar relatórios técnicos (403).
- Frontend: página `/reports` com formulário de geração (admin, período
  opcional) e duas listas de relatórios com link de download.

## Testes

75 testes automatizados (`pytest -q`), incluindo 10 novos para
relatórios: permissão de geração (somente admin), geração com período
explícito (PDFs válidos gerados em disco), período padrão de 7 dias,
idempotência ao regenerar o mesmo período, listagem filtrada por papel,
permissão de download por tipo, relatório inexistente (404) e validação
de período inválido (start > end).
