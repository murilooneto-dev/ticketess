export const TYPE_LABELS = {
  nova_funcionalidade: "Nova funcionalidade",
  alteracao: "Alteração",
  melhoria: "Melhoria",
  bug: "Correção de bug",
  suporte: "Suporte",
  outro: "Outro",
};

export const TYPE_OPTIONS = Object.entries(TYPE_LABELS).map(([value, label]) => ({ value, label }));

export const PRIORITY_LABELS = {
  baixa: "Baixa",
  media: "Média",
  alta: "Alta",
  urgente: "Urgente",
};

export const PRIORITY_OPTIONS = Object.entries(PRIORITY_LABELS).map(([value, label]) => ({ value, label }));

export const STATUS_LABELS = {
  aberto: "Aberto",
  em_andamento: "Em andamento",
  aguardando: "Aguardando",
  concluido: "Concluído",
  cancelado: "Cancelado",
};

export const STATUS_OPTIONS = Object.entries(STATUS_LABELS).map(([value, label]) => ({ value, label }));

export const FIELD_LABELS = {
  status: "Status",
  priority: "Prioridade",
  type: "Tipo",
};

export function historyValueLabel(field, value) {
  if (value === null || value === undefined) return "—";
  if (field === "status") return STATUS_LABELS[value] || value;
  if (field === "priority") return PRIORITY_LABELS[value] || value;
  if (field === "type") return TYPE_LABELS[value] || value;
  return value;
}
