import { registrarUsuario, loginUsuario, buscarLinha, BuscarLinhaError } from "../api";

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
