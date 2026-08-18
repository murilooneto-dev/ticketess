const FIELD_LABELS_PT = {
  username: "Nome de usuário",
  password: "Senha",
  name: "Nome",
  email: "E-mail",
  role: "Papel",
  title: "Título",
  project_id: "Projeto",
  github_repo: "Repositório GitHub",
  github_token: "Token do GitHub",
  period_start: "Início do período",
  period_end: "Fim do período",
};

function fieldLabel(loc) {
  const field = Array.isArray(loc) ? loc[loc.length - 1] : loc;
  return FIELD_LABELS_PT[field] || field;
}

/**
 * Extrai uma mensagem de erro legível do "detail" de uma resposta da API.
 * O FastAPI retorna `detail` como string em erros de negócio (404, 409...)
 * mas como uma lista de objetos {loc, msg} em erros de validação (422).
 */
export function extractErrorMessage(detail, fallback) {
  if (typeof detail === "string" && detail) {
    return detail;
  }
  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item) => {
        if (item && typeof item === "object" && item.msg) {
          return item.loc ? `${fieldLabel(item.loc)}: ${item.msg}` : item.msg;
        }
        return String(item);
      })
      .join("; ");
  }
  return fallback;
}

export async function handleApiResponse(response) {
  if (!response.ok) {
    let detail = null;
    try {
      const body = await response.json();
      detail = body.detail;
    } catch {
      // corpo sem JSON, mantém mensagem padrão
    }
    throw new Error(extractErrorMessage(detail, `Erro ${response.status}`));
  }
  return response.json();
}
