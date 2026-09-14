import {
  registrarUsuario,
  loginUsuario,
  buscarLinha,
  BuscarLinhaError,
  sugerirLinhas,
  buscarLugares,
  calcularRotas,
  CalcularRotaError,
  nomearLugar,
} from "../api";

/**
 * Regressão: o front-end já bateu em /auth/registro e /auth/login
 * (sem o prefixo /api, e "registro" em vez de "registrar") — paths
 * que não existem no Gateway (só /api/auth/registrar e /api/auth/login
 * são roteados/públicos). Isso travava CORS + 401 em produção.
 */
describe("api.ts — paths do Gateway", () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        id: "1",
        nome: "Teste",
        email: "teste@example.com",
        mensagem: "ok",
        access_token: "a",
        refresh_token: "b",
        token_type: "bearer",
      }),
    }) as jest.Mock;
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it("registrarUsuario chama /api/auth/registrar", async () => {
    await registrarUsuario({
      nome: "Teste",
      email: "teste@example.com",
      senha: "senha123",
      termosAceitos: true,
    });

    const [url] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toMatch(/\/api\/auth\/registrar$/);
  });

  it("loginUsuario chama /api/auth/login com credentials include", async () => {
    await loginUsuario({ email: "teste@example.com", senha: "senha123" });

    const [url, options] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toMatch(/\/api\/auth\/login$/);
    expect(options.credentials).toBe("include");
  });
});

describe("api.ts — buscarLinha (US #17)", () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  it("chama /api/mobilidade/linhas/{numero} com credentials include", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        numero: "0.110",
        nome: "0.110 — Taguatinga",
        sentido: "Taguatinga → Rodoviária",
        paradas: [{ nome: "Parada A", lat: -15.8, lng: -48.0 }],
        trajeto: [[-15.8, -48.0], [-15.79, -47.9]],
        horarios_previstos: ["06:00"],
      }),
    }) as jest.Mock;

    const resultado = await buscarLinha("0.110");

    const [url, options] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toMatch(/\/api\/mobilidade\/linhas\/0\.110$/);
    expect(options.credentials).toBe("include");
    expect(resultado?.horariosPrevistos).toEqual(["06:00"]);
    expect(resultado?.trajeto).toEqual([[-15.8, -48.0], [-15.79, -47.9]]);
  });

  it("retorna null quando a linha não é encontrada (404)", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: "Linha não encontrada." }),
    }) as jest.Mock;

    const resultado = await buscarLinha("9.999");

    expect(resultado).toBeNull();
  });

  it("lança BuscarLinhaError em outras falhas (ex: 401/500)", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({}),
    }) as jest.Mock;

    await expect(buscarLinha("0.110")).rejects.toThrow(BuscarLinhaError);
  });
});

describe("api.ts — sugerirLinhas (autocomplete, US #17)", () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  it("chama /api/mobilidade/linhas?q= com o termo digitado", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [
        { numero: "0.108", nome: "0.108 — Ceilândia / Plano Piloto", sentido: "Ceilândia → Plano Piloto" },
      ],
    }) as jest.Mock;

    const resultado = await sugerirLinhas("ceilandia");

    const [url, options] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toMatch(/\/api\/mobilidade\/linhas\?q=ceilandia$/);
    expect(options.credentials).toBe("include");
    expect(resultado).toHaveLength(1);
    expect(resultado[0].numero).toBe("0.108");
  });

  it("nunca lança exceção — retorna [] em qualquer falha", async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error("rede fora")) as jest.Mock;

    const resultado = await sugerirLinhas("0.110");

    expect(resultado).toEqual([]);
  });

  it("retorna [] quando a resposta não é ok", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({}),
    }) as jest.Mock;

    const resultado = await sugerirLinhas("0.110");

    expect(resultado).toEqual([]);
  });
});

describe("api.ts — rota origem → destino (US #20)", () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  it("calcularRotas manda as quatro coordenadas como query params", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [],
    }) as jest.Mock;

    await calcularRotas(
      { lat: -15.8195, lng: -48.1096 },
      { lat: -15.7939, lng: -47.8828 }
    );

    const [url, options] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toContain("/api/mobilidade/rotas?");
    expect(url).toContain("origem_lat=-15.8195");
    expect(url).toContain("origem_lng=-48.1096");
    expect(url).toContain("destino_lat=-15.7939");
    expect(url).toContain("destino_lng=-47.8828");
    expect(options.credentials).toBe("include");
  });

  it("lista vazia é resposta válida, não erro (Cenário 3 da US)", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [],
    }) as jest.Mock;

    await expect(
      calcularRotas({ lat: -15.8, lng: -48.1 }, { lat: -15.7, lng: -47.8 })
    ).resolves.toEqual([]);
  });

  it("falha do servidor lança CalcularRotaError", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({}),
    }) as jest.Mock;

    await expect(
      calcularRotas({ lat: -15.8, lng: -48.1 }, { lat: -15.7, lng: -47.8 })
    ).rejects.toThrow(CalcularRotaError);
  });

  it("devolve as pernas da viagem com embarque e desembarque", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [
        {
          pernas: [
            {
              numero: "0.382",
              sentido: "IDA",
              nome: "0.382 — Ceilândia / Rodoviária",
              embarque: {
                lat: -15.81,
                lng: -48.1,
                parada_nome: "Avenida Hélio Prates, Ceilândia",
                caminhada_metros: 119,
              },
              desembarque: {
                lat: -15.79,
                lng: -47.88,
                parada_nome: "Eixo L Central, Setor Bancário Sul",
                caminhada_metros: 58,
              },
              distancia_km: 27,
              paradas_no_trecho: 33,
              trajeto: [
                [-15.81, -48.1],
                [-15.79, -47.88],
              ],
            },
          ],
          baldeacoes: 0,
          distancia_km: 27,
          caminhada_metros: 177,
          duracao_estimada_min: 76,
        },
      ],
    }) as jest.Mock;

    const opcoes = await calcularRotas(
      { lat: -15.8195, lng: -48.1096 },
      { lat: -15.7939, lng: -47.8828 }
    );

    expect(opcoes).toHaveLength(1);
    expect(opcoes[0].baldeacoes).toBe(0);
    expect(opcoes[0].pernas[0].numero).toBe("0.382");
    expect(opcoes[0].pernas[0].embarque.parada_nome).toBe(
      "Avenida Hélio Prates, Ceilândia"
    );
  });

  it("buscarLugares nunca lança — geocodificação é best-effort", async () => {
    global.fetch = jest
      .fn()
      .mockRejectedValue(new Error("nominatim fora")) as jest.Mock;

    await expect(buscarLugares("rodoviaria")).resolves.toEqual([]);
  });

  it("nomearLugar devolve null quando o ponto não tem nome", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({}),
    }) as jest.Mock;

    await expect(nomearLugar(-15.8, -48.1)).resolves.toBeNull();
  });
});
