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
  buscarChegadasParada,
  buscarChegadasDaRota,
  buscarViagemAtiva,
  definirDestinoDaViagem,
  embarcarNoOnibus,
  encerrarViagem,
  ViagemError,
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

describe("api.ts — parada de referência do ETA (card #179)", () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  function respostaComVeiculo(extra: Record<string, unknown>) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        numero: "0.110",
        veiculos: [
          {
            prefixo: "440001",
            lat: -15.8,
            lng: -48.0,
            sentido: "IDA",
            velocidade: 30,
            atualizado_em: "2026-10-14T12:00:00",
            operadora: "VIAÇÃO TESTE",
            eta_minutos: 4.3,
            ...extra,
          },
        ],
      }),
    };
  }

  it("traz a parada até a qual o ETA foi medido", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValue(respostaComVeiculo({ parada_codigo: "PR-12345", parada_nome: "W3 Sul 502" })) as jest.Mock;

    const { veiculos } = await buscarPosicoesDaLinha("0.110", { lat: -15.8, lng: -47.9 });

    expect(veiculos[0].paradaCodigo).toBe("PR-12345");
    expect(veiculos[0].paradaNome).toBe("W3 Sul 502");
    expect(veiculos[0].etaMinutos).toBe(4.3);
  });

  it("backend antigo, sem os campos novos, continua funcionando", async () => {
    global.fetch = jest.fn().mockResolvedValue(respostaComVeiculo({})) as jest.Mock;

    const { veiculos } = await buscarPosicoesDaLinha("0.110");

    expect(veiculos[0].paradaCodigo).toBeNull();
    expect(veiculos[0].paradaNome).toBeNull();
  });
});

describe("api.ts — chegadas numa parada (card #179, ⑤b)", () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  const PAYLOAD = {
    parada_codigo: "PR-12345",
    parada_nome: "W3 Sul 502",
    calculado_em: "2026-10-14T15:00:00+00:00",
    chegadas: [
      {
        numero: "0.110",
        nome: "0.110 — Taguatinga",
        rota_sentido: "IDA",
        eta_minutos: 4.3,
        fonte: "ao_vivo",
        prefixo: "440001",
        veiculos_a_caminho: 2,
        horario_previsto: null,
      },
      {
        numero: "875A",
        nome: "875A — Perdizes",
        rota_sentido: "VOLTA",
        eta_minutos: 17.6,
        fonte: "previsto",
        prefixo: null,
        veiculos_a_caminho: 0,
        horario_previsto: "15:18",
      },
      {
        numero: "106.2",
        nome: "106.2",
        rota_sentido: "IDA",
        eta_minutos: null,
        fonte: null,
      },
    ],
  };

  it("chama o endpoint da parada pelo CÓDIGO (estável), com sessão e sem cache", async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: true, status: 200, json: async () => PAYLOAD }) as jest.Mock;

    await buscarChegadasParada("PR-12345");

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/mobilidade\/paradas\/PR-12345\/chegadas$/),
      expect.objectContaining({ credentials: "include", cache: "no-store" })
    );
  });

  it("codifica o código na URL", async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: true, status: 200, json: async () => PAYLOAD }) as jest.Mock;

    await buscarChegadasParada("PR 1/2");

    expect((global.fetch as jest.Mock).mock.calls[0][0]).toContain("/paradas/PR%201%2F2/chegadas");
  });

  it("converte o payload para camelCase, preservando a fonte de cada número", async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: true, status: 200, json: async () => PAYLOAD }) as jest.Mock;

    const resultado = await buscarChegadasParada("PR-12345");

    expect(resultado?.paradaCodigo).toBe("PR-12345");
    expect(resultado?.paradaNome).toBe("W3 Sul 502");
    expect(resultado?.chegadas[0]).toEqual({
      numero: "0.110",
      nome: "0.110 — Taguatinga",
      rotaSentido: "IDA",
      etaMinutos: 4.3,
      fonte: "ao_vivo",
      prefixo: "440001",
      veiculosACaminho: 2,
      horarioPrevisto: null,
    });
    expect(resultado?.chegadas[1]).toMatchObject({ fonte: "previsto", horarioPrevisto: "15:18", prefixo: null });
  });

  it("campos opcionais ausentes viram null/0, e sem dado continua sem dado", async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: true, status: 200, json: async () => PAYLOAD }) as jest.Mock;

    const resultado = await buscarChegadasParada("PR-12345");

    expect(resultado?.chegadas[2]).toMatchObject({
      etaMinutos: null,
      fonte: null,
      prefixo: null,
      veiculosACaminho: 0,
      horarioPrevisto: null,
    });
  });

  it("404 (código que não é de parada física) devolve null, sem lançar", async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: false, status: 404 }) as jest.Mock;

    await expect(buscarChegadasParada("PR-NAO-EXISTE")).resolves.toBeNull();
  });

  it("erro do servidor devolve null, sem lançar", async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: false, status: 500 }) as jest.Mock;

    await expect(buscarChegadasParada("PR-12345")).resolves.toBeNull();
  });

  it("falha de rede devolve null — o painel da parada não pode quebrar por causa de um extra", async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error("rede fora")) as jest.Mock;

    await expect(buscarChegadasParada("PR-12345")).resolves.toBeNull();
  });

  it("lista de chegadas ausente vira lista vazia", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValue({ ok: true, status: 200, json: async () => ({ ...PAYLOAD, chegadas: undefined }) }) as jest.Mock;

    const resultado = await buscarChegadasParada("PR-12345");

    expect(resultado?.chegadas).toEqual([]);
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
  listarFavoritosRemoto,
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

  it("retorna cache local quando o servidor responde 5xx", async () => {
    cachearFavoritos([FAVORITO_RESPONSE]);
    global.fetch = jest.fn().mockResolvedValue({ ok: false, status: 503 }) as jest.Mock;

    const lista = await listarFavoritos();
    expect(lista).toHaveLength(1);
  });

  it("em 401 devolve [] e apaga o cache (cache não é por usuário)", async () => {
    cachearFavoritos([FAVORITO_RESPONSE]);
    global.fetch = jest.fn().mockResolvedValue({ ok: false, status: 401 }) as jest.Mock;

    const lista = await listarFavoritos();
    expect(lista).toEqual([]);
    expect(lerFavoritosCache()).toEqual([]);
  });

  it("listarFavoritosRemoto lança quando a rede falha", async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error("rede fora")) as jest.Mock;
    await expect(listarFavoritosRemoto()).rejects.toThrow();
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

describe("api.ts — pegar o ônibus (US #171)", () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  function resposta(status: number, corpo: unknown = {}) {
    return { ok: status >= 200 && status < 300, status, json: async () => corpo };
  }

  const ATIVA = {
    ativa: true,
    viagem: {
      id: "v-1",
      numero_linha: "0.110",
      sentido: "IDA",
      veiculo_prefixo: "440001",
      parada_destino_codigo: "PR-C",
      embarcou_em: "2026-10-14T15:00:00Z",
      encerrada_em: null,
      motivo_encerramento: null,
    },
    sinal: "ao_vivo",
    veiculo: { prefixo: "440001", lat: -15.8, lng: -48.0, direcao: 90, atualizado_em: "2026-10-14T12:00:00-03:00" },
    destino: { codigo: "PR-C", nome: "Parada C", lat: -15.8, lng: -48.1, ultrapassado: false },
    proxima_parada: { codigo: "PR-B", nome: "Parada B", lat: -15.8, lng: -48.05 },
    paradas_restantes: [
      { codigo: "PR-B", nome: "Parada B", lat: -15.8, lng: -48.05 },
      { codigo: "PR-C", nome: "Parada C", lat: -15.8, lng: -48.1 },
    ],
  };

  describe("buscarViagemAtiva", () => {
    it("chama /viagens/ativa pelo Gateway, com sessão e sem cache", async () => {
      global.fetch = jest.fn().mockResolvedValue(resposta(200, { ativa: false })) as jest.Mock;

      await buscarViagemAtiva();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringMatching(/\/api\/mobilidade\/viagens\/ativa$/),
        expect.objectContaining({ credentials: "include", cache: "no-store" })
      );
    });

    it("converte o payload para camelCase", async () => {
      global.fetch = jest.fn().mockResolvedValue(resposta(200, ATIVA)) as jest.Mock;

      const r = await buscarViagemAtiva();

      expect(r.falhou).toBe(false);
      if (r.falhou || !r.viagem) throw new Error("esperava viagem");
      expect(r.viagem).toMatchObject({
        id: "v-1",
        numeroLinha: "0.110",
        sentido: "IDA",
        veiculoPrefixo: "440001",
        paradaDestinoCodigo: "PR-C",
        sinal: "ao_vivo",
        veiculo: { prefixo: "440001", direcao: 90 },
        destino: { codigo: "PR-C", ultrapassado: false },
        proximaParada: { codigo: "PR-B" },
      });
      expect(r.viagem.paradasRestantes.map((p) => p.codigo)).toEqual(["PR-B", "PR-C"]);
    });

    it("`ativa: false` é 'aguardando', não falha", async () => {
      global.fetch = jest.fn().mockResolvedValue(resposta(200, { ativa: false })) as jest.Mock;
      expect(await buscarViagemAtiva()).toEqual({ falhou: false, viagem: null });
    });

    it("sem sessão (401) também é 'aguardando'", async () => {
      global.fetch = jest.fn().mockResolvedValue(resposta(401)) as jest.Mock;
      expect(await buscarViagemAtiva()).toEqual({ falhou: false, viagem: null });
    });

    it("erro do servidor é FALHA — quem chama mantém o que mostrava", async () => {
      global.fetch = jest.fn().mockResolvedValue(resposta(502)) as jest.Mock;
      expect(await buscarViagemAtiva()).toEqual({ falhou: true });
    });

    it("rede fora do ar é FALHA e nunca lança", async () => {
      global.fetch = jest.fn().mockRejectedValue(new Error("offline")) as jest.Mock;
      expect(await buscarViagemAtiva()).toEqual({ falhou: true });
    });

    it("sinal desconhecido vira 'sem_sinal' (na dúvida, não afirma ao vivo)", async () => {
      global.fetch = jest
        .fn()
        .mockResolvedValue(resposta(200, { ...ATIVA, sinal: "qualquer-coisa" })) as jest.Mock;
      const r = await buscarViagemAtiva();
      expect(!r.falhou && r.viagem?.sinal).toBe("sem_sinal");
    });

    it("tolera os campos opcionais ausentes", async () => {
      global.fetch = jest
        .fn()
        .mockResolvedValue(
          resposta(200, {
            ativa: true,
            viagem: { id: "v", numero_linha: "1", veiculo_prefixo: "9", embarcou_em: "2026-10-14T15:00:00Z" },
            sinal: "sem_sinal",
          })
        ) as jest.Mock;

      const r = await buscarViagemAtiva();

      if (r.falhou || !r.viagem) throw new Error("esperava viagem");
      expect(r.viagem.sentido).toBeNull();
      expect(r.viagem.paradaDestinoCodigo).toBeNull();
      expect(r.viagem.veiculo).toBeNull();
      expect(r.viagem.destino).toBeNull();
      expect(r.viagem.proximaParada).toBeNull();
      expect(r.viagem.paradasRestantes).toEqual([]);
    });
  });

  describe("embarcarNoOnibus", () => {
    it("faz POST /viagens com os nomes de campo do backend", async () => {
      global.fetch = jest.fn().mockResolvedValue(resposta(201, {})) as jest.Mock;

      await embarcarNoOnibus({ numeroLinha: "0.110", lat: -15.8, lng: -48.05, paradaDestinoCodigo: "PR-C" });

      const [url, opcoes] = (global.fetch as jest.Mock).mock.calls[0];
      expect(url).toMatch(/\/api\/mobilidade\/viagens$/);
      expect(opcoes).toMatchObject({ method: "POST", credentials: "include" });
      expect(JSON.parse(opcoes.body)).toEqual({
        numero_linha: "0.110",
        lat: -15.8,
        lng: -48.05,
        parada_destino_codigo: "PR-C",
      });
    });

    it("sem destino, não manda o campo", async () => {
      global.fetch = jest.fn().mockResolvedValue(resposta(201, {})) as jest.Mock;

      await embarcarNoOnibus({ numeroLinha: "0.110", lat: 1, lng: 2 });

      expect(JSON.parse((global.fetch as jest.Mock).mock.calls[0][1].body)).not.toHaveProperty(
        "parada_destino_codigo"
      );
    });

    it("422: usa a frase em português do servidor e guarda o status", async () => {
      global.fetch = jest
        .fn()
        .mockResolvedValue(resposta(422, { detail: "Não conseguimos confirmar seu embarque." })) as jest.Mock;

      const erro = await embarcarNoOnibus({ numeroLinha: "0.110", lat: 1, lng: 2 }).catch((e) => e);

      expect(erro).toBeInstanceOf(ViagemError);
      expect(erro.message).toBe("Não conseguimos confirmar seu embarque.");
      expect(erro.status).toBe(422);
    });

    it("409: já está em viagem", async () => {
      global.fetch = jest
        .fn()
        .mockResolvedValue(resposta(409, { detail: "Você já está em uma viagem." })) as jest.Mock;

      const erro = await embarcarNoOnibus({ numeroLinha: "0.110", lat: 1, lng: 2 }).catch((e) => e);

      expect(erro.status).toBe(409);
      expect(erro.message).toBe("Você já está em uma viagem.");
    });

    it("422 do schema (detail é lista) não vaza estrutura técnica", async () => {
      global.fetch = jest
        .fn()
        .mockResolvedValue(resposta(422, { detail: [{ loc: ["body", "lat"], msg: "x" }] })) as jest.Mock;

      const erro = await embarcarNoOnibus({ numeroLinha: "0.110", lat: 1, lng: 2 }).catch((e) => e);

      expect(erro.message).toBe("Não foi possível registrar o embarque. Tente novamente.");
    });

    it("401: pede login", async () => {
      global.fetch = jest.fn().mockResolvedValue(resposta(401)) as jest.Mock;
      const erro = await embarcarNoOnibus({ numeroLinha: "0.110", lat: 1, lng: 2 }).catch((e) => e);
      expect(erro.message).toBe("Faça login para registrar a viagem.");
    });

    it("500 não vaza texto técnico do servidor", async () => {
      global.fetch = jest.fn().mockResolvedValue(resposta(500, { detail: "Traceback ..." })) as jest.Mock;
      const erro = await embarcarNoOnibus({ numeroLinha: "0.110", lat: 1, lng: 2 }).catch((e) => e);
      expect(erro.message).toBe("Não foi possível registrar o embarque. Tente novamente.");
    });

    it("rede fora do ar vira ViagemError, não TypeError", async () => {
      global.fetch = jest.fn().mockRejectedValue(new TypeError("Failed to fetch")) as jest.Mock;
      const erro = await embarcarNoOnibus({ numeroLinha: "0.110", lat: 1, lng: 2 }).catch((e) => e);
      expect(erro).toBeInstanceOf(ViagemError);
      expect(erro.message).toMatch(/conexão/);
    });
  });

  describe("definirDestinoDaViagem", () => {
    it("faz PUT no destino da viagem, com o código", async () => {
      global.fetch = jest.fn().mockResolvedValue(resposta(200, {})) as jest.Mock;

      await definirDestinoDaViagem("v-1", "PR-C");

      const [url, opcoes] = (global.fetch as jest.Mock).mock.calls[0];
      expect(url).toMatch(/\/api\/mobilidade\/viagens\/v-1\/destino$/);
      expect(opcoes.method).toBe("PUT");
      expect(JSON.parse(opcoes.body)).toEqual({ parada_destino_codigo: "PR-C" });
    });

    it("`null` tira o destino (vai como null, não some do corpo)", async () => {
      global.fetch = jest.fn().mockResolvedValue(resposta(200, {})) as jest.Mock;

      await definirDestinoDaViagem("v-1", null);

      expect(JSON.parse((global.fetch as jest.Mock).mock.calls[0][1].body)).toEqual({
        parada_destino_codigo: null,
      });
    });

    it("codifica o id na URL", async () => {
      global.fetch = jest.fn().mockResolvedValue(resposta(200, {})) as jest.Mock;
      await definirDestinoDaViagem("a/b", "PR-C");
      expect((global.fetch as jest.Mock).mock.calls[0][0]).toContain("/viagens/a%2Fb/destino");
    });

    it("422: frase do servidor", async () => {
      global.fetch = jest
        .fn()
        .mockResolvedValue(resposta(422, { detail: "A parada de destino não faz parte desta linha." })) as jest.Mock;
      const erro = await definirDestinoDaViagem("v-1", "PR-Z").catch((e) => e);
      expect(erro.message).toBe("A parada de destino não faz parte desta linha.");
      expect(erro.status).toBe(422);
    });
  });

  describe("encerrarViagem", () => {
    it("faz POST em /encerrar", async () => {
      global.fetch = jest.fn().mockResolvedValue(resposta(200, {})) as jest.Mock;

      await encerrarViagem("v-1");

      const [url, opcoes] = (global.fetch as jest.Mock).mock.calls[0];
      expect(url).toMatch(/\/api\/mobilidade\/viagens\/v-1\/encerrar$/);
      expect(opcoes).toMatchObject({ method: "POST", credentials: "include" });
    });

    it("404 não é erro: a viagem já não existe, e era isso que a pessoa queria", async () => {
      global.fetch = jest.fn().mockResolvedValue(resposta(404, { detail: "Viagem não encontrada." })) as jest.Mock;
      await expect(encerrarViagem("v-1")).resolves.toBeUndefined();
    });

    it("500 é erro", async () => {
      global.fetch = jest.fn().mockResolvedValue(resposta(500)) as jest.Mock;
      await expect(encerrarViagem("v-1")).rejects.toThrow(/encerrar a viagem/);
    });

    it("rede fora do ar é erro com mensagem", async () => {
      global.fetch = jest.fn().mockRejectedValue(new TypeError("Failed to fetch")) as jest.Mock;
      await expect(encerrarViagem("v-1")).rejects.toBeInstanceOf(ViagemError);
    });
  });
});

// ---------------------------------------------------------------------------
// Issue #190 — tempo do ônibus nas paradas de subir e descer de uma rota
// ---------------------------------------------------------------------------

describe("buscarChegadasDaRota (issue #190)", () => {
  const PEDIDO = [
    { numero: "0.110", sentido: "IDA", embarqueCodigo: "PR-E", desembarqueCodigo: "PR-D" },
    { numero: "0.186", sentido: "CIRCULAR", embarqueCodigo: null, desembarqueCodigo: "PR-D2" },
  ];

  const PAYLOAD = {
    calculado_em: "2026-10-14T15:00:00+00:00",
    pernas: [
      {
        numero: "0.110",
        sentido: "IDA",
        embarque: { parada_codigo: "PR-E", eta_minutos: 4.3, fonte: "ao_vivo", prefixo: "440001", horario_previsto: null },
        desembarque: { parada_codigo: "PR-D", eta_minutos: 18, fonte: "previsto", prefixo: null, horario_previsto: "15:18" },
      },
      {
        numero: "0.186",
        sentido: "CIRCULAR",
        embarque: { parada_codigo: null, eta_minutos: null, fonte: null },
        desembarque: { parada_codigo: "PR-D2" },
      },
    ],
  };

  function respondendo(payload: unknown, ok = true, status = 200) {
    global.fetch = jest.fn().mockResolvedValue({ ok, status, json: async () => payload }) as jest.Mock;
  }

  it("faz POST em lote no endpoint da rota, com sessão e sem cache", async () => {
    respondendo(PAYLOAD);

    await buscarChegadasDaRota(PEDIDO);

    expect(global.fetch).toHaveBeenCalledTimes(1);
    const [url, opcoes] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toMatch(/\/api\/mobilidade\/rotas\/chegadas$/);
    expect(opcoes).toMatchObject({
      method: "POST",
      credentials: "include",
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
    });
  });

  it("manda os códigos em snake_case, na ordem dos trechos, e null onde não há código", async () => {
    respondendo(PAYLOAD);

    await buscarChegadasDaRota(PEDIDO);

    const corpo = JSON.parse((global.fetch as jest.Mock).mock.calls[0][1].body);
    expect(corpo).toEqual({
      pernas: [
        { numero: "0.110", sentido: "IDA", embarque_codigo: "PR-E", desembarque_codigo: "PR-D" },
        { numero: "0.186", sentido: "CIRCULAR", embarque_codigo: null, desembarque_codigo: "PR-D2" },
      ],
    });
  });

  it("converte o payload para camelCase, preservando a fonte de cada número", async () => {
    respondendo(PAYLOAD);

    const resultado = await buscarChegadasDaRota(PEDIDO);

    expect(resultado?.calculadoEm).toBe("2026-10-14T15:00:00+00:00");
    expect(resultado?.pernas).toHaveLength(2);
    expect(resultado?.pernas[0].embarque).toEqual({
      paradaCodigo: "PR-E",
      etaMinutos: 4.3,
      fonte: "ao_vivo",
      prefixo: "440001",
      horarioPrevisto: null,
    });
    expect(resultado?.pernas[0].desembarque).toEqual({
      paradaCodigo: "PR-D",
      etaMinutos: 18,
      fonte: "previsto",
      prefixo: null,
      horarioPrevisto: "15:18",
    });
  });

  it("campos ausentes viram null — sem dado continua sem dado", async () => {
    respondendo(PAYLOAD);

    const resultado = await buscarChegadasDaRota(PEDIDO);

    expect(resultado?.pernas[1].embarque).toEqual({
      paradaCodigo: null,
      etaMinutos: null,
      fonte: null,
      prefixo: null,
      horarioPrevisto: null,
    });
    expect(resultado?.pernas[1].desembarque).toMatchObject({ paradaCodigo: "PR-D2", etaMinutos: null, fonte: null });
  });

  it("resposta sem a lista de trechos vira lista vazia, não quebra", async () => {
    respondendo({ calculado_em: "x" });
    expect((await buscarChegadasDaRota(PEDIDO))?.pernas).toEqual([]);
  });

  it.each([[500], [422], [401], [404]])("HTTP %s devolve null (é um extra: não quebra a tela)", async (status) => {
    respondendo({ detail: "x" }, false, status);
    expect(await buscarChegadasDaRota(PEDIDO)).toBeNull();
  });

  it("rede fora do ar devolve null", async () => {
    global.fetch = jest.fn().mockRejectedValue(new TypeError("Failed to fetch")) as jest.Mock;
    expect(await buscarChegadasDaRota(PEDIDO)).toBeNull();
  });

  it("JSON inválido devolve null", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => {
        throw new SyntaxError("Unexpected token");
      },
    }) as jest.Mock;
    expect(await buscarChegadasDaRota(PEDIDO)).toBeNull();
  });
});
