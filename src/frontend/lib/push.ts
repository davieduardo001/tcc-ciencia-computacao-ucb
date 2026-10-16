// Web Push no navegador — alerta de proximidade com a tela bloqueada (US #172).
//
// Este arquivo só cuida do lado do aparelho: suporte, permissão, inscrição no
// serviço de push do navegador e o estado que a tela de Configurações mostra.
// As chamadas ao servidor ficam em lib/api.ts.
//
// Regra que manda aqui: a permissão do navegador só é pedida DENTRO de um
// clique do usuário (`ativarPush`). Nenhuma função de leitura (`lerEstadoPush`)
// pede nada — pode ser chamada ao abrir a tela sem incomodar ninguém.

import {
  obterConfiguracaoPush,
  PushError,
  registrarInscricaoPush,
  removerInscricaoPush,
} from "./api";

export type EstadoPush =
  | { tipo: "carregando" }
  /** Navegador sem Service Worker, Push ou Notification. */
  | { tipo: "nao-suportado" }
  /** iPhone/iPad no Safari, fora do app instalado: o iOS só entrega push ao PWA. */
  | { tipo: "ios-instalar" }
  /** Servidor sem chaves VAPID. */
  | { tipo: "indisponivel" }
  /** A pessoa bloqueou as notificações do site no navegador. */
  | { tipo: "negado" }
  | { tipo: "desativado" }
  | { tipo: "ativo" };

// Tempo máximo esperando o service worker ficar pronto, e o servidor ao sair.
const ESPERA_SERVICE_WORKER_MS = 5000;
const ESPERA_REMOCAO_NO_LOGOUT_MS = 3000;

export function ehIos(): boolean {
  if (typeof navigator === "undefined") return false;
  if (/iPhone|iPad|iPod/.test(navigator.userAgent || "")) return true;
  // iPadOS 13+ se apresenta como Mac, mas é o único "Mac" com tela de toque.
  return navigator.platform === "MacIntel" && (navigator.maxTouchPoints ?? 0) > 1;
}

export function rodandoComoApp(): boolean {
  if (typeof window === "undefined") return false;
  const padrao =
    typeof window.matchMedia === "function" &&
    window.matchMedia("(display-mode: standalone)").matches;
  // Safari/iOS não implementa display-mode: usa a propriedade própria.
  return padrao || (navigator as Navigator & { standalone?: boolean }).standalone === true;
}

export function suportaPush(): boolean {
  return (
    typeof navigator !== "undefined" &&
    typeof window !== "undefined" &&
    "serviceWorker" in navigator &&
    "PushManager" in window &&
    "Notification" in window
  );
}

/** base64url (como o servidor entrega a chave pública) → bytes. */
export function urlBase64ParaBytes(base64Url: string) {
  const preenchido = base64Url + "=".repeat((4 - (base64Url.length % 4)) % 4);
  const base64 = preenchido.replace(/-/g, "+").replace(/_/g, "/");
  const bruto = atob(base64);
  // Sobre um ArrayBuffer explícito: `applicationServerKey` não aceita
  // SharedArrayBuffer, e o tipo inferido já diz isso ao compilador.
  const bytes = new Uint8Array(new ArrayBuffer(bruto.length));
  for (let i = 0; i < bruto.length; i++) bytes[i] = bruto.charCodeAt(i);
  return bytes;
}

function bytesIguais(a: ArrayBuffer | null, b: Uint8Array): boolean {
  if (a === null) return false;
  const x = new Uint8Array(a);
  return x.length === b.length && x.every((valor, i) => valor === b[i]);
}

function comLimite<T>(promessa: Promise<T>, ms: number, erro: string): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const relogio = setTimeout(() => reject(new PushError(erro)), ms);
    promessa.then(
      (valor) => {
        clearTimeout(relogio);
        resolve(valor);
      },
      (falha) => {
        clearTimeout(relogio);
        reject(falha);
      }
    );
  });
}

async function inscricaoAtual(): Promise<PushSubscription | null> {
  const registro = await navigator.serviceWorker.getRegistration();
  return registro ? registro.pushManager.getSubscription() : null;
}

/**
 * Estado do controle. Não pede permissão e não escreve nada: só lê.
 *
 * A ordem importa. No iPhone fora do app instalado o navegador nem expõe
 * PushManager, então "iOS sem instalar" precisa vir antes de "não suportado".
 */
export async function lerEstadoPush(): Promise<EstadoPush> {
  if (ehIos() && !rodandoComoApp()) return { tipo: "ios-instalar" };
  if (!suportaPush()) return { tipo: "nao-suportado" };

  const config = await obterConfiguracaoPush();
  if (!config.disponivel) return { tipo: "indisponivel" };

  if (Notification.permission === "denied") return { tipo: "negado" };

  try {
    const inscricao = await inscricaoAtual();
    if (Notification.permission === "granted" && inscricao) return { tipo: "ativo" };
  } catch {
    // sem registro legível: tratamos como desativado
  }
  return { tipo: "desativado" };
}

async function registroPronto(): Promise<ServiceWorkerRegistration> {
  // O registro normal acontece em RegistrarServiceWorker (só em produção).
  // Se ainda não houver, registra aqui: sem worker não há onde receber push.
  const existente = await navigator.serviceWorker.getRegistration();
  if (!existente) await navigator.serviceWorker.register("/sw.js");
  return comLimite(
    navigator.serviceWorker.ready,
    ESPERA_SERVICE_WORKER_MS,
    "Não foi possível preparar o app para os avisos. Recarregue a página e tente de novo."
  );
}

/**
 * Chamar SÓ de um clique. `Notification.requestPermission()` é a primeira
 * coisa assíncrona, antes de qualquer `fetch`: o Safari exige que ela esteja
 * ligada ao gesto do usuário e perde essa ligação se houver espera antes.
 *
 * Devolve o estado resultante. Lança PushError (com texto para a tela) se o
 * servidor recusar; nesse caso a inscrição local é desfeita, para o aparelho
 * não ficar "ativo" no navegador e desconhecido no servidor.
 */
export async function ativarPush(): Promise<EstadoPush> {
  const permissao = await Notification.requestPermission();
  if (permissao === "denied") return { tipo: "negado" };
  if (permissao !== "granted") return { tipo: "desativado" }; // fechou o pedido sem escolher

  const config = await obterConfiguracaoPush();
  if (!config.disponivel || !config.chavePublica) {
    throw new PushError("Avisos com a tela bloqueada não estão disponíveis no momento.");
  }

  const registro = await registroPronto();
  const chave = urlBase64ParaBytes(config.chavePublica);

  let inscricao = await registro.pushManager.getSubscription();
  // Inscrição feita com outra chave pública (chaves trocadas no servidor)
  // nunca receberia nada: refaz do zero.
  if (inscricao && !bytesIguais(inscricao.options.applicationServerKey, chave)) {
    await inscricao.unsubscribe();
    inscricao = null;
  }
  if (!inscricao) {
    inscricao = await registro.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: chave,
    });
  }

  try {
    await registrarInscricaoPush(inscricao.toJSON());
  } catch (erro) {
    await inscricao.unsubscribe().catch(() => {});
    throw erro;
  }
  return { tipo: "ativo" };
}

/** Desliga os avisos neste aparelho (servidor e navegador). */
export async function desativarPush(): Promise<EstadoPush> {
  const inscricao = await inscricaoAtual();
  if (inscricao) {
    // Se o servidor não responder, ainda assim cancelamos no navegador: a
    // linha que sobrar lá será apagada no primeiro 404/410 do serviço de push.
    await removerInscricaoPush(inscricao.endpoint).catch(() => {});
    await inscricao.unsubscribe().catch(() => {});
  }
  return { tipo: "desativado" };
}

/**
 * Chamada pelo logout, ANTES de a sessão acabar (a remoção no servidor
 * exige a sessão). Nunca lança e nunca demora mais que alguns segundos:
 * sair da conta não pode depender de rede nem de permissão.
 */
export async function desativarPushAoSair(): Promise<void> {
  if (!suportaPush()) return;
  try {
    const inscricao = await inscricaoAtual();
    if (!inscricao) return;
    await comLimite(
      removerInscricaoPush(inscricao.endpoint),
      ESPERA_REMOCAO_NO_LOGOUT_MS,
      "tempo esgotado"
    ).catch(() => {});
    await inscricao.unsubscribe().catch(() => {});
  } catch {
    // best-effort
  }
}
