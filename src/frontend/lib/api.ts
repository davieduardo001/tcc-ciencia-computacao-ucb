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

/**
 * Encerra a sessão: chama o Gateway (que limpa os cookies httpOnly e
 * repassa pro Auth Service revogar a sessão) e limpa os tokens locais.
 * Sempre limpa o estado local, mesmo se a chamada ao Gateway falhar —
 * logout nunca deve travar o usuário do lado de fora por causa de um
 * erro de rede.
 */
export async function logoutUsuario(): Promise<void> {
  try {
    await fetch(`${API_URL}/api/auth/logout`, {
      method: "POST",
      credentials: "include",
    });
  } finally {
    clearTokens();
  }
}

export interface ParadaLinha {
  nome: string;
  lat: number;
  lng: number;
}

export interface LinhaDetalhada {
  numero: string;
  nome: string;
  sentido: string;
  paradas: ParadaLinha[];
  trajeto: [number, number][];
  horariosPrevistos: string[];
}

export class BuscarLinhaError extends Error {}

export interface LinhaResumo {
  numero: string;
  nome: string;
  sentido: string;
}

/**
 * US #17 — Autocomplete: sugere linhas por número, nome ou destino
 * (ex: digitar "Ceilândia" sugere as linhas que passam por lá).
 * Termo vazio lista todas as linhas conhecidas.
 *
 * Nunca lança exceção — é só uma sugestão, uma falha aqui não deve
 * travar a busca principal (ver buscarLinha). Retorna [] em qualquer
 * erro.
 */
export async function sugerirLinhas(termo: string): Promise<LinhaResumo[]> {
  try {
    const response = await fetch(
      `${API_URL}/api/mobilidade/linhas?q=${encodeURIComponent(termo)}`,
      { credentials: "include", cache: "no-store" }
    );
    if (!response.ok) return [];
    return await response.json();
  } catch {
    return [];
  }
}

// ---------------------------------------------------------------------------
// US #20 — Rota de origem até destino
// ---------------------------------------------------------------------------

export interface Lugar {
  nome: string;
  endereco: string;
  lat: number;
  lng: number;
}

export interface PontoEmbarque {
  lat: number;
  lng: number;
  /** Vazio quando não há parada cadastrada perto — a UI mostra o ponto no mapa. */
  parada_nome: string;
  caminhada_metros: number;
}

export interface PernaViagem {
  numero: string;
  sentido: string;
  nome: string;
  embarque: PontoEmbarque;
  desembarque: PontoEmbarque;
  distancia_km: number;
  paradas_no_trecho: number;
  trajeto: [number, number][];
}

export interface OpcaoViagem {
  pernas: PernaViagem[];
  baldeacoes: number;
  distancia_km: number;
  caminhada_metros: number;
  duracao_estimada_min: number;
}

/**
 * US #20 — Autocomplete de origem/destino por ponto de referência
 * ("Rodoviária", "UnB", "Shopping Taguatinga").
 *
 * Existe porque os nomes de parada do SEMOB são endereços de rua, que
 * ninguém digita. Resolvido no backend via OpenStreetMap/Nominatim.
 *
 * Nunca lança: sem geocodificação o usuário ainda tem "usar minha
 * localização" e o clique no mapa.
 */
export async function buscarLugares(termo: string): Promise<Lugar[]> {
  try {
    const response = await fetch(
      `${API_URL}/api/mobilidade/lugares?q=${encodeURIComponent(termo)}`,
      { credentials: "include", cache: "no-store" }
    );
    if (!response.ok) return [];
    return await response.json();
  } catch {
    return [];
  }
}

/**
 * US #20 — Nome legível de um ponto, pra "usar minha localização" e pro
 * clique no mapa não deixarem o campo mostrando coordenada crua.
 * Retorna null quando o ponto não tem nome conhecido.
 */
export async function nomearLugar(
  lat: number,
  lng: number
): Promise<Lugar | null> {
  try {
    const response = await fetch(
      `${API_URL}/api/mobilidade/lugares/reverso?lat=${lat}&lng=${lng}`,
      { credentials: "include", cache: "no-store" }
    );
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

export class CalcularRotaError extends Error {}

/**
 * US #20 — Opções de viagem entre dois pontos, diretas primeiro e com
 * uma baldeação quando não há linha direta.
 *
 * Lista vazia é resposta válida (Cenário 3 da US: nenhuma rota
 * disponível), não erro. Falha de rede/servidor lança CalcularRotaError
 * — aqui, diferente do autocomplete, o usuário precisa saber que não
 * deu certo.
 */
export async function calcularRotas(
  origem: { lat: number; lng: number },
  destino: { lat: number; lng: number }
): Promise<OpcaoViagem[]> {
  const params = new URLSearchParams({
    origem_lat: String(origem.lat),
    origem_lng: String(origem.lng),
    destino_lat: String(destino.lat),
    destino_lng: String(destino.lng),
  });

  const response = await fetch(`${API_URL}/api/mobilidade/rotas?${params}`, {
    credentials: "include",
    cache: "no-store",
  });

  if (!response.ok) {
    throw new CalcularRotaError(
      "Não foi possível calcular a rota. Tente novamente."
    );
  }

  return response.json();
}

/**
 * US #17 — Busca os detalhes de uma linha (trajeto, paradas, sentido)
 * pra desenhar no mapa. Usa o mesmo endpoint da US #15
 * (GET /api/mobilidade/linhas/{numero}, via Gateway).
 *
 * Retorna null quando a linha não é encontrada (404 — cenário 2 da
 * US #15/#17), sem lançar exceção nesse caso. Outras falhas (rede,
 * 401/500) lançam BuscarLinhaError.
 */
export async function buscarLinha(
  numero: string
): Promise<LinhaDetalhada | null> {
  const response = await fetch(
    `${API_URL}/api/mobilidade/linhas/${encodeURIComponent(numero)}`,
    { credentials: "include", cache: "no-store" }
  );

  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new BuscarLinhaError("Não foi possível buscar a linha. Tente novamente.");
  }

  const data = await response.json();
  return {
    numero: data.numero,
    nome: data.nome,
    sentido: data.sentido,
    paradas: data.paradas,
    trajeto: data.trajeto,
    horariosPrevistos: data.horarios_previstos,
  };
}
export interface VeiculoAoVivo {
  /** Número da linha que o veículo está fazendo. Necessário porque o
   * mapa rastreia várias linhas ao mesmo tempo quando o usuário escolhe
   * um itinerário com baldeação (US #20). */
  linha: string;
  prefixo: string;
  lat: number;
  lng: number;
  sentido: string | null;
  velocidade: number | null;
  atualizadoEm: string;
  operadora: string;
}

/**
 * US #16 — posição ao vivo dos ônibus de uma linha, do feed de GPS do
 * SEMOB (a mesma fonte do app oficial DF no Ponto).
 *
 * Lista vazia é situação normal: significa que nenhum veículo dessa
 * linha está reportando posição agora (Cenário 3 da US). Falha de rede
 * também devolve lista vazia — o trajeto continua no mapa, só sem os
 * ônibus; não faz sentido derrubar a tela por causa disso.
 */
export async function buscarPosicoesDaLinha(
  numero: string
): Promise<VeiculoAoVivo[]> {
  try {
    const response = await fetch(
      `${API_URL}/api/mobilidade/linhas/${encodeURIComponent(numero)}/posicoes`,
      { credentials: "include", cache: "no-store" }
    );
    if (!response.ok) return [];

    const data = await response.json();
    return (data.veiculos ?? []).map(
      (v: {
        prefixo: string;
        lat: number;
        lng: number;
        sentido: string | null;
        velocidade: number | null;
        atualizado_em: string;
        operadora: string;
      }) => ({
        linha: data.numero ?? numero,
        prefixo: v.prefixo,
        lat: v.lat,
        lng: v.lng,
        sentido: v.sentido,
        velocidade: v.velocidade,
        atualizadoEm: v.atualizado_em,
        operadora: v.operadora,
      })
    );
  } catch {
    return [];
  }
}
