import {
  ativarPush,
  desativarPush,
  desativarPushAoSair,
  ehIos,
  lerEstadoPush,
  rodandoComoApp,
  suportaPush,
  urlBase64ParaBytes,
} from "../push";
import {
  obterConfiguracaoPush,
  PushError,
  registrarInscricaoPush,
  removerInscricaoPush,
} from "../api";

jest.mock("../api", () => {
  class PushError extends Error {}
  return {
    PushError,
    obterConfiguracaoPush: jest.fn(),
    registrarInscricaoPush: jest.fn(),
    removerInscricaoPush: jest.fn(),
  };
});

const configMock = obterConfiguracaoPush as jest.Mock;
const registrarMock = registrarInscricaoPush as jest.Mock;
const removerMock = removerInscricaoPush as jest.Mock;

// Chave pública de teste: 65 bytes 0x04 + zeros, em base64url.
const CHAVE_BYTES = new Uint8Array(65);
CHAVE_BYTES[0] = 4;
const CHAVE_B64URL = btoa(String.fromCharCode(...CHAVE_BYTES))
  .replace(/\+/g, "-")
  .replace(/\//g, "_")
  .replace(/=+$/, "");
const OUTRA_CHAVE_BYTES = new Uint8Array(65).fill(7);

const ENDPOINT = "https://fcm.googleapis.com/fcm/send/abc123";
const UA_ANDROID = "Mozilla/5.0 (Linux; Android 14) Chrome/130 Mobile Safari/537.36";
const UA_IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605 Safari/604";

// ---------------------------------------------------------------------------
// navegador falso
// ---------------------------------------------------------------------------

function criarInscricao(chave: Uint8Array | null = CHAVE_BYTES) {
  return {
    endpoint: ENDPOINT,
    options: { applicationServerKey: chave ? chave.buffer.slice(0) : null },
    toJSON: () => ({ endpoint: ENDPOINT, keys: { p256dh: "p", auth: "a" } }),
    unsubscribe: jest.fn().mockResolvedValue(true),
  };
}

interface Cenario {
  suporte?: boolean;
  userAgent?: string;
  standalone?: boolean;
  permissao?: NotificationPermission;
  pedidoDePermissao?: NotificationPermission;
  inscricao?: ReturnType<typeof criarInscricao> | null;
  semRegistro?: boolean;
  swPronto?: boolean;
}

let ordem: string[];
let inscricaoAtual: ReturnType<typeof criarInscricao> | null;
let registro: {
  pushManager: { getSubscription: jest.Mock; subscribe: jest.Mock };
};
let serviceWorker: { getRegistration: jest.Mock; register: jest.Mock; ready: Promise<unknown> };
let notification: { permission: NotificationPermission; requestPermission: jest.Mock };

const guardados: Record<string, PropertyDescriptor | undefined> = {};

function definir(alvo: object, nome: string, valor: unknown) {
  const chave = `${(alvo as { constructor: { name: string } }).constructor.name}.${nome}`;
  if (!(chave in guardados)) guardados[chave] = Object.getOwnPropertyDescriptor(alvo, nome);
  Object.defineProperty(alvo, nome, { value: valor, configurable: true, writable: true });
}

function montarNavegador(c: Cenario = {}) {
  ordem = [];
  inscricaoAtual = c.inscricao === undefined ? null : c.inscricao;

  definir(navigator, "userAgent", c.userAgent ?? UA_ANDROID);
  definir(navigator, "standalone", c.standalone === true ? true : undefined);
  definir(window, "matchMedia", jest.fn().mockReturnValue({ matches: c.standalone === true }));

  if (c.suporte === false) {
    definir(navigator, "serviceWorker", undefined);
    delete (navigator as unknown as Record<string, unknown>).serviceWorker;
    delete (window as unknown as Record<string, unknown>).PushManager;
    delete (window as unknown as Record<string, unknown>).Notification;
    return;
  }

  const novaInscricao = criarInscricao();
  registro = {
    pushManager: {
      getSubscription: jest.fn(async () => inscricaoAtual),
      subscribe: jest.fn(async () => {
        ordem.push("subscribe");
        inscricaoAtual = novaInscricao;
        return novaInscricao;
      }),
    },
  };
  serviceWorker = {
    getRegistration: jest.fn(async () => (c.semRegistro ? undefined : registro)),
    register: jest.fn(async () => {
      ordem.push("register");
      return registro;
    }),
    ready: c.swPronto === false ? new Promise(() => {}) : Promise.resolve(registro),
  };
  notification = {
    permission: c.permissao ?? "default",
    requestPermission: jest.fn(async () => {
      ordem.push("permissao");
      return c.pedidoDePermissao ?? "granted";
    }),
  };
  definir(navigator, "serviceWorker", serviceWorker);
  definir(window, "PushManager", class {});
  definir(window, "Notification", notification);
}

beforeEach(() => {
  jest.clearAllMocks();
  configMock.mockImplementation(async () => {
    ordem.push("config");
    return { disponivel: true, chavePublica: CHAVE_B64URL };
  });
  registrarMock.mockImplementation(async () => {
    ordem.push("registrar");
  });
  removerMock.mockResolvedValue(undefined);
  montarNavegador();
});

afterEach(() => {
  jest.useRealTimers();
});

// ---------------------------------------------------------------------------

describe("detecção do ambiente", () => {
  it("reconhece iPhone e iPad pelo user agent", () => {
    montarNavegador({ userAgent: UA_IPHONE });
    expect(ehIos()).toBe(true);
    montarNavegador({ userAgent: UA_ANDROID });
    expect(ehIos()).toBe(false);
  });

  it("reconhece o app instalado pelo display-mode e pelo standalone do Safari", () => {
    montarNavegador({ standalone: false });
    expect(rodandoComoApp()).toBe(false);
    montarNavegador({ standalone: true });
    expect(rodandoComoApp()).toBe(true);
  });

  it("diz se o navegador tem service worker, push e notificações", () => {
    montarNavegador();
    expect(suportaPush()).toBe(true);
    montarNavegador({ suporte: false });
    expect(suportaPush()).toBe(false);
  });

  it("converte a chave base64url em bytes", () => {
    expect(Array.from(urlBase64ParaBytes("AQID"))).toEqual([1, 2, 3]);
    expect(Array.from(urlBase64ParaBytes("-_8"))).toEqual([0xfb, 0xff]); // alfabeto url-safe
    expect(Array.from(urlBase64ParaBytes(CHAVE_B64URL))).toEqual(Array.from(CHAVE_BYTES));
  });
});

describe("lerEstadoPush", () => {
  it("iPhone fora do app instalado pede para instalar, antes de qualquer outra checagem", async () => {
    montarNavegador({ userAgent: UA_IPHONE, standalone: false, suporte: false });

    expect(await lerEstadoPush()).toEqual({ tipo: "ios-instalar" });
    expect(configMock).not.toHaveBeenCalled();
  });

  it("iPhone com o app instalado segue o fluxo normal", async () => {
    montarNavegador({ userAgent: UA_IPHONE, standalone: true });

    expect(await lerEstadoPush()).toEqual({ tipo: "desativado" });
  });

  it("navegador sem suporte", async () => {
    montarNavegador({ suporte: false });

    expect(await lerEstadoPush()).toEqual({ tipo: "nao-suportado" });
    expect(configMock).not.toHaveBeenCalled();
  });

  it("servidor sem chaves VAPID", async () => {
    configMock.mockResolvedValue({ disponivel: false, chavePublica: null });

    expect(await lerEstadoPush()).toEqual({ tipo: "indisponivel" });
  });

  it("permissão bloqueada no navegador", async () => {
    montarNavegador({ permissao: "denied" });

    expect(await lerEstadoPush()).toEqual({ tipo: "negado" });
  });

  it("permissão concedida e aparelho inscrito = ativo", async () => {
    montarNavegador({ permissao: "granted", inscricao: criarInscricao() });

    expect(await lerEstadoPush()).toEqual({ tipo: "ativo" });
  });

  it("permissão concedida mas sem inscrição = desativado", async () => {
    montarNavegador({ permissao: "granted", inscricao: null });

    expect(await lerEstadoPush()).toEqual({ tipo: "desativado" });
  });

  it("nunca pede permissão ao ler o estado", async () => {
    montarNavegador({ permissao: "default" });

    expect(await lerEstadoPush()).toEqual({ tipo: "desativado" });
    expect(notification.requestPermission).not.toHaveBeenCalled();
  });

  it("sem registro de service worker legível, trata como desativado", async () => {
    montarNavegador({ permissao: "granted" });
    serviceWorker.getRegistration.mockRejectedValue(new Error("falhou"));

    expect(await lerEstadoPush()).toEqual({ tipo: "desativado" });
  });
});

describe("ativarPush", () => {
  it("pede a permissão ANTES de qualquer chamada ao servidor (gesto do usuário)", async () => {
    await ativarPush();

    expect(ordem[0]).toBe("permissao");
    expect(ordem.indexOf("permissao")).toBeLessThan(ordem.indexOf("config"));
  });

  it("concedida: inscreve com userVisibleOnly e a chave do servidor, registra e fica ativo", async () => {
    const estado = await ativarPush();

    expect(estado).toEqual({ tipo: "ativo" });
    const opcoes = registro.pushManager.subscribe.mock.calls[0][0];
    expect(opcoes.userVisibleOnly).toBe(true);
    expect(Array.from(opcoes.applicationServerKey as Uint8Array)).toEqual(Array.from(CHAVE_BYTES));
    expect(registrarMock).toHaveBeenCalledWith({
      endpoint: ENDPOINT,
      keys: { p256dh: "p", auth: "a" },
    });
    expect(ordem).toEqual(["permissao", "config", "subscribe", "registrar"]);
  });

  it("negada: não inscreve nem fala com o servidor", async () => {
    montarNavegador({ pedidoDePermissao: "denied" });

    expect(await ativarPush()).toEqual({ tipo: "negado" });
    expect(registro.pushManager.subscribe).not.toHaveBeenCalled();
    expect(registrarMock).not.toHaveBeenCalled();
    expect(configMock).not.toHaveBeenCalled();
  });

  it("pedido fechado sem escolher: continua desativado e não inscreve", async () => {
    montarNavegador({ pedidoDePermissao: "default" });

    expect(await ativarPush()).toEqual({ tipo: "desativado" });
    expect(registro.pushManager.subscribe).not.toHaveBeenCalled();
  });

  it("servidor sem VAPID depois da permissão: erro com texto para a tela e nada inscrito", async () => {
    configMock.mockResolvedValue({ disponivel: false, chavePublica: null });

    await expect(ativarPush()).rejects.toThrow("não estão disponíveis");
    expect(registro.pushManager.subscribe).not.toHaveBeenCalled();
  });

  it("servidor recusa a inscrição: desfaz a inscrição do navegador e repassa o erro", async () => {
    registrarMock.mockRejectedValue(new PushError("Este navegador usa um serviço que o Movecity não aceita."));

    await expect(ativarPush()).rejects.toThrow("não aceita");

    const criada = await registro.pushManager.subscribe.mock.results[0].value;
    expect(criada.unsubscribe).toHaveBeenCalled();
  });

  it("reaproveita a inscrição existente que usa a mesma chave", async () => {
    montarNavegador({ inscricao: criarInscricao(CHAVE_BYTES) });

    expect(await ativarPush()).toEqual({ tipo: "ativo" });
    expect(registro.pushManager.subscribe).not.toHaveBeenCalled();
    expect(registrarMock).toHaveBeenCalled(); // o servidor é idempotente
  });

  it("refaz a inscrição feita com outra chave pública (chaves trocadas no servidor)", async () => {
    const velha = criarInscricao(OUTRA_CHAVE_BYTES);
    montarNavegador({ inscricao: velha });

    expect(await ativarPush()).toEqual({ tipo: "ativo" });
    expect(velha.unsubscribe).toHaveBeenCalled();
    expect(registro.pushManager.subscribe).toHaveBeenCalledTimes(1);
  });

  it("registra o service worker quando ainda não há um", async () => {
    montarNavegador({ semRegistro: true });

    await ativarPush();

    expect(serviceWorker.register).toHaveBeenCalledWith("/sw.js");
  });

  it("não fica esperando para sempre um service worker que não ativa", async () => {
    montarNavegador({ swPronto: false });
    jest.useFakeTimers();

    const resultado = ativarPush();
    const esperado = expect(resultado).rejects.toThrow("Recarregue a página");
    await jest.advanceTimersByTimeAsync(5001);
    await esperado;
  });
});

describe("desativarPush", () => {
  it("remove no servidor e cancela a inscrição do navegador", async () => {
    const inscricao = criarInscricao();
    montarNavegador({ inscricao });

    expect(await desativarPush()).toEqual({ tipo: "desativado" });
    expect(removerMock).toHaveBeenCalledWith(ENDPOINT);
    expect(inscricao.unsubscribe).toHaveBeenCalled();
  });

  it("se o servidor não responder, cancela no navegador mesmo assim", async () => {
    const inscricao = criarInscricao();
    montarNavegador({ inscricao });
    removerMock.mockRejectedValue(new PushError("sem rede"));

    expect(await desativarPush()).toEqual({ tipo: "desativado" });
    expect(inscricao.unsubscribe).toHaveBeenCalled();
  });

  it("sem inscrição não chama o servidor", async () => {
    montarNavegador({ inscricao: null });

    expect(await desativarPush()).toEqual({ tipo: "desativado" });
    expect(removerMock).not.toHaveBeenCalled();
  });
});

describe("desativarPushAoSair (logout)", () => {
  it("não faz nada, nem levanta, num navegador sem suporte", async () => {
    montarNavegador({ suporte: false });

    await expect(desativarPushAoSair()).resolves.toBeUndefined();
    expect(removerMock).not.toHaveBeenCalled();
  });

  it("remove a inscrição deste aparelho no servidor e no navegador", async () => {
    const inscricao = criarInscricao();
    montarNavegador({ inscricao });

    await desativarPushAoSair();

    expect(removerMock).toHaveBeenCalledWith(ENDPOINT);
    expect(inscricao.unsubscribe).toHaveBeenCalled();
  });

  it("sem inscrição, não chama o servidor", async () => {
    montarNavegador({ inscricao: null });

    await desativarPushAoSair();

    expect(removerMock).not.toHaveBeenCalled();
  });

  it("não impede a saída se o servidor falhar", async () => {
    const inscricao = criarInscricao();
    montarNavegador({ inscricao });
    removerMock.mockRejectedValue(new PushError("sem rede"));

    await expect(desativarPushAoSair()).resolves.toBeUndefined();
    expect(inscricao.unsubscribe).toHaveBeenCalled();
  });

  it("não fica preso se o servidor não responder", async () => {
    const inscricao = criarInscricao();
    montarNavegador({ inscricao });
    removerMock.mockReturnValue(new Promise(() => {}));
    jest.useFakeTimers();

    const saida = desativarPushAoSair();
    await jest.advanceTimersByTimeAsync(3001);

    await expect(saida).resolves.toBeUndefined();
    expect(inscricao.unsubscribe).toHaveBeenCalled();
  });

  it("não levanta se ler o registro do service worker falhar", async () => {
    montarNavegador({ inscricao: criarInscricao() });
    serviceWorker.getRegistration.mockRejectedValue(new Error("falhou"));

    await expect(desativarPushAoSair()).resolves.toBeUndefined();
  });
});
