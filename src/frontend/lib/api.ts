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

export interface GoogleLoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  account_linking_pending: boolean;
  account_linking_required: boolean;
}

export class GoogleLoginError extends Error {}

function armazenarTokensSeExistirem(data: {
  access_token?: string;
  refresh_token?: string;
}): void {
  if (data.access_token) {
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token ?? "");
  }
}

/**
 * Login via Google: envia o id_token (JWT) obtido do Google Identity
 * Services. Se o e-mail já pertencer a uma conta local com senha, o
 * backend não retorna tokens — retorna account_linking_required: true
 * pra que o front peça confirmação antes de vincular (ver
 * confirmarVinculoGoogle).
 */
export async function loginComGoogle(
  idToken: string
): Promise<GoogleLoginResponse> {
  const response = await fetch(`${API_URL}/api/auth/login/google`, {
    credentials: "include",
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id_token: idToken }),
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new GoogleLoginError(
      data.detail || "Não foi possível entrar com o Google."
    );
  }

  armazenarTokensSeExistirem(data);

  return data;
}

export interface ConfirmarVinculoGooglePayload {
  idToken: string;
  email: string;
  googleId: string;
}

/** Confirma a vinculação de uma conta local existente com o Google. */
export async function confirmarVinculoGoogle(
  dados: ConfirmarVinculoGooglePayload
): Promise<GoogleLoginResponse> {
  const response = await fetch(`${API_URL}/api/auth/link-google/confirmar`, {
    credentials: "include",
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      id_token: dados.idToken,
      email: dados.email,
      google_id: dados.googleId,
    }),
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new GoogleLoginError(
      data.detail || "Não foi possível confirmar o vínculo com o Google."
    );
  }

  armazenarTokensSeExistirem(data);

  return data;
}

/**
 * Decodifica (sem validar assinatura) o payload de um id_token JWT do
 * Google, só pra extrair email/sub e mostrar a tela de confirmação de
 * vínculo. A validação de verdade sempre acontece no Auth Service.
 */
export function decodificarIdTokenGoogle(idToken: string): {
  email?: string;
  sub?: string;
} {
  try {
    const payload = idToken.split(".")[1];
    const normalizado = payload.replace(/-/g, "+").replace(/_/g, "/");
    const json = decodeURIComponent(
      atob(normalizado)
        .split("")
        .map((c) => "%" + c.charCodeAt(0).toString(16).padStart(2, "0"))
        .join("")
    );
    return JSON.parse(json);
  } catch {
    return {};
  }
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

export interface UsuarioAtual {
  id: string;
  nome: string;
  email: string;
  avatarUrl: string | null;
}

/**
 * Busca os dados do usuário autenticado (sessão via cookie httpOnly
 * setado pelo Gateway no login). Retorna null quando não há sessão
 * válida — nunca lança exceção, para uso simples em componentes que
 * só precisam exibir "logado" vs "visitante".
 */
export async function buscarUsuarioAtual(): Promise<UsuarioAtual | null> {
  try {
    const response = await fetch(`${API_URL}/api/auth/me`, {
      credentials: "include",
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    return {
      id: data.id,
      nome: data.nome,
      email: data.email,
      avatarUrl: data.avatar_url ?? null,
    };
  } catch {
    return null;
  }
}