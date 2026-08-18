# TickeTess

*Suporte • TI • Soluções*

Sistema interno para gerenciamento dos projetos de desenvolvimento de
software de um escritório: controle de projetos, solicitações
(tickets), integração com GitHub, notificações, dashboards e relatórios
técnicos/gerenciais — tudo rodando localmente em Windows, disponível
pela rede local (LAN), sem Docker.

> O nome de pacote interno (`devcontrol`, arquivos de banco/scripts)
> continua o mesmo por baixo dos panos — é só implementação; a marca
> visível para quem usa o sistema é **TickeTess**.

## Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, Alembic, Pydantic,
  APScheduler, HTTPX, bcrypt, ReportLab.
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

**Depois da instalação, edite o `.env`** e troque pelo menos
`ADMIN_PASSWORD` (o sistema avisa no log se você esquecer). O login
inicial do administrador usa `ADMIN_USERNAME` (padrão: `admin`).

## Uso

Iniciar manualmente:

```powershell
.\scripts\start.ps1
```

Acesse em `http://localhost:8000` (ou `http://IP-DA-MAQUINA:8000` pela
rede local).

Para iniciar automaticamente com o Windows e liberar o acesso pela
rede local, veja [docs/fase11.md](docs/fase11.md).

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

## Login

O login é feito por **nome de usuário e senha** (sem e-mail). Cada
usuário é cadastrado pelo administrador na tela "Usuários".

## Papéis de usuário

- **Administrador**: desenvolve os sistemas, cadastra usuários, define
  classificação/prioridade/status das solicitações, controla o
  andamento de projetos e gera relatórios. Vê e altera tudo.
- **Gestor**: visualiza todas as solicitações (de operadores e de
  outros gestores) e todos os projetos, abre novas solicitações e
  comenta. Não define tipo/prioridade/status.
- **Operador**: abre solicitações (novas funcionalidades, alterações,
  melhorias, bugs, suporte) e só acompanha o andamento e status das
  solicitações que ele mesmo criou.

O administrador é sempre notificado quando um gestor ou operador cria,
comenta ou anexa algo a uma solicitação.

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

- Papel **Operador** adicionado (visibilidade restrita às próprias
  solicitações); login passou a ser por usuário/senha (sem e-mail);
  tela de cadastro de usuários; classificação/prioridade da solicitação
  ficou exclusiva do admin; notificações ampliadas para sempre avisar o
  admin quando gestor/operador altera algo.
- Identidade visual **TickeTess** aplicada em toda a interface e nos
  relatórios PDF (cabeçalho, cores, rodapé com paginação).
