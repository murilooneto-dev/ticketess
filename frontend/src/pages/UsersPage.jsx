import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { createUserAccount, fetchUsers, updateUserAccount } from "../services/users.js";

const ROLE_LABELS = {
  admin: "Administrador",
  gestor: "Gestor",
  operador: "Operador",
};

const ROLE_OPTIONS = [
  { value: "operador", label: "Operador (só vê as próprias solicitações)" },
  { value: "gestor", label: "Gestor (vê todas as solicitações)" },
  { value: "admin", label: "Administrador" },
];

export default function UsersPage() {
  const queryClient = useQueryClient();

  const [name, setName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("operador");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [passwordEdits, setPasswordEdits] = useState({});
  const [rowErrors, setRowErrors] = useState({});

  const { data: users, isLoading } = useQuery({ queryKey: ["users"], queryFn: fetchUsers });

  async function handleCreate(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await createUserAccount({ name, username, password, role });
      setName("");
      setUsername("");
      setPassword("");
      setRole("operador");
      queryClient.invalidateQueries({ queryKey: ["users"] });
    } catch (err) {
      setError(err.message || "Não foi possível criar o usuário.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRoleChange(userId, newRole) {
    await updateUserAccount(userId, { role: newRole });
    queryClient.invalidateQueries({ queryKey: ["users"] });
  }

  async function handleToggleActive(user) {
    await updateUserAccount(user.id, { is_active: !user.is_active });
    queryClient.invalidateQueries({ queryKey: ["users"] });
  }

  async function handleChangePassword(userId) {
    const newPassword = passwordEdits[userId];
    if (!newPassword) return;
    setRowErrors((prev) => ({ ...prev, [userId]: "" }));
    try {
      await updateUserAccount(userId, { password: newPassword });
      setPasswordEdits((prev) => ({ ...prev, [userId]: "" }));
    } catch (err) {
      setRowErrors((prev) => ({ ...prev, [userId]: err.message || "Não foi possível trocar a senha." }));
    }
  }

  return (
    <main className="page">
      <h1>Usuários</h1>

      <form className="form" onSubmit={handleCreate}>
        <label htmlFor="name">Nome completo</label>
        <input id="name" value={name} onChange={(e) => setName(e.target.value)} required autoFocus />

        <label htmlFor="username">Nome de usuário</label>
        <input
          id="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="ex.: joao.silva"
          required
        />

        <label htmlFor="password">Senha</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="new-password"
          required
        />

        <label htmlFor="role">Papel</label>
        <select id="role" value={role} onChange={(e) => setRole(e.target.value)}>
          {ROLE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        {error && <p className="error">{error}</p>}

        <button type="submit" disabled={submitting}>
          {submitting ? "Criando..." : "Criar usuário"}
        </button>
      </form>

      {isLoading && <p>Carregando usuários...</p>}

      {users && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Nome</th>
              <th>Usuário</th>
              <th>Papel</th>
              <th>Status</th>
              <th>Nova senha</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.name}</td>
                <td>{u.username}</td>
                <td>
                  <select value={u.role} onChange={(e) => handleRoleChange(u.id, e.target.value)}>
                    {ROLE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {ROLE_LABELS[option.value]}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <button type="button" onClick={() => handleToggleActive(u)}>
                    {u.is_active ? "Ativo — desativar" : "Inativo — ativar"}
                  </button>
                </td>
                <td>
                  <div className="page-actions">
                    <input
                      type="password"
                      placeholder="Nova senha"
                      value={passwordEdits[u.id] || ""}
                      onChange={(e) => setPasswordEdits((prev) => ({ ...prev, [u.id]: e.target.value }))}
                    />
                    <button type="button" onClick={() => handleChangePassword(u.id)}>
                      Salvar
                    </button>
                  </div>
                  {rowErrors[u.id] && <p className="error">{rowErrors[u.id]}</p>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
