const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ServiceStatus {
  service: string;
  status: string;
}

interface StatusAgregadoResponse {
  service: string;
  status: string;
  servicos: ServiceStatus[];
}

/**
 * Busca o status do gateway e dos serviços de domínio (auth,
 * mobilidade, colaboracao) em uma única chamada ao Gateway
 * (/api/status), o ponto único de entrada. Cada chamada aqui já
 * "acorda" serviços do Fly.io que estejam ociosos, já que qualquer
 * request HTTP dispara o auto_start_machines.
 */
export async function fetchAllServicesStatus(): Promise<ServiceStatus[]> {
  try {
    const response = await fetch(`${API_URL}/api/status`, {
      cache: "no-store",
    });
    if (!response.ok) {
      throw new Error("Erro ao buscar status dos serviços");
    }
    const data: StatusAgregadoResponse = await response.json();
    return data.servicos;
  } catch {
    return ["gateway", "auth", "mobilidade", "colaboracao"].map(
      (service) => ({ service, status: "error" })
    );
  }
}

export interface RegistroPayload {
  nome: string;
  email: string;
  senha: string;
  termosAceitos: boolean;
}

export interface RegistroResponse {
  id: string;
  nome: string;
  email: string;
  mensagem: string;
}

export class RegistroError extends Error {}

export async function registrarUsuario(
  dados: RegistroPayload
): Promise<RegistroResponse> {
  const response = await fetch(`${API_URL}/api/auth/registrar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      nome: dados.nome,
      email: dados.email,
      senha: dados.senha,
      termos_aceitos: dados.termosAceitos,
    }),
  });

  if (response.status === 409) {
    throw new RegistroError("Este e-mail já está em uso.");
  }
  if (!response.ok) {
    throw new RegistroError("Não foi possível concluir o cadastro.");
  }

  return response.json();
}

export interface LoginPayload {
  email: string;
  senha: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export class LoginError extends Error {}

export async function loginUsuario(
  dados: LoginPayload
): Promise<LoginResponse> {
  const response = await fetch(`${API_URL}/api/auth/login`, {
    credentials: "include",
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: dados.email,
      senha: dados.senha,
    }),
  });

  if (!response.ok) {
    const data = await response.json();
    throw new LoginError(data.detail || "Não foi possível realizar o login.");
  }

  const data = await response.json();

  if (data.access_token) {
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
  }

  return data;
}

export function getAccessToken(): string | null {
  return localStorage.getItem("access_token");
}

export function getRefreshToken(): string | null {
  return localStorage.getItem("refresh_token");
}

export function clearTokens(): void {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}