import { registrarUsuario, loginUsuario } from "../api";

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
