# DevControl — Fase 2

## O que foi implementado

- Modelos `User` (com papéis `admin`/`gestor`) e `Session` (tokens de sessão).
- Hash de senha com `bcrypt`.
- Autenticação por cookie de sessão (`devcontrol_session`, httponly), com
  token aleatório armazenado como hash SHA-256 no banco e expiração
  configurável (`SESSION_EXPIRE_DAYS`).
- Endpoints:
  - `POST /api/auth/login`
  - `POST /api/auth/logout`
  - `GET /api/auth/me`
  - `GET /api/users`, `POST /api/users`, `PUT /api/users/{id}` (somente admin)
- Permissões verificadas no backend via dependências
  (`get_current_user`, `require_admin`) — o frontend nunca é a fonte de
  verdade.
- Um usuário administrador é criado automaticamente no startup, caso
  nenhum admin exista, usando `ADMIN_NAME`/`ADMIN_EMAIL`/`ADMIN_PASSWORD`
  do `.env`. **Troque a senha padrão em produção.**
- Frontend: tela de login, `AuthContext`, rota protegida (`ProtectedRoute`)
  e botão de logout na home.

## Credenciais padrão (trocar depois do primeiro login)

```
E-mail: admin@devcontrol.local
Senha: changeme123
```

## Testes

19 testes automatizados (`pytest -q`), cobrindo:

- login com credenciais válidas/ inválidas/ usuário inativo;
- `/api/auth/me` autenticado e não autenticado;
- logout invalidando a sessão;
- permissão de admin vs. gestor no CRUD de usuários;
- e-mail duplicado ao criar usuário.

Testado também manualmente no navegador: login, navegação para área
protegida e logout.
