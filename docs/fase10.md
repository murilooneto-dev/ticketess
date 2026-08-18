# DevControl — Fase 10

## O que foi implementado

Scheduler em background (APScheduler, `BackgroundScheduler`) iniciado e
finalizado junto com o ciclo de vida da aplicação FastAPI
(`app/main.py`, lifespan). Três jobs, cada um controlado por uma flag no
`.env`:

1. **Sincronização automática do GitHub** (`GITHUB_ENABLED`,
   `GITHUB_SYNC_INTERVAL` em minutos) — percorre todos os projetos com
   `github_repo` configurado e chama `github_service.sync_project` para
   cada um. Se um repositório falhar (API fora do ar, rate limit, etc.),
   o erro é logado e os demais projetos continuam sendo processados.

2. **Geração automática dos relatórios semanais** (`REPORT_ENABLED`,
   `REPORT_DAY` — dia da semana, 0=segunda a 6=domingo, `REPORT_TIME`) —
   gera os relatórios técnico e gerencial para os últimos 7 dias,
   reaproveitando o mesmo `report_service.generate_reports` da Fase 8.
   `generated_by` fica `None` para indicar geração automática pelo
   sistema.

3. **Backup diário do banco de dados** (`BACKUP_ENABLED`, `BACKUP_TIME`,
   `BACKUP_RETENTION_DAYS`) — copia o arquivo SQLite para
   `backups/database/devcontrol_AAAAMMDD_HHMMSS.db` e remove backups
   mais antigos que `BACKUP_RETENTION_DAYS`.

Logs dedicados passaram a existir conforme já estava previsto desde a
Fase 1: `logs/scheduler.log` e `logs/github.log` (além do
`logs/security.log`, que já vinha sendo usado desde a Fase 2), todos
também espelhados em `logs/app.log`.

## Testes

83 testes automatizados (`pytest -q`), incluindo 8 novos para os jobs do
scheduler: sincronização pulada quando desabilitada, sincroniza somente
projetos com repositório configurado, continua após erro em um projeto,
geração de relatório pulada quando desabilitada, geração cria os dois
PDFs com `generated_by=None`, backup pulado quando desabilitado, e
backup cria a cópia e limpa arquivos expirados pela retenção.

Também validei manualmente que o scheduler inicia e finaliza de forma
limpa junto com o ciclo de vida completo da aplicação (os 3 jobs são
registrados no startup e desligados no shutdown, sem erros).
