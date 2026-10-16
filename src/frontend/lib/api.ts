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
  /** Issue #190 — `codigo` da parada física deste ponto na rota do trecho.
   * `null`/ausente quando não há parada ingerida a até 40 m (ou num backend
   * antigo): sem código não dá para pedir o tempo do ônibus. */
  parada_codigo?: string | null;
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
  /** Issue #174 — próximos horários DESTA linha (até 3). Ausente num
   * backend antigo: o painel cai de volta na lista combinada da parada. */
  proximosHorarios?: string[];
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
    linhas: (data.linhas as Record<string, unknown>[]).map(
      ({ proximos_horarios: porLinha, ...linha }) =>
        (Array.isArray(porLinha)
          ? { ...linha, proximosHorarios: porLinha }
          : linha) as unknown as LinhaNaParada
    ),
    proximosHorarios: data.proximos_horarios,
  };
}

// ---------------------------------------------------------------------------
// US #21 — Buscar parada por nome ou endereço
// ---------------------------------------------------------------------------

export interface ParadaBuscada {
  codigo: string;
  /** Vazio quando o SEMOB só traz o CEP do abrigo. */
  nome: string;
  lat: number;
  lng: number;
  qtdLinhas: number;
  /** Só na busca por endereço: metros até o lugar encontrado. */
  distanciaM: number | null;
}

export interface ResultadoBuscaParada {
  /** Qual cenário respondeu: nome (1), endereço (2) ou nenhum (3). */
  tipo: "nome" | "endereco" | "nenhum";
  paradas: ParadaBuscada[];
  /** Só na busca por endereço: o lugar em torno do qual o mapa centraliza. */
  referencia: Lugar | null;
}

export class BuscarParadasError extends Error {}

/**
 * US #21 — Paradas pelo nome ou, se nenhuma tiver esse nome, num raio de
 * 500 m do endereço/ponto de referência digitado.
 *
 * "Nada encontrado" não é erro (vem com `tipo: "nenhum"`); só falha de
 * rede ou do servidor lança BuscarParadasError — são mensagens diferentes
 * para o usuário.
 */
export async function buscarParadas(termo: string): Promise<ResultadoBuscaParada> {
  let response: Response;
  try {
    response = await fetch(
      `${API_URL}/api/mobilidade/paradas/busca?q=${encodeURIComponent(termo)}`,
      { credentials: "include", cache: "no-store" }
    );
  } catch {
    throw new BuscarParadasError("Sem conexão. Verifique a internet e tente novamente.");
  }

  if (!response.ok) {
    throw new BuscarParadasError("Não foi possível buscar paradas. Tente novamente.");
  }

  const data = await response.json();
  return {
    tipo: data.tipo,
    paradas: (data.paradas ?? []).map(
      (p: {
        codigo: string;
        nome: string;
        lat: number;
        lng: number;
        qtd_linhas: number;
        distancia_m: number | null;
      }) => ({
        codigo: p.codigo,
        nome: p.nome,
        lat: p.lat,
        lng: p.lng,
        qtdLinhas: p.qtd_linhas,
        distanciaM: p.distancia_m ?? null,
      })
    ),
    referencia: data.referencia ?? null,
  };
}

// ---------------------------------------------------------------------------
// Card #179 (⑤b) — Quando o ônibus chega NESTA parada
// ---------------------------------------------------------------------------

/** De onde veio o número: posição real do ônibus, ou saída + percurso. */
export type FonteChegada = "ao_vivo" | "previsto";

export interface ChegadaNaParada {
  numero: string;
  nome: string;
  rotaSentido: string;
  /** `null` quando não há dado (nem ônibus a caminho, nem horário). */
  etaMinutos: number | null;
  fonte: FonteChegada | null;
  /** Só `ao_vivo`. */
  prefixo: string | null;
  veiculosACaminho: number;
  /** Só `previsto`: "HH:MM" da passagem prevista nesta parada. */
  horarioPrevisto: string | null;
}

export interface ChegadasDaParada {
  paradaCodigo: string;
  paradaNome: string;
  calculadoEm: string;
  chegadas: ChegadaNaParada[];
}

/**
 * Chegadas das linhas numa parada física, pelo `codigo` (estável — ADR-14).
 *
 * Devolve `null` em qualquer falha, inclusive 404 (código que não é de uma
 * parada física conhecida): quem exibe simplesmente não mostra a seção. É um
 * extra sobre o painel da parada, que não deve quebrar nem mostrar erro por
 * causa dele — mesma postura de `buscarPosicoesDaLinha`.
 */
export async function buscarChegadasParada(
  codigo: string
): Promise<ChegadasDaParada | null> {
  try {
    const response = await fetch(
      `${API_URL}/api/mobilidade/paradas/${encodeURIComponent(codigo)}/chegadas`,
      { credentials: "include", cache: "no-store" }
    );
    if (!response.ok) return null;

    const data = await response.json();
    return {
      paradaCodigo: data.parada_codigo,
      paradaNome: data.parada_nome,
      calculadoEm: data.calculado_em,
      chegadas: (data.chegadas ?? []).map(
        (c: {
          numero: string;
          nome: string;
          rota_sentido: string;
          eta_minutos: number | null;
          fonte: FonteChegada | null;
          prefixo: string | null;
          veiculos_a_caminho: number;
          horario_previsto: string | null;
        }) => ({
          numero: c.numero,
          nome: c.nome,
          rotaSentido: c.rota_sentido,
          etaMinutos: c.eta_minutos ?? null,
          fonte: c.fonte ?? null,
          prefixo: c.prefixo ?? null,
          veiculosACaminho: c.veiculos_a_caminho ?? 0,
          horarioPrevisto: c.horario_previsto ?? null,
        })
      ),
    };
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Issue #190 — tempo do ônibus nas paradas de subir e descer de uma rota
// ---------------------------------------------------------------------------

export interface ChegadaNoPonto {
  paradaCodigo: string | null;
  /** `null` quando não há dado (nem ônibus a caminho, nem horário). */
  etaMinutos: number | null;
  fonte: FonteChegada | null;
  /** Só `ao_vivo`: o ônibus que o passageiro pegaria. */
  prefixo: string | null;
  /** Só `previsto`: "HH:MM" da passagem prevista. */
  horarioPrevisto: string | null;
}

export interface ChegadasDaPerna {
  numero: string;
  sentido: string;
  embarque: ChegadaNoPonto;
  desembarque: ChegadaNoPonto;
}

export interface ChegadasDaRota {
  calculadoEm: string;
  /** Na mesma ordem das pernas pedidas. */
  pernas: ChegadasDaPerna[];
}

export interface PernaParaChegadas {
  numero: string;
  sentido: string;
  embarqueCodigo: string | null;
  desembarqueCodigo: string | null;
}

function lerChegadaNoPonto(p: {
  parada_codigo?: string | null;
  eta_minutos?: number | null;
  fonte?: FonteChegada | null;
  prefixo?: string | null;
  horario_previsto?: string | null;
}): ChegadaNoPonto {
  return {
    paradaCodigo: p.parada_codigo ?? null,
    etaMinutos: p.eta_minutos ?? null,
    fonte: p.fonte ?? null,
    prefixo: p.prefixo ?? null,
    horarioPrevisto: p.horario_previsto ?? null,
  };
}

/**
 * Quando o ônibus de cada trecho da rota escolhida chega à parada de subir e
 * à de descer — em lote, uma chamada para a rota inteira.
 *
 * Devolve `null` em qualquer falha: é um extra sobre o resultado da rota, que
 * não deve quebrar nem mostrar erro por causa dele (mesma postura de
 * `buscarChegadasParada`). Quem chama mantém o último valor bom.
 */
export async function buscarChegadasDaRota(
  pernas: PernaParaChegadas[]
): Promise<ChegadasDaRota | null> {
  try {
    const response = await fetch(`${API_URL}/api/mobilidade/rotas/chegadas`, {
      method: "POST",
      credentials: "include",
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        pernas: pernas.map((p) => ({
          numero: p.numero,
          sentido: p.sentido,
          embarque_codigo: p.embarqueCodigo,
          desembarque_codigo: p.desembarqueCodigo,
        })),
      }),
    });
    if (!response.ok) return null;

    const data = await response.json();
    return {
      calculadoEm: data.calculado_em,
      pernas: (data.pernas ?? []).map(
        (p: {
          numero: string;
          sentido: string;
          embarque: Parameters<typeof lerChegadaNoPonto>[0];
          desembarque: Parameters<typeof lerChegadaNoPonto>[0];
        }) => ({
          numero: p.numero,
          sentido: p.sentido,
          embarque: lerChegadaNoPonto(p.embarque ?? {}),
          desembarque: lerChegadaNoPonto(p.desembarque ?? {}),
        })
      ),
    };
  } catch {
    return null;
  }
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
  /** Card #179 — parada ATÉ A QUAL o `etaMinutos` foi medido (a mais
   * próxima do usuário, no sentido deste veículo). Ausente/`null` quando
   * não havia parada ingerida por perto e o tempo veio da projeção do GPS
   * no traçado. */
  paradaCodigo?: string | null;
  paradaNome?: string | null;
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
        parada_codigo?: string | null;
        parada_nome?: string | null;
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
        paradaCodigo: v.parada_codigo ?? null,
        paradaNome: v.parada_nome ?? null,
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
// US #24 — Visualizar Ocorrências Reportadas por Outros Passageiros
// ---------------------------------------------------------------------------

export type StatusOcorrencia = "pendente" | "confirmada";

export interface OcorrenciaListada {
  id: string;
  linhaNumero: string;
  tipo: TipoOcorrencia;
  descricao: string | null;
  local: string | null;
  status: StatusOcorrencia;
  contadorConfirmacoes: number;
  criadoEm: string;
  expiraEm: string;
}

export class ListarOcorrenciasError extends Error {
  naoAutenticado: boolean;

  constructor(message: string, naoAutenticado = false) {
    super(message);
    this.naoAutenticado = naoAutenticado;
  }
}

/**
 * Lista as ocorrências ativas (não expiradas) reportadas por outros
 * passageiros, da mais recente pra mais antiga. Com `linha`, só as dela.
 *
 * `cache: "no-store"`: uma ocorrência expira em minutos — servir uma lista
 * velha do cache do navegador mostraria problemas que já passaram.
 */
export async function listarOcorrencias(linha?: string): Promise<OcorrenciaListada[]> {
  const termo = linha?.trim();
  const query = termo ? `?linha=${encodeURIComponent(termo)}` : "";

  const response = await fetch(`${API_URL}/api/colaboracao/ocorrencias${query}`, {
    credentials: "include",
    cache: "no-store",
  });

  if (response.status === 401) {
    throw new ListarOcorrenciasError("Sua sessão expirou. Faça login novamente.", true);
  }
  if (!response.ok) {
    throw new ListarOcorrenciasError("Não foi possível carregar as ocorrências.");
  }

  const lista = await response.json();
  return lista.map((item: Record<string, unknown>) => ({
    id: item.id,
    linhaNumero: item.linha_numero,
    tipo: item.tipo,
    descricao: item.descricao ?? null,
    local: item.local ?? null,
    status: item.status,
    contadorConfirmacoes: item.contador_confirmacoes,
    criadoEm: item.criado_em,
    expiraEm: item.expira_em,
  })) as OcorrenciaListada[];
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

// ---------------------------------------------------------------------------
// US #171 — Pegar o ônibus: embarcar, acompanhar e encerrar a viagem
// ---------------------------------------------------------------------------

export interface ParadaDaViagem {
  codigo: string;
  nome: string;
  lat: number;
  lng: number;
}

/**
 * US #172 — "o ônibus está chegando na sua parada", ainda não visto. O
 * servidor só devolve um aviso recente (alguns minutos) e que a pessoa ainda
 * não dispensou.
 */
export interface AvisoDeProximidade {
  id: string;
  paradaCodigo: string;
  /** `null` quando a parada não tem nome cadastrado. */
  paradaNome: string | null;
  /** ETA no instante do disparo; envelhece, por isso a tela não o exibe. */
  etaMinutos: number | null;
  disparadoEm: string;
}

export interface ViagemAtiva {
  id: string;
  numeroLinha: string;
  sentido: string | null;
  veiculoPrefixo: string;
  paradaDestinoCodigo: string | null;
  embarcouEm: string;
  /** "sem_sinal": o ônibus não está no feed ou a posição é velha — a tela
   * diz isso em vez de estimar (RN-09). */
  sinal: "ao_vivo" | "sem_sinal";
  veiculo: {
    prefixo: string;
    lat: number;
    lng: number;
    direcao: number | null;
    atualizadoEm: string;
  } | null;
  destino: (ParadaDaViagem & { ultrapassado: boolean }) | null;
  proximaParada: ParadaDaViagem | null;
  paradasRestantes: ParadaDaViagem[];
  /** US #172. Opcional: respostas de um backend antigo não trazem o campo. */
  avisoProximidade?: AvisoDeProximidade | null;
}

/** `falhou` separa "o servidor disse que não há viagem" de "não consegui
 * perguntar": no segundo caso quem chama mantém o que já mostrava. */
export type ResultadoViagemAtiva =
  | { falhou: true }
  | { falhou: false; viagem: ViagemAtiva | null };

/** `status` deixa a tela distinguir 409 (já em viagem) de 422 (sem veículo
 * perto). `message` já vem em português do servidor nesses dois casos. */
export class ViagemError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.status = status;
  }
}

function paradaDaViagem(p: {
  codigo: string;
  nome: string;
  lat: number;
  lng: number;
}): ParadaDaViagem {
  return { codigo: p.codigo, nome: p.nome, lat: p.lat, lng: p.lng };
}

/**
 * Viagem em andamento do usuário, com o progresso ao vivo. Nunca lança:
 * é uma consulta periódica de fundo e não deve quebrar a tela.
 */
export async function buscarViagemAtiva(): Promise<ResultadoViagemAtiva> {
  try {
    const response = await fetch(`${API_URL}/api/mobilidade/viagens/ativa`, {
      credentials: "include",
      cache: "no-store",
    });
    // Sem sessão não há viagem: é o estado "aguardando", não uma falha.
    if (response.status === 401) return { falhou: false, viagem: null };
    if (!response.ok) return { falhou: true };

    const data = await response.json();
    if (!data.ativa || !data.viagem) return { falhou: false, viagem: null };

    return {
      falhou: false,
      viagem: {
        id: data.viagem.id,
        numeroLinha: data.viagem.numero_linha,
        sentido: data.viagem.sentido ?? null,
        veiculoPrefixo: data.viagem.veiculo_prefixo,
        paradaDestinoCodigo: data.viagem.parada_destino_codigo ?? null,
        embarcouEm: data.viagem.embarcou_em,
        sinal: data.sinal === "ao_vivo" ? "ao_vivo" : "sem_sinal",
        veiculo: data.veiculo
          ? {
              prefixo: data.veiculo.prefixo,
              lat: data.veiculo.lat,
              lng: data.veiculo.lng,
              direcao: data.veiculo.direcao ?? null,
              atualizadoEm: data.veiculo.atualizado_em,
            }
          : null,
        destino: data.destino
          ? { ...paradaDaViagem(data.destino), ultrapassado: !!data.destino.ultrapassado }
          : null,
        proximaParada: data.proxima_parada ? paradaDaViagem(data.proxima_parada) : null,
        paradasRestantes: (data.paradas_restantes ?? []).map(paradaDaViagem),
        avisoProximidade: data.alerta_proximidade
          ? {
              id: data.alerta_proximidade.id,
              paradaCodigo: data.alerta_proximidade.parada_codigo,
              paradaNome: data.alerta_proximidade.parada_nome ?? null,
              etaMinutos: data.alerta_proximidade.eta_minutos ?? null,
              disparadoEm: data.alerta_proximidade.disparado_em,
            }
          : null,
      },
    };
  } catch {
    return { falhou: true };
  }
}

async function erroDaViagem(response: Response, padrao: string): Promise<ViagemError> {
  if (response.status === 401) {
    return new ViagemError("Faça login para registrar a viagem.", 401);
  }
  // 404/409/422 trazem uma frase pronta em português no `detail`. Qualquer
  // outra coisa (500, 502 do Gateway) não deve vazar texto técnico.
  if ([404, 409, 422].includes(response.status)) {
    try {
      const data = await response.json();
      if (typeof data.detail === "string") {
        return new ViagemError(data.detail, response.status);
      }
    } catch {
      // cai no texto padrão
    }
  }
  return new ViagemError(padrao, response.status);
}

export interface EmbarquePayload {
  numeroLinha: string;
  /** Só confirma que o usuário está perto do ônibus; o servidor não guarda. */
  lat: number;
  lng: number;
  paradaDestinoCodigo?: string;
}

/**
 * Cenários 1 e 4 — registra o embarque. Lança `ViagemError` com `status`
 * 409 (já em viagem) ou 422 (sem veículo perto / parada inválida).
 */
export async function embarcarNoOnibus(dados: EmbarquePayload): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/mobilidade/viagens`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        numero_linha: dados.numeroLinha,
        lat: dados.lat,
        lng: dados.lng,
        parada_destino_codigo: dados.paradaDestinoCodigo,
      }),
    });
  } catch {
    throw new ViagemError("Não foi possível registrar o embarque. Verifique sua conexão.");
  }
  if (!response.ok) {
    throw await erroDaViagem(response, "Não foi possível registrar o embarque. Tente novamente.");
  }
}

/** Escolhe, troca ou tira (`null`) a parada de destino da viagem. */
export async function definirDestinoDaViagem(
  viagemId: string,
  paradaDestinoCodigo: string | null
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(
      `${API_URL}/api/mobilidade/viagens/${encodeURIComponent(viagemId)}/destino`,
      {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ parada_destino_codigo: paradaDestinoCodigo }),
      }
    );
  } catch {
    throw new ViagemError("Não foi possível salvar o destino. Verifique sua conexão.");
  }
  if (!response.ok) {
    throw await erroDaViagem(response, "Não foi possível salvar o destino. Tente novamente.");
  }
}

/** Cenário 3 — "Cheguei". Idempotente no servidor: repetir não dá erro. */
export async function encerrarViagem(viagemId: string): Promise<void> {
  let response: Response;
  try {
    response = await fetch(
      `${API_URL}/api/mobilidade/viagens/${encodeURIComponent(viagemId)}/encerrar`,
      { method: "POST", credentials: "include" }
    );
  } catch {
    throw new ViagemError("Não foi possível encerrar a viagem. Verifique sua conexão.");
  }
  // 404 = a viagem já não existe para este usuário (expirou, ou foi
  // encerrada em outro aparelho): o objetivo de quem tocou em "Cheguei"
  // está cumprido, então não é erro.
  if (!response.ok && response.status !== 404) {
    throw await erroDaViagem(response, "Não foi possível encerrar a viagem. Tente novamente.");
  }
}

/**
 * US #172 — avisa o servidor que a pessoa viu o aviso de proximidade, para
 * ele não voltar nas próximas consultas. Nunca lança: o aviso já saiu da tela
 * e, se a confirmação se perder, o pior caso é ele reaparecer depois de
 * recarregar a página (a tela também o esconde localmente).
 */
export async function confirmarAvisoDeProximidade(viagemId: string): Promise<void> {
  try {
    await fetch(
      `${API_URL}/api/mobilidade/viagens/${encodeURIComponent(viagemId)}/alerta-proximidade/visto`,
      { method: "POST", credentials: "include" }
    );
  } catch {
    // sem rede: ver o comentário acima
  }
}
