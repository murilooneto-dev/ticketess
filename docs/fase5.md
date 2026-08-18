# DevControl — Fase 5

## O que foi implementado

- Modelo `Notification` (destinatário, tipo, título, mensagem, link
  opcional para a página relevante, lida/não lida).
- Gatilhos automáticos de notificação:
  - **Ticket criado** → notifica todos os administradores (exceto quem
    abriu, se for admin).
  - **Ticket atualizado** (status/prioridade/tipo, feito pelo admin) →
    notifica o autor da solicitação, com resumo do que mudou (ex.:
    "Status: Aberto → Em andamento").
  - **Novo comentário** → se quem comentou foi o autor da solicitação,
    notifica os admins; se foi o admin, notifica o autor da solicitação.
  - **Novo andamento em projeto** → notifica o gestor responsável pelo
    projeto (quando definido).
- Envio de e-mail opcional (best-effort, via `smtplib` da biblioteca
  padrão): só é acionado se `SMTP_ENABLED=true` no `.env`; falhas de envio
  são registradas em log e não interrompem a requisição. Continua
  desativado por padrão, como já estava preparado desde a Fase 1.
- Endpoints:
  - `GET /api/notifications` — lista as notificações do usuário logado
    (aceita `?unread_only=true`).
  - `GET /api/notifications/unread-count` — contador de não lidas.
  - `POST /api/notifications/{id}/read` — marca uma notificação como
    lida (só o próprio dono pode marcar).
  - `POST /api/notifications/read-all` — marca todas como lidas.
- Frontend: sino de notificações na barra de navegação, com contador de
  não lidas (atualizado a cada 30s), dropdown com a lista, marcação
  automática como lida ao clicar (navegando para o link relacionado) e
  botão "marcar todas como lidas".

## Testes

52 testes automatizados (`pytest -q`), incluindo 10 novos para
notificações: criação de ticket notifica admins (e não notifica o
próprio autor), atualização de status notifica o autor, comentários
notificam a parte correta em cada direção, andamento de projeto notifica
o gestor, contagem de não lidas, marcar como lida (individual e em
massa), proteção contra marcar notificação de outro usuário como lida, e
confirmação de que nenhum e-mail é enviado com `SMTP_ENABLED=false`.

Testado manualmente no navegador: como gestor, abri uma solicitação de
bug; logado como admin, o sino mostrou contador "1", o dropdown exibiu a
notificação correta, e o clique navegou para o ticket e zerou o
contador.
