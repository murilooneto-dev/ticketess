# TickeTess

*Suporte • TI • Soluções*

Sistema de uso pessoal para gerenciamento dos projetos de desenvolvimento
de software de um escritório: controle de projetos, solicitações
(tickets), integração com GitHub, dashboards e relatórios
técnicos/gerenciais — tudo rodando localmente em Windows, sem Docker,
como app desktop (ou pelo navegador, se preferir).

> O nome de pacote interno (`devcontrol`, arquivos de banco/scripts)
> continua o mesmo por baixo dos panos — é só implementação; a marca
> visível para quem usa o sistema é **TickeTess**.

## Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, Alembic, Pydantic,
  APScheduler, HTTPX, ReportLab.
- **Frontend**: React + Vite + React Router + TanStack Query, compilado
  e servido pelo próprio FastAPI em produção.
- **Banco**: SQLite (modo WAL).

## Instalação

```powershell
.\scripts\install.ps1
```

Isso cria o ambiente virtual do backend, instala as dependências,
copia `.env.example` para `.env`, aplica as migrations e gera o build
de produção do frontend.

Não há tela de login — o sistema é de uso pessoal (um usuário só, sem
papéis/permissões) e abre direto no dashboard.

## Uso

Iniciar manualmente:

```powershell
.\scripts\start.ps1
```

Acesse em `http://localhost:8000` (ou `http://IP-DA-MAQUINA:8000` pela
rede local).

Para iniciar automaticamente com o Windows e liberar o acesso pela
rede local, veja [docs/fase11.md](docs/fase11.md).

## App desktop

Além de acessar pelo navegador, há um app desktop (Electron) que abre o
TickeTess numa janela própria, sem barra de endereço. Ele usa o mesmo
backend local — não é um sistema separado.

```powershell
.\scripts\install-desktop.ps1
```

Isso instala as dependências do app (`desktop/`) e cria um atalho
"TickeTess" na Área de Trabalho. Basta clicar nele para abrir — se o
servidor ainda não estiver rodando, o próprio app inicia o backend
automaticamente; se já estiver (por exemplo, iniciado pelo
`Iniciar TickeTess.bat`), o app só abre a janela usando o servidor
existente.

Requer que a instalação normal (`scripts/install.ps1`) já tenha sido
feita antes (venv do backend e build do frontend).

## Desenvolvimento

```powershell
# backend (com reload automático)
cd backend
.venv\Scripts\activate
python run.py

# frontend (modo dev, com proxy para a API em :8000)
cd frontend
npm run dev
```

Testes do backend:

```powershell
cd backend
.venv\Scripts\activate
pytest -q
```

## Se o sistema for exposto além da LAN

O TickeTess foi construído para rodar em HTTP puro dentro da rede
local do escritório. Se um dia precisar ser acessado fora da LAN (VPN
não conta como "fora"), adicione TLS na frente (ex.: um reverse proxy
com certificado) antes de expor a porta publicamente — isso não faz
parte do escopo atual.

## Fases do projeto

O desenvolvimento seguiu 12 fases incrementais, cada uma documentada em
`docs/`:

| Fase | Descrição | Doc |
|---|---|---|
| 1 | Estrutura inicial, backend/frontend básico | [fase1.md](docs/fase1.md) |
| 2 | Autenticação, usuários e permissões | [fase2.md](docs/fase2.md) |
| 3 | Projetos, gestores e andamentos | [fase3.md](docs/fase3.md) |
| 4 | Tickets, comentários, anexos, histórico | [fase4.md](docs/fase4.md) |
| 5 | Notificações | [fase5.md](docs/fase5.md) |
| 6 | Integração GitHub | [fase6.md](docs/fase6.md) |
| 7 | Dashboards | [fase7.md](docs/fase7.md) |
| 8 | Relatórios técnico e gerencial | [fase8.md](docs/fase8.md) |
| 9 | *(pulada — ver fase8.md, decisão registrada)* | — |
| 10 | Scheduler, sync automática, backups | [fase10.md](docs/fase10.md) |
| 11 | Instalação e inicialização no Windows | [fase11.md](docs/fase11.md) |
| 12 | Testes finais e segurança | [fase12.md](docs/fase12.md) |

## Atualizações pós-lançamento

- Identidade visual **TickeTess** aplicada em toda a interface e nos
  relatórios PDF (cabeçalho, cores, rodapé com paginação).
- App desktop (Electron) — veja a seção "App desktop" acima.
- Sistema simplificado para uso pessoal: login e papéis
  (Admin/Gestor/Operador) removidos, tela de "Usuários" removida,
  notificações removidas. Criação de ticket ganhou campo livre "quem
  pediu" e status selecionável na hora de abrir a solicitação. O
  relatório de acompanhamento passou a resumir cada projeto numa única
  linha ("N alterações entre DD/MM e DD/MM") em vez de listar cada
  evento; o relatório técnico continua detalhado.
