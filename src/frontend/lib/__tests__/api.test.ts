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
  buscarPosicoesDaLinha,
  solicitarResetSenha,
  redefinirSenha,
} from "../api";

/**
 * Regressão: o front-end já bateu em /auth/registro e /auth/login
 * (sem o prefixo /api, e "registro" em vez de "registrar") — paths do Gateway
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
        {
          numero: "0.108",
          nome: "0.108 — Ceilândia / Plano Piloto",
          sentido: "Ceilândia → Plano Piloto",
        },
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

describe("api.ts — posição ao vivo (US #16)", () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  it("chama /api/mobilidade/linhas/{numero}/posicoes e converte o payload", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        numero: "0.620",
        veiculos: [
          {
            prefixo: "122190",
            lat: -15.60806,
            lng: -47.69308,
            sentido: "VOLTA",
            velocidade: 8.06,
            atualizado_em: "2026-09-13T22:13:40",
            operadora: "VIAÇÃO PIRACICABANA - BACIA 01",
            eta_minutos: null,
          },
        ],
      }),
    }) as jest.Mock;

    const { veiculos, proximoHorarioPrevisto } = await buscarPosicoesDaLinha(
      "0.620"
    );

    const [url, options] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toMatch(/\/api\/mobilidade\/linhas\/0\.620\/posicoes$/);
    expect(options.credentials).toBe("include");
    expect(veiculos).toHaveLength(1);
    expect(veiculos[0].prefixo).toBe("122190");
    expect(veiculos[0].atualizadoEm).toBe("2026-09-13T22:13:40");
    expect(veiculos[0].velocidade).toBe(8.06);
    expect(veiculos[0].etaMinutos).toBeNull();
    expect(proximoHorarioPrevisto).toBeNull();
  });

  it("US #19 — informa lat/lng do usuário e devolve eta_minutos por veículo", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        numero: "0.620",
        veiculos: [
          {
            prefixo: "122190",
            lat: -15.60806,
            lng: -47.69308,
            sentido: "VOLTA",
            velocidade: 8.06,
            atualizado_em: "2026-09-13T22:13:40",
            operadora: "VIAÇÃO PIRACICABANA - BACIA 01",
            eta_minutos: 4.2,
          },
        ],
      }),
    }) as jest.Mock;

    const { veiculos } = await buscarPosicoesDaLinha("0.620", {
      lat: -15.6,
      lng: -47.69,
    });

    const [url] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toContain("lat=-15.6");
    expect(url).toContain("lng=-47.69");
    expect(veiculos[0].etaMinutos).toBe(4.2);
  });

  it("US #19, Cenário 3 — sem veículo, devolve o próximo horário previsto", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        numero: "0.110",
        veiculos: [],
        proximo_horario_previsto: "06:20",
      }),
    }) as jest.Mock;

    const resultado = await buscarPosicoesDaLinha("0.110", {
      lat: -15.8,
      lng: -48.05,
    });

    expect(resultado.veiculos).toEqual([]);
    expect(resultado.proximoHorarioPrevisto).toBe("06:20");
  });

  it("lista vazia é normal — nenhum ônibus em operação (Cenário 3)", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ numero: "0.110", veiculos: [] }),
    }) as jest.Mock;

    await expect(buscarPosicoesDaLinha("0.110")).resolves.toEqual({
      veiculos: [],
      proximoHorarioPrevisto: null,
    });
  });

  it("falha de rede não derruba a tela — devolve lista vazia", async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error("rede fora")) as jest.Mock;

    await expect(buscarPosicoesDaLinha("0.110")).resolves.toEqual({
      veiculos: [],
      proximoHorarioPrevisto: null,
    });
  });
});

describe("api.ts — recuperação de senha (US #133)", () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  it("solicitarResetSenha chama /api/auth/esqueci-senha", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        mensagem:
          "Se o e-mail estiver cadastrado, voce recebera um link de redefinicao.",
      }),
    }) as jest.Mock;

    const resultado = await solicitarResetSenha("teste@example.com");

    const [url, options] = (global.fetch as jest.Mock).mock.calls[0];

    expect(url).toMatch(/\/api\/auth\/esqueci-senha$/);
    expect(options.method).toBe("POST");
    expect(options.headers["Content-Type"]).toBe("application/json");
    expect(JSON.parse(options.body)).toEqual({
      email: "teste@example.com",
    });
    expect(resultado.mensagem).toContain("Se o e-mail estiver cadastrado");
  });

  it("solicitarResetSenha mostra mensagem amigável quando recebe 429", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 429,
      json: async () => ({
        detail: "Muitas solicitações.",
      }),
    }) as jest.Mock;

    await expect(
      solicitarResetSenha("teste@example.com")
    ).rejects.toThrow("Muitas solicitações. Tente novamente mais tarde.");
  });

  it("redefinirSenha chama /api/auth/redefinir-senha com os dados corretos", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        mensagem: "Senha redefinida com sucesso.",
      }),
    }) as jest.Mock;

    const resultado = await redefinirSenha({
      token: "token-de-teste",
      novaSenha: "NovaSenha123!",
      confirmacaoSenha: "NovaSenha123!",
    });

    const [url, options] = (global.fetch as jest.Mock).mock.calls[0];

    expect(url).toMatch(/\/api\/auth\/redefinir-senha$/);
    expect(options.method).toBe("POST");
    expect(options.headers["Content-Type"]).toBe("application/json");
    expect(JSON.parse(options.body)).toEqual({
      token: "token-de-teste",
      nova_senha: "NovaSenha123!",
      confirmacao_senha: "NovaSenha123!",
    });
    expect(resultado.mensagem).toBe("Senha redefinida com sucesso.");
  });

  it("redefinirSenha transforma erro do backend em RecuperacaoSenhaError", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({
        detail: "Este link nao e mais valido ou expirou.",
      }),
    }) as jest.Mock;

    await expect(
      redefinirSenha({
        token: "token-invalido",
        novaSenha: "NovaSenha123!",
        confirmacaoSenha: "NovaSenha123!",
      })
    ).rejects.toThrow("Este link nao e mais valido ou expirou.");
  });
});


// ---------------------------------------------------------------------------
// US #25 — Salvar e Visualizar Rota Favorita
// ---------------------------------------------------------------------------

import {
  salvarFavorito,
  listarFavoritos,
  removerFavorito,
  SalvarFavoritoError,
  cachearFavoritos,
  lerFavoritosCache,
  limparCacheFavoritos,
} from "../api";

const PAYLOAD_FAVORITO = {
  numero_linha: "0.110",
  nome_linha: "0.110 — Taguatinga / Rodoviária",
  label: "Casa → Trabalho",
  origem_lat: -15.8305,
  origem_lng: -48.0425,
  destino_lat: -15.7939,
  destino_lng: -47.8828,
};

const FAVORITO_RESPONSE = {
  id: "uuid-teste",
  usuario_id: "uuid-usuario",
  ...PAYLOAD_FAVORITO,
  criado_em: "2026-10-05T14:30:00",
};

describe("api.ts — salvarFavorito (US #25)", () => {
  afterEach(() => jest.resetAllMocks());

  it("chama POST /api/colaboracao/favoritos com credentials include", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => FAVORITO_RESPONSE,
    }) as jest.Mock;

    const resultado = await salvarFavorito(PAYLOAD_FAVORITO);

    const [url, options] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toMatch(/\/api\/colaboracao\/favoritos$/);
    expect(options.method).toBe("POST");
    expect(options.credentials).toBe("include");
    expect(resultado.id).toBe("uuid-teste");
    expect(resultado.label).toBe("Casa → Trabalho");
  });

  it("lança SalvarFavoritoError com status 401 quando não autenticado", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Não autenticado" }),
    }) as jest.Mock;

    await expect(salvarFavorito(PAYLOAD_FAVORITO)).rejects.toThrow(
      SalvarFavoritoError
    );
    await expect(salvarFavorito(PAYLOAD_FAVORITO)).rejects.toMatchObject({
      status: 401,
    });
  });

  it("lança SalvarFavoritoError com status 409 quando rota já favoritada", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({ detail: "rota_ja_favoritada" }),
    }) as jest.Mock;

    await expect(salvarFavorito(PAYLOAD_FAVORITO)).rejects.toMatchObject({
      status: 409,
      message: expect.stringContaining("já está"),
    });
  });

  it("lança SalvarFavoritoError com status 422 quando limite atingido", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({ detail: "limite_favoritos_atingido" }),
    }) as jest.Mock;

    await expect(salvarFavorito(PAYLOAD_FAVORITO)).rejects.toMatchObject({
      status: 422,
      message: expect.stringContaining("limite"),
    });
  });
});

describe("api.ts — listarFavoritos (US #25)", () => {
  afterEach(() => {
    jest.resetAllMocks();
    limparCacheFavoritos();
  });

  it("chama GET /api/colaboracao/favoritos com credentials include", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [FAVORITO_RESPONSE],
    }) as jest.Mock;

    const lista = await listarFavoritos();

    const [url, options] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toMatch(/\/api\/colaboracao\/favoritos$/);
    expect(options.credentials).toBe("include");
    expect(lista).toHaveLength(1);
    expect(lista[0].id).toBe("uuid-teste");
  });

  it("retorna [] quando a lista está vazia", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [],
    }) as jest.Mock;

    const lista = await listarFavoritos();
    expect(lista).toEqual([]);
  });

  it("retorna cache local quando a requisição falha (offline)", async () => {
    cachearFavoritos([FAVORITO_RESPONSE]);
    global.fetch = jest.fn().mockRejectedValue(new Error("rede fora")) as jest.Mock;

    const lista = await listarFavoritos();
    expect(lista).toHaveLength(1);
    expect(lista[0].id).toBe("uuid-teste");
  });

  it("atualiza o cache local quando o servidor responde com sucesso", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [FAVORITO_RESPONSE],
    }) as jest.Mock;

    await listarFavoritos();
    const cache = lerFavoritosCache();
    expect(cache).toHaveLength(1);
    expect(cache[0].id).toBe("uuid-teste");
  });
});

describe("api.ts — removerFavorito (US #25)", () => {
  afterEach(() => jest.resetAllMocks());

  it("chama DELETE /api/colaboracao/favoritos/{id} com credentials include", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 204,
      json: async () => ({}),
    }) as jest.Mock;

    await removerFavorito("uuid-teste");

    const [url, options] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toMatch(/\/api\/colaboracao\/favoritos\/uuid-teste$/);
    expect(options.method).toBe("DELETE");
    expect(options.credentials).toBe("include");
  });

  it("lança SalvarFavoritoError com status 403 para favorito alheio", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({ detail: "Acesso negado" }),
    }) as jest.Mock;

    await expect(removerFavorito("uuid-alheio")).rejects.toMatchObject({
      status: 403,
    });
  });

  it("lança SalvarFavoritoError com status 404 para favorito inexistente", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: "Não encontrado" }),
    }) as jest.Mock;

    await expect(removerFavorito("uuid-inexistente")).rejects.toMatchObject({
      status: 404,
    });
  });
});

describe("api.ts — cache de favoritos (US #25)", () => {
  afterEach(() => limparCacheFavoritos());

  it("cachearFavoritos persiste no localStorage", () => {
    cachearFavoritos([FAVORITO_RESPONSE]);
    const raw = localStorage.getItem("movecity:favoritos");
    expect(raw).not.toBeNull();
    expect(JSON.parse(raw!)[0].id).toBe("uuid-teste");
  });

  it("lerFavoritosCache retorna os dados salvos", () => {
    cachearFavoritos([FAVORITO_RESPONSE]);
    const cache = lerFavoritosCache();
    expect(cache).toHaveLength(1);
    expect(cache[0].label).toBe("Casa → Trabalho");
  });

  it("lerFavoritosCache retorna [] quando chave ausente", () => {
    expect(lerFavoritosCache()).toEqual([]);
  });

  it("lerFavoritosCache retorna [] quando JSON corrompido, sem lançar erro", () => {
    localStorage.setItem("movecity:favoritos", "{ json corrompido ]");
    expect(lerFavoritosCache()).toEqual([]);
  });

  it("limparCacheFavoritos remove a chave do localStorage", () => {
    cachearFavoritos([FAVORITO_RESPONSE]);
    limparCacheFavoritos();
    expect(localStorage.getItem("movecity:favoritos")).toBeNull();
  });
});
