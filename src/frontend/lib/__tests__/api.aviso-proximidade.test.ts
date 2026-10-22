import { buscarViagemAtiva, confirmarAvisoDeProximidade } from "../api";

/**
 * US #172 — o aviso de proximidade no cliente da API: como a resposta de
 * /viagens/ativa vira `avisoProximidade` e como a tela confirma que o viu.
 */

function resposta(status: number, corpo?: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => corpo,
  };
}

const VIAGEM = {
  id: "v-1",
  numero_linha: "0.110",
  sentido: "IDA",
  veiculo_prefixo: "440001",
  parada_destino_codigo: "PR-C",
  embarcou_em: "2026-10-14T15:00:00Z",
};

const ATIVA = {
  ativa: true,
  viagem: VIAGEM,
  sinal: "ao_vivo",
  veiculo: null,
  destino: null,
  proxima_parada: null,
  paradas_restantes: [],
};

async function viagemDa(corpo: unknown) {
  global.fetch = jest.fn().mockResolvedValue(resposta(200, corpo)) as jest.Mock;
  const r = await buscarViagemAtiva();
  if (r.falhou || !r.viagem) throw new Error("esperava viagem");
  return r.viagem;
}

describe("buscarViagemAtiva — aviso de proximidade", () => {
  it("converte o aviso pendente para camelCase", async () => {
    const viagem = await viagemDa({
      ...ATIVA,
      alerta_proximidade: {
        id: "a-1",
        parada_codigo: "PR-C",
        parada_nome: "Terminal Central",
        eta_minutos: 2.5,
        disparado_em: "2026-10-14T15:30:00Z",
      },
    });

    expect(viagem.avisoProximidade).toEqual({
      id: "a-1",
      paradaCodigo: "PR-C",
      paradaNome: "Terminal Central",
      etaMinutos: 2.5,
      disparadoEm: "2026-10-14T15:30:00Z",
    });
  });

  it("sem aviso, o campo é nulo", async () => {
    const viagem = await viagemDa({ ...ATIVA, alerta_proximidade: null });

    expect(viagem.avisoProximidade).toBeNull();
  });

  it("backend antigo, sem o campo: nulo, sem quebrar", async () => {
    const viagem = await viagemDa(ATIVA);

    expect(viagem.avisoProximidade).toBeNull();
  });

  it("parada sem nome e sem ETA viram null", async () => {
    const viagem = await viagemDa({
      ...ATIVA,
      alerta_proximidade: {
        id: "a-2",
        parada_codigo: "PR-C",
        disparado_em: "2026-10-14T15:30:00Z",
      },
    });

    expect(viagem.avisoProximidade).toMatchObject({ paradaNome: null, etaMinutos: null });
  });
});

describe("confirmarAvisoDeProximidade", () => {
  it("avisa o servidor pelo Gateway, com a sessão", async () => {
    global.fetch = jest.fn().mockResolvedValue(resposta(204)) as jest.Mock;

    await confirmarAvisoDeProximidade("v-1");

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/mobilidade\/viagens\/v-1\/alerta-proximidade\/visto$/),
      expect.objectContaining({ method: "POST", credentials: "include" })
    );
  });

  it("escapa o id da viagem na URL", async () => {
    global.fetch = jest.fn().mockResolvedValue(resposta(204)) as jest.Mock;

    await confirmarAvisoDeProximidade("a/b");

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/viagens/a%2Fb/alerta-proximidade/visto"),
      expect.anything()
    );
  });

  it("sem rede, não lança: o aviso já saiu da tela", async () => {
    global.fetch = jest.fn().mockRejectedValue(new TypeError("Failed to fetch")) as jest.Mock;

    await expect(confirmarAvisoDeProximidade("v-1")).resolves.toBeUndefined();
  });

  it("erro do servidor também não lança", async () => {
    global.fetch = jest.fn().mockResolvedValue(resposta(500)) as jest.Mock;

    await expect(confirmarAvisoDeProximidade("v-1")).resolves.toBeUndefined();
  });
});
