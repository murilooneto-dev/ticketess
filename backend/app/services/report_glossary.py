from app.models.ticket import Ticket, TicketPriority, TicketStatus, TicketType

TICKET_TYPE_PLAIN = {
    TicketType.NOVA_FUNCIONALIDADE: "a implementação de um novo recurso",
    TicketType.ALTERACAO: "uma alteração solicitada no sistema",
    TicketType.MELHORIA: "uma melhoria no sistema",
    TicketType.BUG: "a correção de um problema",
    TicketType.SUPORTE: "um atendimento de suporte",
    TicketType.OUTRO: "uma solicitação",
}

TICKET_STATUS_PLAIN = {
    TicketStatus.ABERTO: "em fila para análise",
    TicketStatus.EM_ANDAMENTO: "em desenvolvimento",
    TicketStatus.AGUARDANDO: "aguardando retorno de alguém",
    TicketStatus.CONCLUIDO: "concluída",
    TicketStatus.CANCELADO: "cancelada",
}

TICKET_PRIORITY_PLAIN = {
    TicketPriority.BAIXA: "prioridade baixa",
    TicketPriority.MEDIA: "prioridade normal",
    TicketPriority.ALTA: "prioridade alta",
    TicketPriority.URGENTE: "prioridade urgente",
}


def describe_ticket_opened_plain(ticket: Ticket) -> str:
    kind = TICKET_TYPE_PLAIN.get(ticket.type, "uma solicitação")
    priority = TICKET_PRIORITY_PLAIN.get(ticket.priority, "")
    return f'Foi aberta uma solicitação para {kind}: "{ticket.title}" ({priority}).'


def describe_ticket_resolved_plain(ticket: Ticket) -> str:
    kind = TICKET_TYPE_PLAIN.get(ticket.type, "uma solicitação")
    status = TICKET_STATUS_PLAIN.get(ticket.status, ticket.status.value)
    return f'Está {status}: {kind} — "{ticket.title}".'


def describe_ticket_opened_technical(ticket: Ticket) -> str:
    return f"#{ticket.id} [{ticket.type.value}/{ticket.priority.value}] {ticket.title} (status atual: {ticket.status.value})"


def describe_ticket_resolved_technical(ticket: Ticket) -> str:
    return f"#{ticket.id} [{ticket.type.value}] {ticket.title} (status final: {ticket.status.value})"


def describe_pull_request_plain(pull_request) -> str:
    if pull_request.state == "merged":
        return f'Uma alteração relacionada a "{pull_request.title}" foi revisada e incorporada ao sistema.'
    if pull_request.state == "closed":
        return f'Uma proposta de alteração ("{pull_request.title}") foi encerrada sem ser incorporada.'
    return f'Uma alteração está em revisão: "{pull_request.title}".'


def describe_commits_plain(count: int) -> str:
    if count == 0:
        return "Nenhuma alteração de código registrada no período."
    if count == 1:
        return "Foi registrada 1 alteração no código do sistema."
    return f"Foram registradas {count} alterações no código do sistema."
