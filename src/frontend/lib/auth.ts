const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Usuario {
  id: string;
  nome: string;
  email: string;
  status: string;
  criado_em: string;
}

export async function login(
  email: string,
  senha: string
): Promise<{ sucesso: boolean; erro?: string }> {
  try {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email, senha }),
    });

    if (!response.ok) {
      const data = await response.json();
      return { sucesso: false, erro: data.detail || "Erro ao fazer login" };
    }

    return { sucesso: true };
  } catch {
    return { sucesso: false, erro: "Erro de conexão" };
  }
}

export async function registrar(
  nome: string,
  email: string,
  senha: string
): Promise<{ sucesso: boolean; erro?: string }> {
  try {
    const response = await fetch(`${API_URL}/auth/registrar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nome, email, senha }),
    });

    if (!response.ok) {
      const data = await response.json();
      return { sucesso: false, erro: data.detail || "Erro ao registrar" };
    }

    return { sucesso: true };
  } catch {
    return { sucesso: false, erro: "Erro de conexão" };
  }
}

export async function buscarUsuarioLogado(): Promise<Usuario | null> {
  try {
    const response = await fetch(`${API_URL}/auth/me`, {
      credentials: "include",
    });

    if (!response.ok) {
      return null;
    }

    return await response.json();
  } catch {
    return null;
  }
}

export async function renovarToken(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });

    return response.ok;
  } catch {
    return false;
  }
}

export async function logout(): Promise<void> {
  await fetch(`${API_URL}/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
}
