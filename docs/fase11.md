# DevControl — Fase 11

## O que foi implementado

Scripts PowerShell em `scripts/` para instalar e colocar o DevControl
para iniciar automaticamente com o Windows, sem Docker e sem serviços
externos (usa o Agendador de Tarefas nativo do Windows):

- **`install.ps1`** — instalação inicial: cria o `.venv` do backend,
  instala dependências, copia `.env.example` para `.env` (se ainda não
  existir), aplica as migrations do banco e gera o build de produção do
  frontend (`npm install` + `npm run build`).
- **`start.ps1`** — inicia o servidor (`python run.py`), que serve tanto
  a API quanto o frontend compilado. Usado tanto para start manual
  quanto pela tarefa agendada.
- **`register_startup_task.ps1`** *(requer Administrador)* — registra
  uma Tarefa Agendada do Windows (`DevControl`) que executa
  `start.ps1` na inicialização do sistema, rodando como `SYSTEM`, com
  até 3 tentativas de reinício automático em caso de falha.
- **`unregister_startup_task.ps1`** *(requer Administrador)* — remove
  essa tarefa agendada.
- **`open_firewall_port.ps1`** *(requer Administrador)* — cria uma regra
  de firewall liberando a porta do servidor (padrão 8000) para acesso
  pela rede local, necessário para acessar via `http://IP-DA-MAQUINA:8000`
  de outras máquinas do escritório.

## Por que Agendador de Tarefas em vez de um serviço Windows

Rodar como serviço Windows "de verdade" exigiria uma dependência extra
(`pywin32` ou NSSM) fora da stack combinada. O Agendador de Tarefas já
vem no Windows, suporta iniciar antes do login, reiniciar em caso de
falha e não adiciona nenhuma dependência nova — mantendo a solução
simples, conforme pedido.

## O que eu não executei

Os scripts que alteram configurações do sistema
(`register_startup_task.ps1`, `unregister_startup_task.ps1`,
`open_firewall_port.ps1`) **não foram executados por mim** — validei
apenas a sintaxe de todos os `.ps1` (sem erros). Registrar tarefas do
sistema e alterar o firewall são ações que cabem a você rodar,
manualmente, como Administrador, quando decidir colocar o DevControl
em produção na máquina definitiva.

## Como usar (na máquina de produção)

```powershell
cd C:\DevControl   # ou D:\DEV\DevControl, conforme o local escolhido
.\scripts\install.ps1

# Edite o .env (principalmente ADMIN_PASSWORD)

# Como Administrador:
.\scripts\register_startup_task.ps1
.\scripts\open_firewall_port.ps1
```
