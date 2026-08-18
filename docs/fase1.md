# DevControl — Fase 1

## Como executar em desenvolvimento

Backend:

```
cd backend
.venv\Scripts\activate
python run.py
```

API disponível em http://localhost:8000 (health check em `/api/system/health`).

Frontend (modo dev, com proxy para a API):

```
cd frontend
npm install
npm run dev
```

## Como gerar build de produção

```
cd frontend
npm run build
```

O backend detecta `frontend/dist/` automaticamente e passa a servir o
frontend compilado em `http://IP-DA-MAQUINA:8000/`.

## Migrations (Alembic)

```
cd backend
.venv\Scripts\activate
alembic revision --autogenerate -m "descricao"
alembic upgrade head
```

## Testes

```
cd backend
.venv\Scripts\activate
pytest -q
```
