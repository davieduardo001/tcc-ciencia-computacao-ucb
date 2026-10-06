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


export interface RecuperacaoSenhaResponse {
  mensagem: string;
}

export class RecuperacaoSenhaError extends Error {}

export async function solicitarResetSenha(
  email: string
): Promise<RecuperacaoSenhaResponse> {
  const response = await fetch(`${API_URL}/api/auth/esqueci-senha`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });

  const data = await response.json().catch(() => ({}));

  if (response.status === 429) {
    throw new RecuperacaoSenhaError(
      "Muitas solicitações. Tente novamente mais tarde."
    );
  }

  if (!response.ok) {
    throw new RecuperacaoSenhaError(
      data.detail || "Não foi possível solicitar a recuperação de senha."
    );
  }

  return data;
}


export interface RedefinirSenhaPayload {
  token: string;
  novaSenha: string;
  confirmacaoSenha: string;
}

export async function redefinirSenha(
  dados: RedefinirSenhaPayload
): Promise<RecuperacaoSenhaResponse> {
  const response = await fetch(`${API_URL}/api/auth/redefinir-senha`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      token: dados.token,
      nova_senha: dados.novaSenha,
      confirmacao_senha: dados.confirmacaoSenha,
    }),
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new RecuperacaoSenhaError(
      data.detail || "Não foi possível redefinir a senha."
    );
  }

  return data;
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
  firstAccess: boolean;
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
      firstAccess: data.first_access ?? true,
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
    // US #25 — limpa o cache local de favoritos ao sair.
    try { localStorage.removeItem("movecity:favoritos"); } catch { /* best-effort */ }
  }
}

/**
 * Atualiza a flag first_access do usuário logado.
 * Usado para pular ou rever o tutorial de onboarding.
 */
export async function atualizarFirstAccess(firstAccess: boolean): Promise<void> {
  const response = await fetch(`${API_URL}/api/auth/me/first-access`, {
    method: "PUT",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ first_access: firstAccess }),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || "Não foi possível atualizar preferência do tutorial.");
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
  /** US #159 — minutos estimados até embarcar nesta perna. `undefined`
   * num backend antigo (o campo é novo e opcional); `null` quando o
   * backend não conseguiu estimar. */
  espera_min?: number | null;
  fonte_espera?: "tempo_real" | "intervalo_medio" | "teorica";
  /** Só vem preenchido quando `fonte_espera === "tempo_real"`. */
  prefixo_veiculo?: string | null;
  /** Só vem preenchido quando `fonte_espera === "intervalo_medio"`. */
  intervalo_medio_min?: number | null;
}

export interface OpcaoViagem {
  pernas: PernaViagem[];
  baldeacoes: number;
  distancia_km: number;
  caminhada_metros: number;
  duracao_estimada_min: number;
  /** US #159 — ETA real da viagem inteira, calculado a partir da
   * posição ao vivo dos ônibus. `null`/ausente quando não há ônibus
   * identificável — nesse caso use `duracao_estimada_min`. */
  duracao_real_min?: number | null;
  tipo_estimativa?: "tempo_real" | "parcial" | "teorica";
  calculado_em?: string | null;
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

// ---------------------------------------------------------------------------
// US #18 — Detalhes de uma parada
// ---------------------------------------------------------------------------

export interface LinhaNaParada {
  numero: string;
  nome: string;
  sentido: string;
}

export interface DetalhesParada {
  nome: string;
  codigo: string;
  lat: number;
  lng: number;
  linhas: LinhaNaParada[];
  /** Cenário 2 da US #18: vazio quando não há horário previsto — o
   * painel mostra um aviso em vez de uma lista vazia sem explicação. */
  proximosHorarios: string[];
}

export class BuscarParadaError extends Error {}

/**
 * US #18 — Detalhes de uma parada: nome, código, linhas que passam por
 * ela e os próximos horários previstos.
 *
 * Retorna null quando nenhuma linha cacheada tem parada perto da
 * coordenada (404) — não deveria acontecer ao clicar num marcador que o
 * próprio mapa desenhou, mas o painel trata isso como "sem dados" em vez
 * de quebrar. Outras falhas lançam BuscarParadaError.
 */
export async function buscarDetalhesParada(
  lat: number,
  lng: number
): Promise<DetalhesParada | null> {
  const response = await fetch(
    `${API_URL}/api/mobilidade/paradas?lat=${lat}&lng=${lng}`,
    { credentials: "include", cache: "no-store" }
  );

  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new BuscarParadaError(
      "Não foi possível carregar os detalhes da parada. Tente novamente."
    );
  }

  const data = await response.json();
  return {
    nome: data.nome,
    codigo: data.codigo,
    lat: data.lat,
    lng: data.lng,
    linhas: data.linhas,
    proximosHorarios: data.proximos_horarios,
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
  /** Rumo em graus (0 = norte), pra apontar o ícone na direção da viagem. */
  direcao: number | null;
  atualizadoEm: string;
  operadora: string;
  /** US #19 — minutos até chegar na posição do usuário. `null` quando não
   * informamos localização, ou quando o veículo está parado/sem
   * velocidade confiável (Cenário 5: pílula sem tempo). */
  etaMinutos: number | null;
}

/** US #19 — resultado de uma busca de posições, com o fallback do Cenário 3. */
export interface PosicoesDaLinha {
  veiculos: VeiculoAoVivo[];
  /** Só preenchido quando `veiculos` está vazio e a localização do
   * usuário foi informada: próximo horário previsto da tabela teórica. */
  proximoHorarioPrevisto: string | null;
}

/**
 * US #16 — posição ao vivo dos ônibus de uma linha, do feed de GPS do
 * SEMOB (a mesma fonte do app oficial DF no Ponto).
 * US #19 — quando `coordenadasUsuario` é informado, cada veículo vem
 * com `etaMinutos` calculado até essa posição.
 *
 * Lista vazia é situação normal: significa que nenhum veículo dessa
 * linha está reportando posição agora (Cenário 3 da US #16). Falha de
 * rede também devolve lista vazia — o trajeto continua no mapa, só sem
 * os ônibus; não faz sentido derrubar a tela por causa disso.
 */
export async function buscarPosicoesDaLinha(
  numero: string,
  coordenadasUsuario?: { lat: number; lng: number } | null
): Promise<PosicoesDaLinha> {
  const vazio: PosicoesDaLinha = { veiculos: [], proximoHorarioPrevisto: null };
  try {
    const params = coordenadasUsuario
      ? `?lat=${coordenadasUsuario.lat}&lng=${coordenadasUsuario.lng}`
      : "";
    const response = await fetch(
      `${API_URL}/api/mobilidade/linhas/${encodeURIComponent(numero)}/posicoes${params}`,
      { credentials: "include", cache: "no-store" }
    );
    if (!response.ok) return vazio;

    const data = await response.json();
    const veiculos: VeiculoAoVivo[] = (data.veiculos ?? []).map(
      (v: {
        prefixo: string;
        lat: number;
        lng: number;
        sentido: string | null;
        velocidade: number | null;
        direcao: number | null;
        atualizado_em: string;
        operadora: string;
        eta_minutos: number | null;
      }) => ({
        linha: data.numero ?? numero,
        prefixo: v.prefixo,
        lat: v.lat,
        lng: v.lng,
        sentido: v.sentido,
        velocidade: v.velocidade,
        direcao: v.direcao ?? null,
        atualizadoEm: v.atualizado_em,
        operadora: v.operadora,
        etaMinutos: v.eta_minutos ?? null,
      })
    );

    return {
      veiculos,
      proximoHorarioPrevisto: data.proximo_horario_previsto ?? null,
    };
  } catch {
    return vazio;
  }
}

// ---------------------------------------------------------------------------
// US #23 — Reportar Ocorrência em uma Linha
// ---------------------------------------------------------------------------

export type TipoOcorrencia =
  | "atraso"
  | "nao_passou"
  | "lotacao"
  | "obra_via"
  | "onibus_quebrou"
  | "acidente"
  | "seguranca";

export interface OcorrenciaPayload {
  linhaNumero: string;
  tipo: TipoOcorrencia;
  descricao?: string;
  local?: string;
  lat?: number;
  lng?: number;
}

export interface OcorrenciaRegistrada {
  id: string;
  linhaNumero: string;
  tipo: TipoOcorrencia;
  status: string;
  contadorConfirmacoes: number;
  criadoEm: string;
  expiraEm: string;
}

export class ReportarOcorrenciaError extends Error {
  resetEm?: string;

  constructor(message: string, resetEm?: string) {
    super(message);
    this.resetEm = resetEm;
  }
}

export async function reportarOcorrencia(
  dados: OcorrenciaPayload
): Promise<OcorrenciaRegistrada> {
  const response = await fetch(`${API_URL}/api/colaboracao/ocorrencias`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      linha_numero: dados.linhaNumero,
      tipo: dados.tipo,
      descricao: dados.descricao,
      local: dados.local,
      lat: dados.lat,
      lng: dados.lng,
    }),
  });

  if (response.status === 401) {
    throw new ReportarOcorrenciaError("Faça login para reportar uma ocorrência.");
  }
  if (response.status === 429) {
    const data = await response.json();
    throw new ReportarOcorrenciaError(
      "Você atingiu o limite de reportes. Tente novamente mais tarde.",
      data.detail?.reset_em
    );
  }
  if (!response.ok) {
    throw new ReportarOcorrenciaError("Não foi possível registrar o reporte.");
  }

  const data = await response.json();
  return {
    id: data.id,
    linhaNumero: data.linha_numero,
    tipo: data.tipo,
    status: data.status,
    contadorConfirmacoes: data.contador_confirmacoes,
    criadoEm: data.criado_em,
    expiraEm: data.expira_em,
  };
}


// ---------------------------------------------------------------------------
// US #25 — Salvar e Visualizar Rota Favorita
// ---------------------------------------------------------------------------

export interface RotaFavorita {
  id: string;
  usuario_id: string;
  numero_linha: string;
  nome_linha: string;
  label: string;
  origem_lat: number;
  origem_lng: number;
  destino_lat: number;
  destino_lng: number;
  criado_em: string;
}

export interface RotaFavoritaPayload {
  numero_linha: string;
  nome_linha: string;
  label: string;
  origem_lat: number;
  origem_lng: number;
  destino_lat: number;
  destino_lng: number;
}

export class SalvarFavoritoError extends Error {
  /** HTTP status retornado pelo servidor, quando disponível. */
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.status = status;
  }
}

// Chave do localStorage — prefixo "movecity:" para evitar colisão.
const CACHE_FAVORITOS_KEY = "movecity:favoritos";

/** Persiste a lista de favoritos no localStorage para acesso offline. */
export function cachearFavoritos(lista: RotaFavorita[]): void {
  try {
    localStorage.setItem(CACHE_FAVORITOS_KEY, JSON.stringify(lista));
  } catch {
    // localStorage pode estar indisponível (modo privado, storage cheio).
    // Falha silenciosa — o cache é best-effort.
  }
}

/** Lê favoritos do cache local. Retorna [] em qualquer erro de parse. */
export function lerFavoritosCache(): RotaFavorita[] {
  try {
    const raw = localStorage.getItem(CACHE_FAVORITOS_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as RotaFavorita[];
  } catch {
    return [];
  }
}

/** Remove o cache local de favoritos (chamado no logout). */
export function limparCacheFavoritos(): void {
  try {
    localStorage.removeItem(CACHE_FAVORITOS_KEY);
  } catch {
    // Falha silenciosa.
  }
}

/**
 * US #25 — Salva uma rota calculada como favorita.
 *
 * Lança `SalvarFavoritoError` em caso de falha — o frontend precisa saber
 * o motivo para exibir o feedback correto (limite, duplicata, não autenticado).
 */
export async function salvarFavorito(
  dados: RotaFavoritaPayload
): Promise<RotaFavorita> {
  const response = await fetch(`${API_URL}/api/colaboracao/favoritos`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      numero_linha: dados.numero_linha,
      nome_linha: dados.nome_linha,
      label: dados.label,
      origem_lat: dados.origem_lat,
      origem_lng: dados.origem_lng,
      destino_lat: dados.destino_lat,
      destino_lng: dados.destino_lng,
    }),
  });

  if (response.status === 401) {
    throw new SalvarFavoritoError("Faça login para salvar rotas favoritas.", 401);
  }
  if (response.status === 409) {
    throw new SalvarFavoritoError("Esta rota já está nos seus favoritos.", 409);
  }
  if (response.status === 422) {
    const data = await response.json().catch(() => ({}));
    const detalhe = data.detail ?? "";
    if (detalhe === "limite_favoritos_atingido") {
      throw new SalvarFavoritoError(
        "Você atingiu o limite de 20 rotas favoritas. Remova uma para salvar esta.",
        422
      );
    }
    throw new SalvarFavoritoError("Dados inválidos. Verifique os campos.", 422);
  }
  if (!response.ok) {
    throw new SalvarFavoritoError(
      "Não foi possível salvar o favorito. Tente novamente."
    );
  }

  return response.json();
}

/**
 * US #25 — Busca as favoritas direto do servidor. Lança em qualquer falha
 * (rede fora, 5xx) para o chamador saber que NÃO são dados frescos.
 *
 * Em 401 o cache é apagado e a lista vem vazia: a sessão acabou, e o cache
 * não é por usuário — mostrá-lo exporia as rotas de quem usou o aparelho antes.
 */
export async function listarFavoritosRemoto(): Promise<RotaFavorita[]> {
  const response = await fetch(`${API_URL}/api/colaboracao/favoritos`, {
    credentials: "include",
    cache: "no-store",
  });
  if (response.status === 401) {
    limparCacheFavoritos();
    return [];
  }
  if (!response.ok) {
    throw new Error(`Falha ao listar favoritos (${response.status}).`);
  }
  const lista: RotaFavorita[] = await response.json();
  cachearFavoritos(lista);
  return lista;
}

/**
 * US #25 — Lista as rotas favoritas do usuário autenticado.
 *
 * Nunca lança exceção: falha de rede ou do servidor retorna o cache local.
 * Quem precisa saber se os dados são frescos usa `listarFavoritosRemoto`.
 */
export async function listarFavoritos(): Promise<RotaFavorita[]> {
  try {
    return await listarFavoritosRemoto();
  } catch {
    return lerFavoritosCache();
  }
}

/**
 * US #25 — Remove uma rota favorita pelo ID.
 *
 * Lança erro em caso de falha (403, 404, rede).
 */
export async function removerFavorito(id: string): Promise<void> {
  const response = await fetch(
    `${API_URL}/api/colaboracao/favoritos/${encodeURIComponent(id)}`,
    {
      method: "DELETE",
      credentials: "include",
    }
  );

  if (response.status === 403) {
    throw new SalvarFavoritoError(
      "Você não tem permissão para remover este favorito.",
      403
    );
  }
  if (response.status === 404) {
    throw new SalvarFavoritoError("Favorito não encontrado.", 404);
  }
  if (!response.ok) {
    throw new SalvarFavoritoError(
      "Não foi possível remover o favorito. Tente novamente."
    );
  }
  // 204 No Content — sem corpo.
}
