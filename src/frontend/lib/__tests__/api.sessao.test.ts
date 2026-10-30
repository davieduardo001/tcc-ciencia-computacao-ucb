import {
  fetchAutenticado,
  buscarPosicoesDaLinha,
  buscarDetalhesParada,
  buscarUsuarioAtual,
  loginUsuario,
  SessaoExpiradaError,
  LOGIN_SESSAO_EXPIRADA,
} from "../api";
import { caminhoAtual, irPara } from "../navegacao";

/**
 * Issue #221 — renovação transparente da sessão: 401 -> um POST
 * /api/auth/refresh -> repete a requisição; refresh falho -> login com aviso.
 */

function resposta(status: number, corpo: unknown = {}) {
  return { ok: status >= 200 && status < 300, status, json: async () => corpo };
}

// jsdom não deixa redefinir window.location: o redirecionamento passa por
// lib/navegacao.ts, que aqui é substituído por dublês.
jest.mock("../navegacao", () => ({
  caminhoAtual: jest.fn(),
  irPara: jest.fn(),
}));

describe("api.ts — renovação de sessão (issue #221)", () => {
  const assign = irPara as jest.Mock;

  beforeEach(() => {
    assign.mockReset();
    (caminhoAtual as jest.Mock).mockReset().mockReturnValue("/mapa");
    localStorage.clear();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it("401 seguido de refresh OK repete a chamada e devolve o resultado", async () => {
    const fetchMock = jest
      .fn()
      .mockResolvedValueOnce(resposta(401)) // original
      .mockResolvedValueOnce(resposta(200)) // refresh
      .mockResolvedValueOnce(resposta(200, { ok: true })); // repetição
    global.fetch = fetchMock as jest.Mock;

    const res = await fetchAutenticado("http://x/api/mobilidade/linhas/1", {
      credentials: "include",
    });

    expect(res.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[1][0]).toMatch(/\/api\/auth\/refresh$/);
    expect(fetchMock.mock.calls[1][1]).toMatchObject({
      method: "POST",
      credentials: "include",
    });
    expect(fetchMock.mock.calls[2][0]).toBe("http://x/api/mobilidade/linhas/1");
    expect(assign).not.toHaveBeenCalled();
  });

  it("refresh 401 limpa a sessão e redireciona ao login com aviso", async () => {
    localStorage.setItem("access_token", "a");
    localStorage.setItem("refresh_token", "r");
    const fetchMock = jest
      .fn()
      .mockResolvedValueOnce(resposta(401))
      .mockResolvedValueOnce(resposta(401));
    global.fetch = fetchMock as jest.Mock;

    const res = await fetchAutenticado("http://x/api/mobilidade/linhas/1");

    expect(res.status).toBe(401);
    expect(fetchMock).toHaveBeenCalledTimes(2); // sem repetir a original
    expect(assign).toHaveBeenCalledWith(LOGIN_SESSAO_EXPIRADA);
    expect(LOGIN_SESSAO_EXPIRADA).toContain("sessao=expirada");
    expect(localStorage.getItem("access_token")).toBeNull();
    expect(localStorage.getItem("refresh_token")).toBeNull();
  });

  it("falha de rede no refresh também leva ao login", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(resposta(401))
      .mockRejectedValueOnce(new Error("rede")) as jest.Mock;

    await fetchAutenticado("http://x/api/mobilidade/linhas/1");

    expect(assign).toHaveBeenCalledWith(LOGIN_SESSAO_EXPIRADA);
  });

  it("não redireciona quando já está numa página pública", async () => {
    (caminhoAtual as jest.Mock).mockReturnValue("/login");
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(resposta(401))
      .mockResolvedValueOnce(resposta(401)) as jest.Mock;

    await fetchAutenticado("http://x/api/mobilidade/linhas/1");

    expect(assign).not.toHaveBeenCalled();
  });

  it("requisições simultâneas com 401 disparam um único refresh", async () => {
    let liberarRefresh: (r: unknown) => void = () => {};
    const fetchMock = jest.fn((url: string) => {
      if (url.endsWith("/api/auth/refresh")) {
        return new Promise((resolve) => {
          liberarRefresh = resolve;
        });
      }
      // 1ª chamada de cada URL: 401; repetição: 200
      const chamadas = fetchMock.mock.calls.filter(([u]) => u === url).length;
      return Promise.resolve(chamadas > 1 ? resposta(200) : resposta(401));
    });
    global.fetch = fetchMock as unknown as jest.Mock;

    const todas = Promise.all([
      fetchAutenticado("http://x/a"),
      fetchAutenticado("http://x/b"),
      fetchAutenticado("http://x/c"),
    ]);
    // deixa as três originais voltarem 401 e pedirem renovação
    await new Promise((r) => setTimeout(r, 0));
    liberarRefresh(resposta(200));
    const resultados = await todas;

    const refreshes = fetchMock.mock.calls.filter(([u]) =>
      u.endsWith("/api/auth/refresh")
    );
    expect(refreshes).toHaveLength(1);
    expect(resultados.map((r) => r.status)).toEqual([200, 200, 200]);
  });

  it("depois de concluída, uma nova expiração pode renovar de novo", async () => {
    const fetchMock = jest
      .fn()
      .mockResolvedValueOnce(resposta(401))
      .mockResolvedValueOnce(resposta(200))
      .mockResolvedValueOnce(resposta(200))
      .mockResolvedValueOnce(resposta(401))
      .mockResolvedValueOnce(resposta(200))
      .mockResolvedValueOnce(resposta(200));
    global.fetch = fetchMock as jest.Mock;

    await fetchAutenticado("http://x/a");
    await fetchAutenticado("http://x/b");

    const refreshes = fetchMock.mock.calls.filter(([u]) =>
      String(u).endsWith("/api/auth/refresh")
    );
    expect(refreshes).toHaveLength(2);
  });

  it.each(["login", "registrar", "refresh", "logout", "login/google"])(
    "rota de auth /api/auth/%s com 401 não tenta renovar (sem loop)",
    async (rota) => {
      const fetchMock = jest.fn().mockResolvedValue(resposta(401));
      global.fetch = fetchMock as jest.Mock;

      const res = await fetchAutenticado(`http://x/api/auth/${rota}`, {
        method: "POST",
      });

      expect(res.status).toBe(401);
      expect(fetchMock).toHaveBeenCalledTimes(1);
      expect(assign).not.toHaveBeenCalled();
    }
  );

  it("loginUsuario com credencial errada (401) não dispara refresh", async () => {
    const fetchMock = jest
      .fn()
      .mockResolvedValue(resposta(401, { detail: "Credenciais inválidas" }));
    global.fetch = fetchMock as jest.Mock;

    await expect(
      loginUsuario({ email: "a@b.com", senha: "x" })
    ).rejects.toThrow();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("buscarUsuarioAtual sem sessão devolve null e não redireciona", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(resposta(401))
      .mockResolvedValueOnce(resposta(401)) as jest.Mock;

    await expect(buscarUsuarioAtual()).resolves.toBeNull();
    expect(assign).not.toHaveBeenCalled();
  });

  describe("401 não vira dado vazio", () => {
    it("buscarPosicoesDaLinha lança SessaoExpiradaError em vez de devolver 'nenhum ônibus'", async () => {
      global.fetch = jest.fn().mockResolvedValue(resposta(401)) as jest.Mock;

      await expect(buscarPosicoesDaLinha("0.110")).rejects.toBeInstanceOf(
        SessaoExpiradaError
      );
    });

    it("buscarPosicoesDaLinha repete após refresh e devolve os veículos", async () => {
      const fetchMock = jest
        .fn()
        .mockResolvedValueOnce(resposta(401))
        .mockResolvedValueOnce(resposta(200))
        .mockResolvedValueOnce(
          resposta(200, {
            numero: "0.110",
            veiculos: [
              {
                prefixo: "B1",
                lat: -15.8,
                lng: -48.0,
                sentido: null,
                velocidade: 10,
                direcao: 0,
                atualizado_em: "2026-10-27T09:00:00",
                operadora: "X",
                eta_minutos: null,
              },
            ],
          })
        );
      global.fetch = fetchMock as jest.Mock;

      const r = await buscarPosicoesDaLinha("0.110");

      expect(fetchMock.mock.calls[0][0]).toContain(
        "/api/mobilidade/linhas/0.110/posicoes"
      );
      expect(r.veiculos).toHaveLength(1);
    });

    it("200 com lista vazia continua sendo 'sem ônibus'", async () => {
      global.fetch = jest
        .fn()
        .mockResolvedValue(
          resposta(200, { numero: "0.110", veiculos: [] })
        ) as jest.Mock;

      const r = await buscarPosicoesDaLinha("0.110");

      expect(r.veiculos).toEqual([]);
    });

    it("erro não-auth (500) em posições segue devolvendo vazio", async () => {
      global.fetch = jest.fn().mockResolvedValue(resposta(500)) as jest.Mock;

      const r = await buscarPosicoesDaLinha("0.110");

      expect(r.veiculos).toEqual([]);
    });

    it("buscarDetalhesParada lança SessaoExpiradaError (não o erro genérico de parada)", async () => {
      global.fetch = jest.fn().mockResolvedValue(resposta(401)) as jest.Mock;

      await expect(buscarDetalhesParada(-15.8, -48.0)).rejects.toBeInstanceOf(
        SessaoExpiradaError
      );
    });
  });
});
