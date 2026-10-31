import { act, renderHook } from "@testing-library/react";
import { enviarPosicaoColaborativa, ViagemError } from "@/lib/api";
import {
  INTERVALO_ENVIO_POSICAO_MS,
  usePosicaoColaborativa,
} from "../usePosicaoColaborativa";

jest.mock("@/lib/api", () => ({
  ...jest.requireActual("@/lib/api"),
  enviarPosicaoColaborativa: jest.fn(),
}));

const enviarMock = enviarPosicaoColaborativa as jest.Mock;

const POSICAO = { lat: -15.8, lng: -48.05, precisaoM: 12 };

function montar(opcoes: {
  viagemId?: string | null;
  compartilhando?: boolean;
  posicao?: typeof POSICAO | null;
  revogarLocalmente?: () => void;
} = {}) {
  const revogarLocalmente = opcoes.revogarLocalmente ?? jest.fn();
  const lerPosicao = jest.fn(() => (opcoes.posicao === undefined ? POSICAO : opcoes.posicao));
  const util = renderHook(
    ({ viagemId, compartilhando }) =>
      usePosicaoColaborativa({
        viagemId: viagemId ?? null,
        compartilhando,
        lerPosicao,
        revogarLocalmente,
      }),
    {
      initialProps: {
        viagemId: opcoes.viagemId ?? "v-1",
        compartilhando: opcoes.compartilhando ?? true,
      },
    }
  );
  return { util, lerPosicao, revogarLocalmente };
}

beforeEach(() => {
  jest.useFakeTimers();
  jest.resetAllMocks();
});

afterEach(() => {
  jest.useRealTimers();
});

describe("usePosicaoColaborativa (US #199)", () => {
  it("o intervalo é de 15 s (entre o limite do servidor e o feed da SEMOB)", () => {
    expect(INTERVALO_ENVIO_POSICAO_MS).toBe(15_000);
  });

  it("sem consentimento: não envia nada (Cenário 1, desligado por padrão)", () => {
    montar({ compartilhando: false });

    jest.advanceTimersByTime(60_000);

    expect(enviarMock).not.toHaveBeenCalled();
  });

  it("consentido, envia a posição na hora e a cada 15 s, com lat/lng e precisão do GPS", async () => {
    enviarMock.mockResolvedValue({ aceita: true, motivo: "aceita" });
    const { lerPosicao } = montar();

    // envio imediato
    expect(enviarMock).toHaveBeenCalledTimes(1);
    expect(enviarMock).toHaveBeenNthCalledWith(1, "v-1", POSICAO);
    expect(lerPosicao).toHaveBeenCalled();

    // ciclo seguinte
    await act(async () => {
      await jest.advanceTimersByTimeAsync(INTERVALO_ENVIO_POSICAO_MS);
    });
    await act(async () => {
      await jest.advanceTimersByTimeAsync(INTERVALO_ENVIO_POSICAO_MS);
    });
    expect(enviarMock).toHaveBeenCalledTimes(3);
  });

  it("sem leitura do GPS ainda: não envia, e tenta de novo no ciclo seguinte", async () => {
    enviarMock.mockResolvedValue({ aceita: true, motivo: "aceita" });
    montar({ posicao: null });

    expect(enviarMock).not.toHaveBeenCalled();

    await act(async () => {
      await jest.advanceTimersByTimeAsync(INTERVALO_ENVIO_POSICAO_MS);
    });
    expect(enviarMock).not.toHaveBeenCalled();
  });

  it("429 (anti-martelada): fica quieto, não revoga e continua no próximo ciclo", async () => {
    enviarMock.mockRejectedValue(new ViagemError("Muitos envios.", 429));
    const { revogarLocalmente } = montar();

    expect(enviarMock).toHaveBeenCalledTimes(1);

    await act(async () => {
      await jest.advanceTimersByTimeAsync(INTERVALO_ENVIO_POSICAO_MS);
    });
    expect(enviarMock).toHaveBeenCalledTimes(2);
    expect(revogarLocalmente).not.toHaveBeenCalled();
  });

  it("409 (consentimento revogado): marca a revogação local e PARA de enviar", async () => {
    enviarMock.mockRejectedValue(new ViagemError("Sem consentimento.", 409));
    const { revogarLocalmente } = montar();

    expect(enviarMock).toHaveBeenCalledTimes(1);

    await act(async () => {
      await jest.advanceTimersByTimeAsync(INTERVALO_ENVIO_POSICAO_MS);
    });
    expect(revogarLocalmente).toHaveBeenCalled();
    expect(enviarMock).toHaveBeenCalledTimes(1); // ciclo morto
  });

  it("404 (a viagem já não é dele): também para o ciclo", async () => {
    enviarMock.mockRejectedValue(new ViagemError("Viagem não encontrada.", 404));
    const { revogarLocalmente } = montar();

    await act(async () => {
      await jest.advanceTimersByTimeAsync(INTERVALO_ENVIO_POSICAO_MS);
    });
    expect(revogarLocalmente).toHaveBeenCalled();
    expect(enviarMock).toHaveBeenCalledTimes(1);
  });

  it("'Parar' desliga o consentimento (compartilhando → false): o intervalo morre", async () => {
    enviarMock.mockResolvedValue({ aceita: true, motivo: "aceita" });
    const { util } = montar();

    expect(enviarMock).toHaveBeenCalledTimes(1);

    act(() => {
      util.rerender({ viagemId: "v-1", compartilhando: false });
    });
    await act(async () => {
      await jest.advanceTimersByTimeAsync(INTERVALO_ENVIO_POSICAO_MS);
    });

    expect(enviarMock).toHaveBeenCalledTimes(1); // nada depois do Parar
  });

  it("a leitura é a função mais recente (ref): trocar o GPS no meio não perde envio", async () => {
    enviarMock.mockResolvedValue({ aceita: true, motivo: "aceita" });
    const posicaoAntiga = { lat: 1, lng: 2, precisaoM: 50 };
    const posicaoNova = { lat: 3, lng: 4, precisaoM: 8 };
    const lerPosicao = jest.fn(() => posicaoAntiga);
    const revogarLocalmente = jest.fn();

    const util = renderHook(
      ({ ler }) =>
        usePosicaoColaborativa({
          viagemId: "v-1",
          compartilhando: true,
          lerPosicao: ler,
          revogarLocalmente,
        }),
      { initialProps: { ler: () => posicaoAntiga } }
    );

    // GPS atualizou entre os ciclos: o próximo envio usa a leitura nova.
    await act(async () => {
      await jest.advanceTimersByTimeAsync(INTERVALO_ENVIO_POSICAO_MS);
    });
    util.rerender({ ler: () => posicaoNova });
    await act(async () => {
      await jest.advanceTimersByTimeAsync(INTERVALO_ENVIO_POSICAO_MS);
    });

    expect(enviarMock).toHaveBeenLastCalledWith("v-1", posicaoNova);
    void lerPosicao;
  });
});
