import { buscarParadas, BuscarParadasError } from "../api";

describe("api.ts — buscarParadas (US #21)", () => {
  it("chama o Gateway com o termo codificado e converte os campos", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        tipo: "endereco",
        paradas: [
          { codigo: "PR-1", nome: "W3 Sul", lat: -15.8, lng: -47.9, qtd_linhas: 8, distancia_m: 120 },
        ],
        referencia: { nome: "Hospital", endereco: "Hospital, Brasília", lat: -15.8, lng: -47.9 },
      }),
    }) as jest.Mock;

    const resultado = await buscarParadas("W3 Sul/502");

    const url = (global.fetch as jest.Mock).mock.calls[0][0];
    expect(url).toMatch(/\/api\/mobilidade\/paradas\/busca\?q=W3%20Sul%2F502$/);
    expect(resultado).toEqual({
      tipo: "endereco",
      paradas: [
        { codigo: "PR-1", nome: "W3 Sul", lat: -15.8, lng: -47.9, qtdLinhas: 8, distanciaM: 120 },
      ],
      referencia: { nome: "Hospital", endereco: "Hospital, Brasília", lat: -15.8, lng: -47.9 },
    });
  });

  it("nenhum resultado não é erro", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ tipo: "nenhum", paradas: [], referencia: null }),
    }) as jest.Mock;

    await expect(buscarParadas("xyzw")).resolves.toEqual({
      tipo: "nenhum",
      paradas: [],
      referencia: null,
    });
  });

  it("falha do servidor lança BuscarParadasError", async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: false, status: 500 }) as jest.Mock;

    await expect(buscarParadas("w3 sul")).rejects.toBeInstanceOf(BuscarParadasError);
  });

  it("falha de rede lança BuscarParadasError com mensagem de conexão", async () => {
    global.fetch = jest.fn().mockRejectedValue(new TypeError("Failed to fetch")) as jest.Mock;

    await expect(buscarParadas("w3 sul")).rejects.toThrow("Sem conexão");
  });
});
