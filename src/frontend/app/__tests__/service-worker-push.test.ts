import * as fs from "fs";
import * as path from "path";

/**
 * Web Push no service worker (US #172).
 *
 * Carrega o `public/sw.js` REAL — o mesmo arquivo que vai para produção —
 * dentro de um sandbox com um `self` falso, e dispara os eventos `push` e
 * `notificationclick`. O jsdom não tem service worker, então este é o único
 * jeito de testar o código de verdade em vez de uma cópia dele.
 */

const FONTE = fs.readFileSync(path.join(__dirname, "..", "..", "public", "sw.js"), "utf8");
const ORIGEM = "https://movecity.test";

type Ouvinte = (evento: unknown) => void;

function carregarWorker(janelas: { url: string; focus?: jest.Mock; navigate?: jest.Mock }[] = []) {
  const ouvintes: Record<string, Ouvinte> = {};
  const alvo = {
    location: { origin: ORIGEM },
    addEventListener: (tipo: string, fn: Ouvinte) => {
      ouvintes[tipo] = fn;
    },
    registration: { showNotification: jest.fn().mockResolvedValue(undefined) },
    clients: {
      matchAll: jest.fn().mockResolvedValue(janelas),
      openWindow: jest.fn().mockResolvedValue(undefined),
      claim: jest.fn(),
    },
  };
  // eslint-disable-next-line no-new-func
  new Function("self", "caches", FONTE)(alvo, {});
  return { ouvintes, alvo };
}

async function dispararPush(ouvintes: Record<string, Ouvinte>, data: unknown) {
  const pendentes: Promise<unknown>[] = [];
  ouvintes.push({
    data,
    waitUntil: (p: Promise<unknown>) => pendentes.push(p),
  });
  await Promise.all(pendentes);
}

async function dispararClique(ouvintes: Record<string, Ouvinte>, dados: unknown) {
  const notificacao = { close: jest.fn(), data: dados };
  const pendentes: Promise<unknown>[] = [];
  ouvintes.notificationclick({
    notification: notificacao,
    waitUntil: (p: Promise<unknown>) => pendentes.push(p),
  });
  await Promise.all(pendentes);
  return notificacao;
}

const carga = (obj: unknown) => ({ json: () => obj });

describe("service worker — handlers registrados", () => {
  it("mantém install/activate/fetch e acrescenta push e notificationclick", () => {
    const { ouvintes } = carregarWorker();

    expect(Object.keys(ouvintes).sort()).toEqual(
      ["activate", "fetch", "install", "notificationclick", "push"].sort()
    );
  });
});

describe("service worker — evento push", () => {
  it("mostra a notificação com o texto, a tag e o destino da carga", async () => {
    const { ouvintes, alvo } = carregarWorker();

    await dispararPush(
      ouvintes,
      carga({
        titulo: "Sua parada está chegando",
        corpo: "Linha 0.110 · W3 Sul 502: chega em 3 min.",
        url: "/mapa",
        tag: "proximidade",
      })
    );

    expect(alvo.registration.showNotification).toHaveBeenCalledTimes(1);
    const [titulo, opcoes] = alvo.registration.showNotification.mock.calls[0];
    expect(titulo).toBe("Sua parada está chegando");
    expect(opcoes.body).toBe("Linha 0.110 · W3 Sul 502: chega em 3 min.");
    expect(opcoes.tag).toBe("proximidade");
    expect(opcoes.data).toEqual({ url: "/mapa" });
    expect(opcoes.icon).toBe("/icons/icon-192.png");
  });

  it.each([
    ["sem carga", null],
    ["carga que não é JSON", { json: () => { throw new SyntaxError("Unexpected token"); } }],
    ["JSON que não é objeto (texto)", carga("oi")],
    ["JSON que não é objeto (número)", carga(42)],
    ["JSON nulo", carga(null)],
    ["objeto vazio", carga({})],
    ["campos com tipo errado", carga({ titulo: 1, corpo: {}, url: [], tag: false })],
    ["campos só com espaço", carga({ titulo: "   ", corpo: "  " })],
  ])("sempre mostra UMA notificação, com textos padrão (%s)", async (_nome, data) => {
    const { ouvintes, alvo } = carregarWorker();

    await dispararPush(ouvintes, data);

    // O Chrome exige que todo push resulte numa notificação visível.
    expect(alvo.registration.showNotification).toHaveBeenCalledTimes(1);
    const [titulo, opcoes] = alvo.registration.showNotification.mock.calls[0];
    expect(titulo).toBe("Movecity");
    expect(opcoes.body).toBe("Sua parada está chegando.");
    expect(opcoes.tag).toBe("proximidade");
    expect(opcoes.data).toEqual({ url: "/mapa" });
  });

  it.each([
    ["outro domínio", "https://evil.example/phish"],
    ["protocolo relativo", "//evil.example/phish"],
    ["barra invertida", "/\\evil.example"],
    ["barra invertida no meio", "/ok\\evil"],
    ["javascript:", "javascript:alert(1)"],
    ["caminho relativo", "mapa"],
    ["controle no caminho", "/mapa\nSet-Cookie: x=1"],
    ["tipo errado", 123],
    ["vazio", ""],
  ])("destino de outro site vira /mapa (%s)", async (_nome, url) => {
    const { ouvintes, alvo } = carregarWorker();

    await dispararPush(ouvintes, carga({ titulo: "t", corpo: "c", url }));

    expect(alvo.registration.showNotification.mock.calls[0][1].data).toEqual({ url: "/mapa" });
  });

  it("aceita outro caminho interno do próprio site", async () => {
    const { ouvintes, alvo } = carregarWorker();

    await dispararPush(ouvintes, carga({ titulo: "t", corpo: "c", url: "/ocorrencias?linha=0.110" }));

    expect(alvo.registration.showNotification.mock.calls[0][1].data).toEqual({
      url: "/ocorrencias?linha=0.110",
    });
  });
});

describe("service worker — clique na notificação", () => {
  it("fecha a notificação e abre o app no mapa quando não há janela aberta", async () => {
    const { ouvintes, alvo } = carregarWorker([]);

    const notificacao = await dispararClique(ouvintes, { url: "/mapa" });

    expect(notificacao.close).toHaveBeenCalled();
    expect(alvo.clients.openWindow).toHaveBeenCalledWith(`${ORIGEM}/mapa`);
  });

  it("foca a janela do app que já está aberta, sem abrir outra", async () => {
    const janela = { url: `${ORIGEM}/mapa`, focus: jest.fn().mockResolvedValue(undefined), navigate: jest.fn() };
    const { ouvintes, alvo } = carregarWorker([janela]);

    await dispararClique(ouvintes, { url: "/mapa" });

    expect(janela.focus).toHaveBeenCalled();
    expect(janela.navigate).not.toHaveBeenCalled(); // já está no destino
    expect(alvo.clients.openWindow).not.toHaveBeenCalled();
  });

  it("foca e leva a janela aberta para o destino quando ela está em outra tela", async () => {
    const janela = {
      url: `${ORIGEM}/configuracoes`,
      focus: jest.fn().mockResolvedValue(undefined),
      navigate: jest.fn().mockResolvedValue(undefined),
    };
    const { ouvintes, alvo } = carregarWorker([janela]);

    await dispararClique(ouvintes, { url: "/mapa" });

    expect(janela.focus).toHaveBeenCalled();
    expect(janela.navigate).toHaveBeenCalledWith(`${ORIGEM}/mapa`);
    expect(alvo.clients.openWindow).not.toHaveBeenCalled();
  });

  it("ignora janelas de outra origem", async () => {
    const estranha = { url: "https://outro.site/mapa", focus: jest.fn(), navigate: jest.fn() };
    const { ouvintes, alvo } = carregarWorker([estranha]);

    await dispararClique(ouvintes, { url: "/mapa" });

    expect(estranha.focus).not.toHaveBeenCalled();
    expect(alvo.clients.openWindow).toHaveBeenCalledWith(`${ORIGEM}/mapa`);
  });

  it("se focar a janela falhar, abre uma nova", async () => {
    const quebrada = { url: `${ORIGEM}/mapa`, focus: jest.fn().mockRejectedValue(new Error("fechando")) };
    const { ouvintes, alvo } = carregarWorker([quebrada]);

    await dispararClique(ouvintes, { url: "/mapa" });

    expect(alvo.clients.openWindow).toHaveBeenCalledWith(`${ORIGEM}/mapa`);
  });

  it.each([
    ["sem dados", undefined],
    ["dados nulos", null],
    ["url de outro site", { url: "https://evil.example" }],
    ["url com protocolo relativo", { url: "//evil.example" }],
  ])("destino inválido abre /mapa (%s)", async (_nome, dados) => {
    const { ouvintes, alvo } = carregarWorker([]);

    await dispararClique(ouvintes, dados);

    expect(alvo.clients.openWindow).toHaveBeenCalledWith(`${ORIGEM}/mapa`);
  });
});
