import { act, renderHook, waitFor } from "@testing-library/react";
import { buscarChegadasDaRota, ChegadasDaRota, PernaViagem } from "@/lib/api";
import { INTERVALO_CHEGADAS_MS } from "../useChegadasDaParada";
import { pedidoDasPernas, useChegadasDaRota } from "../useChegadasDaRota";

jest.mock("@/lib/api", () => ({
  buscarChegadasDaRota: jest.fn(),
}));

const buscarMock = buscarChegadasDaRota as jest.Mock;

function perna(numero: string, embarque: string | null, desembarque: string | null): PernaViagem {
  return {
    numero,
    sentido: "IDA",
    nome: `${numero} — teste`,
    embarque: { lat: -15.8, lng: -47.9, parada_nome: "A", caminhada_metros: 10, parada_codigo: embarque },
    desembarque: { lat: -15.7, lng: -47.8, parada_nome: "B", caminhada_metros: 20, parada_codigo: desembarque },
    distancia_km: 5,
    paradas_no_trecho: 10,
    trajeto: [],
  };
}

function resposta(eta: number, quantas = 1): ChegadasDaRota {
  return {
    calculadoEm: "2026-10-14T15:00:00+00:00",
    pernas: Array.from({ length: quantas }, (_, i) => ({
      numero: i === 0 ? "0.110" : "0.186",
      sentido: "IDA",
      embarque: { paradaCodigo: "PR-E", etaMinutos: eta, fonte: "ao_vivo" as const, prefixo: "1", horarioPrevisto: null },
      desembarque: { paradaCodigo: "PR-D", etaMinutos: eta + 10, fonte: "ao_vivo" as const, prefixo: "1", horarioPrevisto: null },
    })),
  };
}

/** Promessa que o teste resolve quando quiser — pra controlar a ordem das respostas. */
function adiavel<T>() {
  let resolver!: (valor: T) => void;
  const promessa = new Promise<T>((resolve) => {
    resolver = resolve;
  });
  return { promessa, resolver };
}

const UMA_PERNA = [perna("0.110", "PR-E", "PR-D")];

describe("pedidoDasPernas", () => {
  it("monta o pedido com sentido e códigos de cada trecho", () => {
    expect(pedidoDasPernas([perna("0.110", "PR-E", "PR-D"), perna("0.186", "PR-X", null)])).toEqual([
      { numero: "0.110", sentido: "IDA", embarqueCodigo: "PR-E", desembarqueCodigo: "PR-D" },
      { numero: "0.186", sentido: "IDA", embarqueCodigo: "PR-X", desembarqueCodigo: null },
    ]);
  });

  it.each([
    ["null", null],
    ["undefined", undefined],
    ["lista vazia", []],
  ])("%s não gera pedido", (_nome, entrada) => {
    expect(pedidoDasPernas(entrada)).toBeNull();
  });

  it("nenhum ponto com código: nada a perguntar", () => {
    expect(pedidoDasPernas([perna("0.110", null, null)])).toBeNull();
  });

  it("código ausente (backend antigo) conta como sem código", () => {
    const antiga = perna("0.110", null, null);
    delete antiga.embarque.parada_codigo;
    delete antiga.desembarque.parada_codigo;
    expect(pedidoDasPernas([antiga])).toBeNull();
  });

  it("basta um ponto com código", () => {
    expect(pedidoDasPernas([perna("0.110", null, "PR-D")])).not.toBeNull();
  });
});

describe("useChegadasDaRota", () => {
  beforeEach(() => {
    buscarMock.mockReset();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("sem opção escolhida, não busca nada", () => {
    const { result } = renderHook(() => useChegadasDaRota(null));

    expect(buscarMock).not.toHaveBeenCalled();
    expect(result.current.chegadas).toBeNull();
  });

  it("sem códigos de parada, não busca nada", () => {
    renderHook(() => useChegadasDaRota([perna("0.110", null, null)]));
    expect(buscarMock).not.toHaveBeenCalled();
  });

  it("busca ao escolher a opção e devolve os tempos, alinhados com as pernas", async () => {
    buscarMock.mockResolvedValue(resposta(4, 2));

    const { result } = renderHook(() =>
      useChegadasDaRota([perna("0.110", "PR-E", "PR-D"), perna("0.186", "PR-E2", "PR-D2")])
    );

    await waitFor(() => expect(result.current.chegadas).toHaveLength(2));
    expect(buscarMock).toHaveBeenCalledTimes(1);
    expect(buscarMock).toHaveBeenCalledWith([
      { numero: "0.110", sentido: "IDA", embarqueCodigo: "PR-E", desembarqueCodigo: "PR-D" },
      { numero: "0.186", sentido: "IDA", embarqueCodigo: "PR-E2", desembarqueCodigo: "PR-D2" },
    ]);
    expect(result.current.chegadas?.[0].embarque.etaMinutos).toBe(4);
  });

  it("atualiza sozinho a cada 20 s", async () => {
    jest.useFakeTimers();
    buscarMock.mockResolvedValueOnce(resposta(4)).mockResolvedValueOnce(resposta(3));

    const { result } = renderHook(() => useChegadasDaRota(UMA_PERNA));
    await act(async () => {});
    expect(result.current.chegadas?.[0].embarque.etaMinutos).toBe(4);

    await act(async () => {
      jest.advanceTimersByTime(INTERVALO_CHEGADAS_MS);
    });

    expect(INTERVALO_CHEGADAS_MS).toBe(20_000);
    expect(buscarMock).toHaveBeenCalledTimes(2);
    expect(result.current.chegadas?.[0].embarque.etaMinutos).toBe(3);
  });

  it("re-renderizar com as mesmas pernas (novo array) NÃO reinicia o polling", async () => {
    jest.useFakeTimers();
    buscarMock.mockResolvedValue(resposta(4));

    const { rerender } = renderHook(({ pernas }) => useChegadasDaRota(pernas), {
      initialProps: { pernas: [perna("0.110", "PR-E", "PR-D")] },
    });
    await act(async () => {});
    rerender({ pernas: [perna("0.110", "PR-E", "PR-D")] });
    rerender({ pernas: [perna("0.110", "PR-E", "PR-D")] });
    await act(async () => {});

    expect(buscarMock).toHaveBeenCalledTimes(1);
  });

  it("desmarcar a opção cancela o polling", async () => {
    jest.useFakeTimers();
    buscarMock.mockResolvedValue(resposta(4));

    const { rerender, result } = renderHook(({ pernas }) => useChegadasDaRota(pernas), {
      initialProps: { pernas: UMA_PERNA as PernaViagem[] | null },
    });
    await act(async () => {});
    rerender({ pernas: null });

    await act(async () => {
      jest.advanceTimersByTime(INTERVALO_CHEGADAS_MS * 3);
    });

    expect(buscarMock).toHaveBeenCalledTimes(1);
    expect(result.current.chegadas).toBeNull();
  });

  it("desmontar cancela o polling (sem vazar o intervalo)", async () => {
    jest.useFakeTimers();
    buscarMock.mockResolvedValue(resposta(4));

    const { unmount } = renderHook(() => useChegadasDaRota(UMA_PERNA));
    await act(async () => {});
    unmount();

    await act(async () => {
      jest.advanceTimersByTime(INTERVALO_CHEGADAS_MS * 3);
    });

    expect(buscarMock).toHaveBeenCalledTimes(1);
  });

  it("trocar de opção: a resposta atrasada da anterior NÃO sobrescreve a da nova", async () => {
    const respostaA = adiavel<ChegadasDaRota | null>();
    buscarMock.mockImplementation((pedido: { numero: string }[]) =>
      pedido[0].numero === "0.AAA" ? respostaA.promessa : Promise.resolve(resposta(7))
    );

    const { result, rerender } = renderHook(({ pernas }) => useChegadasDaRota(pernas), {
      initialProps: { pernas: [perna("0.AAA", "PR-E", "PR-D")] },
    });
    rerender({ pernas: [perna("0.BBB", "PR-E", "PR-D")] });
    await waitFor(() => expect(result.current.chegadas?.[0].embarque.etaMinutos).toBe(7));

    // a resposta de A chega por último
    await act(async () => {
      respostaA.resolver(resposta(1));
    });

    expect(result.current.chegadas?.[0].embarque.etaMinutos).toBe(7);
  });

  it("trocar de opção limpa os tempos da anterior na hora (seriam de outra rota)", async () => {
    buscarMock.mockImplementation((pedido: { numero: string }[]) =>
      pedido[0].numero === "0.AAA" ? Promise.resolve(resposta(2)) : new Promise(() => {})
    );

    const { result, rerender } = renderHook(({ pernas }) => useChegadasDaRota(pernas), {
      initialProps: { pernas: [perna("0.AAA", "PR-E", "PR-D")] },
    });
    await waitFor(() => expect(result.current.chegadas).not.toBeNull());

    rerender({ pernas: [perna("0.BBB", "PR-E", "PR-D")] });

    expect(result.current.chegadas).toBeNull();
  });

  it("uma consulta lenta que termina DEPOIS da seguinte não desfaz o valor mais novo", async () => {
    jest.useFakeTimers();
    const lenta = adiavel<ChegadasDaRota | null>();
    buscarMock
      .mockReturnValueOnce(lenta.promessa) // 1ª: demora
      .mockResolvedValueOnce(resposta(3)); // 2ª: volta antes

    const { result } = renderHook(() => useChegadasDaRota(UMA_PERNA));
    await act(async () => {
      jest.advanceTimersByTime(INTERVALO_CHEGADAS_MS);
    });
    expect(result.current.chegadas?.[0].embarque.etaMinutos).toBe(3);

    await act(async () => {
      lenta.resolver(resposta(9));
    });

    expect(result.current.chegadas?.[0].embarque.etaMinutos).toBe(3);
  });

  it("falha numa atualização não apaga o que já estava na tela", async () => {
    jest.useFakeTimers();
    buscarMock.mockResolvedValueOnce(resposta(4)).mockResolvedValueOnce(null);

    const { result } = renderHook(() => useChegadasDaRota(UMA_PERNA));
    await act(async () => {});
    await act(async () => {
      jest.advanceTimersByTime(INTERVALO_CHEGADAS_MS);
    });

    expect(buscarMock).toHaveBeenCalledTimes(2);
    expect(result.current.chegadas?.[0].embarque.etaMinutos).toBe(4);
  });

  it("falha logo na primeira busca: continua sem chegadas", async () => {
    buscarMock.mockResolvedValue(null);

    const { result } = renderHook(() => useChegadasDaRota(UMA_PERNA));
    await act(async () => {});

    expect(buscarMock).toHaveBeenCalledTimes(1);
    expect(result.current.chegadas).toBeNull();
  });

  it("resposta com outro número de trechos é ignorada (não mostra o tempo de um trecho no outro)", async () => {
    buscarMock.mockResolvedValue(resposta(4, 2));

    const { result } = renderHook(() => useChegadasDaRota(UMA_PERNA));
    await act(async () => {});

    expect(result.current.chegadas).toBeNull();
  });
});
