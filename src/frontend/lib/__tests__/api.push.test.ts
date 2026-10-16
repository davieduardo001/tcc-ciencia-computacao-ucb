import {
  logoutUsuario,
  obterConfiguracaoPush,
  PushError,
  registrarInscricaoPush,
  removerInscricaoPush,
} from "../api";
import { desativarPushAoSair } from "../push";

jest.mock("../push", () => ({
  desativarPushAoSair: jest.fn().mockResolvedValue(undefined),
}));

const desativarMock = desativarPushAoSair as jest.Mock;

const INSCRICAO = {
  endpoint: "https://fcm.googleapis.com/fcm/send/abc",
  expirationTime: null,
  keys: { p256dh: "p", auth: "a" },
};

function resposta(status: number, corpo: unknown = {}) {
  return { ok: status >= 200 && status < 300, status, json: async () => corpo };
}

beforeEach(() => {
  desativarMock.mockReset().mockResolvedValue(undefined);
});

describe("obterConfiguracaoPush", () => {
  it("devolve a chave pública quando o servidor tem VAPID", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValue(resposta(200, { disponivel: true, chave_publica: "CHAVE" })) as jest.Mock;

    expect(await obterConfiguracaoPush()).toEqual({ disponivel: true, chavePublica: "CHAVE" });
    const [url, init] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toMatch(/\/api\/mobilidade\/push\/chave$/);
    expect(init.credentials).toBe("include");
  });

  it("indisponível quando o servidor diz que não tem VAPID", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValue(resposta(200, { disponivel: false, chave_publica: null })) as jest.Mock;

    expect(await obterConfiguracaoPush()).toEqual({ disponivel: false, chavePublica: null });
  });

  it("indisponível se vier 'disponivel' sem a chave", async () => {
    global.fetch = jest.fn().mockResolvedValue(resposta(200, { disponivel: true })) as jest.Mock;

    expect(await obterConfiguracaoPush()).toEqual({ disponivel: false, chavePublica: null });
  });

  it.each([401, 404, 500, 502])("nunca lança: status %s vira indisponível", async (status) => {
    global.fetch = jest.fn().mockResolvedValue(resposta(status)) as jest.Mock;

    expect(await obterConfiguracaoPush()).toEqual({ disponivel: false, chavePublica: null });
  });

  it("nunca lança: sem rede vira indisponível", async () => {
    global.fetch = jest.fn().mockRejectedValue(new TypeError("Failed to fetch")) as jest.Mock;

    expect(await obterConfiguracaoPush()).toEqual({ disponivel: false, chavePublica: null });
  });

  it("nunca lança: corpo que não é JSON vira indisponível", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => {
        throw new SyntaxError("Unexpected token");
      },
    }) as jest.Mock;

    expect(await obterConfiguracaoPush()).toEqual({ disponivel: false, chavePublica: null });
  });
});

describe("registrarInscricaoPush", () => {
  it("envia o JSON da inscrição por PUT, com a sessão", async () => {
    global.fetch = jest.fn().mockResolvedValue(resposta(200, { ativa: true })) as jest.Mock;

    await registrarInscricaoPush(INSCRICAO);

    const [url, init] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toMatch(/\/api\/mobilidade\/push\/inscricao$/);
    expect(init.method).toBe("PUT");
    expect(init.credentials).toBe("include");
    expect(JSON.parse(init.body)).toEqual(INSCRICAO);
  });

  it.each([422, 503])("%s traz a frase pronta do servidor", async (status) => {
    global.fetch = jest
      .fn()
      .mockResolvedValue(resposta(status, { detail: "Frase pronta em português." })) as jest.Mock;

    await expect(registrarInscricaoPush(INSCRICAO)).rejects.toThrow("Frase pronta em português.");
  });

  it("401 pede para entrar", async () => {
    global.fetch = jest.fn().mockResolvedValue(resposta(401)) as jest.Mock;

    await expect(registrarInscricaoPush(INSCRICAO)).rejects.toThrow("Faça login");
  });

  it("erro 500 não vaza texto técnico", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValue(resposta(500, { detail: "Traceback (most recent call last): ..." })) as jest.Mock;

    const erro = await registrarInscricaoPush(INSCRICAO).catch((e) => e);

    expect(erro).toBeInstanceOf(PushError);
    expect(erro.message).toBe("Não foi possível ativar os avisos. Tente novamente.");
    expect(erro.message).not.toMatch(/Traceback/);
  });

  it("422 sem frase legível cai no texto genérico", async () => {
    global.fetch = jest.fn().mockResolvedValue(resposta(422, { detail: [{ loc: ["body"] }] })) as jest.Mock;

    await expect(registrarInscricaoPush(INSCRICAO)).rejects.toThrow("Tente novamente");
  });

  it("sem rede", async () => {
    global.fetch = jest.fn().mockRejectedValue(new TypeError("Failed to fetch")) as jest.Mock;

    await expect(registrarInscricaoPush(INSCRICAO)).rejects.toThrow("Verifique sua conexão");
  });
});

describe("removerInscricaoPush", () => {
  it("envia o endpoint no corpo de um DELETE", async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: true, status: 204 }) as jest.Mock;

    await removerInscricaoPush(INSCRICAO.endpoint);

    const [url, init] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toMatch(/\/api\/mobilidade\/push\/inscricao$/);
    expect(init.method).toBe("DELETE");
    expect(init.credentials).toBe("include");
    expect(JSON.parse(init.body)).toEqual({ endpoint: INSCRICAO.endpoint });
    // o endpoint é identificador do aparelho: nunca na URL (iria para log de acesso)
    expect(url).not.toContain(encodeURIComponent(INSCRICAO.endpoint));
  });

  it("erro do servidor vira PushError", async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: false, status: 500 }) as jest.Mock;

    await expect(removerInscricaoPush("x")).rejects.toBeInstanceOf(PushError);
  });

  it("sem rede vira PushError", async () => {
    global.fetch = jest.fn().mockRejectedValue(new TypeError("Failed to fetch")) as jest.Mock;

    await expect(removerInscricaoPush("x")).rejects.toThrow("Verifique sua conexão");
  });
});

describe("logoutUsuario e o Web Push", () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue({ ok: true, status: 200 }) as jest.Mock;
  });

  it("tira a inscrição deste aparelho ANTES de encerrar a sessão", async () => {
    const ordem: string[] = [];
    desativarMock.mockImplementation(async () => {
      ordem.push("push");
    });
    (global.fetch as jest.Mock).mockImplementation(async (url: string) => {
      ordem.push(url.includes("/auth/logout") ? "logout" : "outro");
      return { ok: true, status: 200 };
    });

    await logoutUsuario();

    expect(ordem).toEqual(["push", "logout"]);
  });

  it("se a limpeza do push falhar, a pessoa sai da conta do mesmo jeito", async () => {
    desativarMock.mockRejectedValue(new Error("falhou"));

    await logoutUsuario();

    const chamadas = (global.fetch as jest.Mock).mock.calls.map(([url]) => url as string);
    expect(chamadas.some((url) => url.includes("/auth/logout"))).toBe(true);
  });
});
