import { act, renderHook, waitFor } from "@testing-library/react";
import { ChegadasDaParada, buscarChegadasParada } from "@/lib/api";
import { INTERVALO_CHEGADAS_MS, useChegadasDaParada } from "../useChegadasDaParada";

jest.mock("@/lib/api", () => ({
  buscarChegadasParada: jest.fn(),
}));

const buscarMock = buscarChegadasParada as jest.Mock;

function chegadas(codigo: string, eta: number): ChegadasDaParada {
  return {
    paradaCodigo: codigo,
    paradaNome: `Parada ${codigo}`,
    calculadoEm: "2026-10-14T15:00:00+00:00",
    chegadas: [
      {
        numero: "0.110",
        nome: "0.110",
        rotaSentido: "IDA",
        etaMinutos: eta,
        fonte: "ao_vivo",
        prefixo: "440001",
        veiculosACaminho: 1,
        horarioPrevisto: null,
      },
    ],
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

describe("useChegadasDaParada", () => {
  beforeEach(() => {
    buscarMock.mockReset();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("sem código (painel fechado), não busca nada", () => {
    const { result } = renderHook(() => useChegadasDaParada(null));

    expect(buscarMock).not.toHaveBeenCalled();
    expect(result.current).toEqual({ chegadas: null, carregando: false });
  });

  it("busca ao abrir e devolve as chegadas", async () => {
    buscarMock.mockResolvedValue(chegadas("PR-1", 4));

    const { result } = renderHook(() => useChegadasDaParada("PR-1"));

    expect(result.current.carregando).toBe(true);
    await waitFor(() => expect(result.current.chegadas?.paradaCodigo).toBe("PR-1"));
    expect(result.current.carregando).toBe(false);
    expect(buscarMock).toHaveBeenCalledWith("PR-1");
  });

  it("atualiza sozinho a cada intervalo, enquanto aberto", async () => {
    jest.useFakeTimers();
    buscarMock.mockResolvedValueOnce(chegadas("PR-1", 4)).mockResolvedValueOnce(chegadas("PR-1", 3));

    const { result } = renderHook(() => useChegadasDaParada("PR-1"));
    await act(async () => {});
    expect(result.current.chegadas?.chegadas[0].etaMinutos).toBe(4);

    await act(async () => {
      jest.advanceTimersByTime(INTERVALO_CHEGADAS_MS);
    });

    expect(buscarMock).toHaveBeenCalledTimes(2);
    expect(result.current.chegadas?.chegadas[0].etaMinutos).toBe(3);
  });

  it("parar de acompanhar (fechar o painel) cancela o polling", async () => {
    jest.useFakeTimers();
    buscarMock.mockResolvedValue(chegadas("PR-1", 4));

    const { rerender } = renderHook(({ codigo }) => useChegadasDaParada(codigo), {
      initialProps: { codigo: "PR-1" as string | null },
    });
    await act(async () => {});
    rerender({ codigo: null });

    await act(async () => {
      jest.advanceTimersByTime(INTERVALO_CHEGADAS_MS * 3);
    });

    expect(buscarMock).toHaveBeenCalledTimes(1);
  });

  it("desmontar cancela o polling (sem vazar o intervalo)", async () => {
    jest.useFakeTimers();
    buscarMock.mockResolvedValue(chegadas("PR-1", 4));

    const { unmount } = renderHook(() => useChegadasDaParada("PR-1"));
    await act(async () => {});
    unmount();

    await act(async () => {
      jest.advanceTimersByTime(INTERVALO_CHEGADAS_MS * 3);
    });

    expect(buscarMock).toHaveBeenCalledTimes(1);
  });

  it("clicar na parada A e logo na B: a resposta atrasada de A NÃO sobrescreve a de B", async () => {
    const respostaA = adiavel<ChegadasDaParada | null>();
    buscarMock.mockImplementation((codigo: string) =>
      codigo === "PR-A" ? respostaA.promessa : Promise.resolve(chegadas("PR-B", 7))
    );

    const { result, rerender } = renderHook(({ codigo }) => useChegadasDaParada(codigo), {
      initialProps: { codigo: "PR-A" as string | null },
    });
    rerender({ codigo: "PR-B" });
    await waitFor(() => expect(result.current.chegadas?.paradaCodigo).toBe("PR-B"));

    // a resposta de A chega por último
    await act(async () => {
      respostaA.resolver(chegadas("PR-A", 1));
    });

    expect(result.current.chegadas?.paradaCodigo).toBe("PR-B");
  });

  it("trocar de parada limpa as chegadas da anterior na hora", async () => {
    buscarMock.mockImplementation((codigo: string) =>
      codigo === "PR-A" ? Promise.resolve(chegadas("PR-A", 2)) : new Promise(() => {})
    );

    const { result, rerender } = renderHook(({ codigo }) => useChegadasDaParada(codigo), {
      initialProps: { codigo: "PR-A" as string | null },
    });
    await waitFor(() => expect(result.current.chegadas?.paradaCodigo).toBe("PR-A"));

    rerender({ codigo: "PR-B" });

    expect(result.current.chegadas).toBeNull();
    expect(result.current.carregando).toBe(true);
  });

  it("falha numa atualização não apaga o que já estava na tela", async () => {
    jest.useFakeTimers();
    buscarMock.mockResolvedValueOnce(chegadas("PR-1", 4)).mockResolvedValueOnce(null);

    const { result } = renderHook(() => useChegadasDaParada("PR-1"));
    await act(async () => {});
    await act(async () => {
      jest.advanceTimersByTime(INTERVALO_CHEGADAS_MS);
    });

    expect(buscarMock).toHaveBeenCalledTimes(2);
    expect(result.current.chegadas?.chegadas[0].etaMinutos).toBe(4);
  });

  it("falha logo na primeira busca: sem chegadas, e para de carregar", async () => {
    buscarMock.mockResolvedValue(null);

    const { result } = renderHook(() => useChegadasDaParada("PR-1"));

    await waitFor(() => expect(result.current.carregando).toBe(false));
    expect(result.current.chegadas).toBeNull();
  });
});
