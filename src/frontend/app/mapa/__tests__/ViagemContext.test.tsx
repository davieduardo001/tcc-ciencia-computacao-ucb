import { ReactNode } from "react";
import { act, renderHook, waitFor } from "@testing-library/react";
import {
  buscarViagemAtiva,
  definirDestinoDaViagem,
  embarcarNoOnibus,
  encerrarViagem,
  ViagemAtiva,
  ViagemError,
} from "@/lib/api";
import { INTERVALO_VIAGEM_MS, useViagem, ViagemProvider } from "../ViagemContext";

// ViagemError é usada em `instanceof` dentro do provider: precisa ser a real.
jest.mock("@/lib/api", () => ({
  ...jest.requireActual("@/lib/api"),
  buscarViagemAtiva: jest.fn(),
  embarcarNoOnibus: jest.fn(),
  definirDestinoDaViagem: jest.fn(),
  encerrarViagem: jest.fn(),
}));

const buscarMock = buscarViagemAtiva as jest.Mock;
const embarcarMock = embarcarNoOnibus as jest.Mock;
const destinoMock = definirDestinoDaViagem as jest.Mock;
const encerrarMock = encerrarViagem as jest.Mock;

function viagem(sobre: Partial<ViagemAtiva> = {}): ViagemAtiva {
  return {
    id: "v-1",
    numeroLinha: "0.110",
    sentido: "IDA",
    veiculoPrefixo: "440001",
    paradaDestinoCodigo: null,
    embarcouEm: "2026-10-14T15:00:00Z",
    sinal: "ao_vivo",
    veiculo: null,
    destino: null,
    proximaParada: null,
    paradasRestantes: [],
    ...sobre,
  };
}

const AGUARDANDO = { falhou: false, viagem: null };
const EM_VIAGEM = { falhou: false, viagem: viagem() };
const FALHA = { falhou: true };

function adiavel<T>() {
  let resolver!: (valor: T) => void;
  const promessa = new Promise<T>((resolve) => {
    resolver = resolve;
  });
  return { promessa, resolver };
}

const wrapper = ({ children }: { children: ReactNode }) => <ViagemProvider>{children}</ViagemProvider>;

function montar() {
  return renderHook(() => useViagem(), { wrapper });
}

describe("ViagemProvider", () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe("estado inicial", () => {
    it("consulta ao abrir; sem viagem, está 'aguardando'", async () => {
      buscarMock.mockResolvedValue(AGUARDANDO);

      const { result } = montar();
      expect(result.current.carregando).toBe(true);

      await waitFor(() => expect(result.current.carregando).toBe(false));
      expect(result.current.viagem).toBeNull();
      expect(buscarMock).toHaveBeenCalledTimes(1);
    });

    it("com viagem em andamento, já abre 'em viagem'", async () => {
      buscarMock.mockResolvedValue(EM_VIAGEM);

      const { result } = montar();

      await waitFor(() => expect(result.current.viagem?.id).toBe("v-1"));
      expect(result.current.carregando).toBe(false);
    });

    it("se a primeira consulta falhar, para de 'carregar' e fica aguardando", async () => {
      buscarMock.mockResolvedValue(FALHA);

      const { result } = montar();

      await waitFor(() => expect(result.current.carregando).toBe(false));
      expect(result.current.viagem).toBeNull();
    });

    it("sem Provider, o hook responde 'aguardando' e não explode", async () => {
      const { result } = renderHook(() => useViagem());

      expect(result.current.viagem).toBeNull();
      expect(result.current.carregando).toBe(false);
      await expect(result.current.encerrar()).resolves.toMatchObject({ ok: false });
      expect(buscarMock).not.toHaveBeenCalled();
    });
  });

  describe("polling", () => {
    it("em viagem, repete a consulta a cada 20 s", async () => {
      jest.useFakeTimers();
      buscarMock.mockResolvedValue(EM_VIAGEM);

      const { result } = montar();
      await act(async () => {
        await Promise.resolve();
      });
      expect(result.current.viagem).not.toBeNull();
      expect(buscarMock).toHaveBeenCalledTimes(1);

      await act(async () => {
        jest.advanceTimersByTime(INTERVALO_VIAGEM_MS);
      });
      expect(buscarMock).toHaveBeenCalledTimes(2);

      await act(async () => {
        jest.advanceTimersByTime(INTERVALO_VIAGEM_MS);
      });
      expect(buscarMock).toHaveBeenCalledTimes(3);
    });

    it("aguardando, NÃO fica consultando (só muda por ação do próprio usuário)", async () => {
      jest.useFakeTimers();
      buscarMock.mockResolvedValue(AGUARDANDO);

      montar();
      await act(async () => {
        await Promise.resolve();
      });
      await act(async () => {
        jest.advanceTimersByTime(INTERVALO_VIAGEM_MS * 5);
      });

      expect(buscarMock).toHaveBeenCalledTimes(1);
    });

    it("falha de rede no polling NÃO derruba o 'em viagem'", async () => {
      jest.useFakeTimers();
      buscarMock.mockResolvedValueOnce(EM_VIAGEM).mockResolvedValue(FALHA);

      const { result } = montar();
      await act(async () => {
        await Promise.resolve();
      });
      await act(async () => {
        jest.advanceTimersByTime(INTERVALO_VIAGEM_MS);
      });

      expect(buscarMock).toHaveBeenCalledTimes(2);
      expect(result.current.viagem?.id).toBe("v-1");
    });

    it("o servidor dizer 'sem viagem' (expirou, encerrou em outro aparelho) volta a 'aguardando'", async () => {
      jest.useFakeTimers();
      buscarMock.mockResolvedValueOnce(EM_VIAGEM).mockResolvedValue(AGUARDANDO);

      const { result } = montar();
      await act(async () => {
        await Promise.resolve();
      });
      await act(async () => {
        jest.advanceTimersByTime(INTERVALO_VIAGEM_MS);
      });

      expect(result.current.viagem).toBeNull();
    });

    it("ao desmontar, para o intervalo", async () => {
      jest.useFakeTimers();
      buscarMock.mockResolvedValue(EM_VIAGEM);

      const { unmount } = montar();
      await act(async () => {
        await Promise.resolve();
      });
      unmount();
      await act(async () => {
        jest.advanceTimersByTime(INTERVALO_VIAGEM_MS * 3);
      });

      expect(buscarMock).toHaveBeenCalledTimes(1);
    });

    it("resposta atrasada de uma consulta ANTIGA não 'desencerra' a viagem encerrada agora", async () => {
      jest.useFakeTimers();
      const atrasada = adiavel<typeof EM_VIAGEM>();
      buscarMock
        .mockResolvedValueOnce(EM_VIAGEM) // abertura
        .mockReturnValueOnce(atrasada.promessa) // polling, que vai demorar
        .mockResolvedValue(AGUARDANDO); // releitura depois do "Cheguei"
      encerrarMock.mockResolvedValue(undefined);

      const { result } = montar();
      await act(async () => {
        await Promise.resolve();
      });
      await act(async () => {
        jest.advanceTimersByTime(INTERVALO_VIAGEM_MS);
      });

      await act(async () => {
        await result.current.encerrar();
      });
      expect(result.current.viagem).toBeNull();

      // Só agora a consulta antiga responde — dizendo que ainda há viagem.
      await act(async () => {
        atrasada.resolver(EM_VIAGEM);
        await Promise.resolve();
      });

      expect(result.current.viagem).toBeNull();
    });
  });

  describe("embarcar (Cenários 1 e 4)", () => {
    const DADOS = { numeroLinha: "0.110", lat: -15.8, lng: -48.05 };

    it("registra e passa a 'em viagem' relendo do servidor", async () => {
      buscarMock.mockResolvedValueOnce(AGUARDANDO).mockResolvedValue(EM_VIAGEM);
      embarcarMock.mockResolvedValue(undefined);

      const { result } = montar();
      await waitFor(() => expect(result.current.carregando).toBe(false));

      let r: unknown;
      await act(async () => {
        r = await result.current.embarcar(DADOS);
      });

      expect(r).toEqual({ ok: true });
      expect(embarcarMock).toHaveBeenCalledWith(DADOS);
      expect(result.current.viagem?.id).toBe("v-1");
    });

    it("422 (sem veículo perto): devolve a frase do servidor e NÃO muda de estado", async () => {
      buscarMock.mockResolvedValue(AGUARDANDO);
      embarcarMock.mockRejectedValue(new ViagemError("Não conseguimos confirmar seu embarque.", 422));

      const { result } = montar();
      await waitFor(() => expect(result.current.carregando).toBe(false));

      let r: unknown;
      await act(async () => {
        r = await result.current.embarcar(DADOS);
      });

      expect(r).toEqual({ ok: false, mensagem: "Não conseguimos confirmar seu embarque." });
      expect(result.current.viagem).toBeNull();
      expect(buscarMock).toHaveBeenCalledTimes(1); // sem releitura inútil
    });

    it("409 (já em viagem): a tela estava desatualizada, então relê e passa a mostrar a viagem", async () => {
      buscarMock.mockResolvedValueOnce(AGUARDANDO).mockResolvedValue(EM_VIAGEM);
      embarcarMock.mockRejectedValue(new ViagemError("Você já está em uma viagem.", 409));

      const { result } = montar();
      await waitFor(() => expect(result.current.carregando).toBe(false));

      let r: { ok: boolean; mensagem?: string } | undefined;
      await act(async () => {
        r = await result.current.embarcar(DADOS);
      });

      expect(r).toEqual({ ok: false, mensagem: "Você já está em uma viagem." });
      expect(result.current.viagem?.id).toBe("v-1");
    });

    it("erro inesperado (não ViagemError) vira a mensagem padrão, sem vazar texto técnico", async () => {
      buscarMock.mockResolvedValue(AGUARDANDO);
      embarcarMock.mockRejectedValue(new TypeError("x is not a function"));

      const { result } = montar();
      await waitFor(() => expect(result.current.carregando).toBe(false));

      let r: { ok: boolean; mensagem?: string } | undefined;
      await act(async () => {
        r = await result.current.embarcar(DADOS);
      });

      expect(r?.ok).toBe(false);
      expect(r?.mensagem).toBe("Não foi possível registrar o embarque. Tente novamente.");
    });

    it("se a releitura falhar logo depois de embarcar, tenta de novo antes de contradizer o que aconteceu", async () => {
      buscarMock
        .mockResolvedValueOnce(AGUARDANDO) // abertura
        .mockResolvedValueOnce(FALHA) // 1ª releitura: soluço de rede
        .mockResolvedValue(EM_VIAGEM); // 2ª releitura
      embarcarMock.mockResolvedValue(undefined);

      const { result } = montar();
      await waitFor(() => expect(result.current.carregando).toBe(false));

      await act(async () => {
        await result.current.embarcar(DADOS);
      });

      expect(result.current.viagem?.id).toBe("v-1");
      expect(buscarMock).toHaveBeenCalledTimes(3);
    });

    it("`ocupado` fica verdadeiro durante a ação (para travar o botão) e volta ao fim", async () => {
      buscarMock.mockResolvedValue(AGUARDANDO);
      const demorada = adiavel<void>();
      embarcarMock.mockReturnValue(demorada.promessa);

      const { result } = montar();
      await waitFor(() => expect(result.current.carregando).toBe(false));

      let acao!: Promise<unknown>;
      act(() => {
        acao = result.current.embarcar(DADOS);
      });
      await waitFor(() => expect(result.current.ocupado).toBe(true));

      await act(async () => {
        demorada.resolver();
        await acao;
      });
      expect(result.current.ocupado).toBe(false);
    });
  });

  describe("definirDestino", () => {
    it("sem viagem, não chama o servidor e explica", async () => {
      buscarMock.mockResolvedValue(AGUARDANDO);

      const { result } = montar();
      await waitFor(() => expect(result.current.carregando).toBe(false));

      let r: unknown;
      await act(async () => {
        r = await result.current.definirDestino("PR-C");
      });

      expect(r).toEqual({ ok: false, mensagem: "Você não está em uma viagem." });
      expect(destinoMock).not.toHaveBeenCalled();
    });

    it("em viagem, manda o id da viagem e o código, e relê", async () => {
      buscarMock
        .mockResolvedValueOnce(EM_VIAGEM)
        .mockResolvedValue({ falhou: false, viagem: viagem({ paradaDestinoCodigo: "PR-C" }) });
      destinoMock.mockResolvedValue(undefined);

      const { result } = montar();
      await waitFor(() => expect(result.current.viagem).not.toBeNull());

      await act(async () => {
        await result.current.definirDestino("PR-C");
      });

      expect(destinoMock).toHaveBeenCalledWith("v-1", "PR-C");
      expect(result.current.viagem?.paradaDestinoCodigo).toBe("PR-C");
    });

    it("`null` tira o destino", async () => {
      buscarMock.mockResolvedValue({ falhou: false, viagem: viagem({ paradaDestinoCodigo: "PR-C" }) });
      destinoMock.mockResolvedValue(undefined);

      const { result } = montar();
      await waitFor(() => expect(result.current.viagem).not.toBeNull());

      await act(async () => {
        await result.current.definirDestino(null);
      });

      expect(destinoMock).toHaveBeenCalledWith("v-1", null);
    });

    it("422: devolve a frase do servidor", async () => {
      buscarMock.mockResolvedValue(EM_VIAGEM);
      destinoMock.mockRejectedValue(new ViagemError("A parada de destino não faz parte desta linha.", 422));

      const { result } = montar();
      await waitFor(() => expect(result.current.viagem).not.toBeNull());

      let r: unknown;
      await act(async () => {
        r = await result.current.definirDestino("PR-Z");
      });

      expect(r).toEqual({ ok: false, mensagem: "A parada de destino não faz parte desta linha." });
    });

    it("409 (a viagem já tinha terminado): relê e volta a 'aguardando'", async () => {
      buscarMock.mockResolvedValueOnce(EM_VIAGEM).mockResolvedValue(AGUARDANDO);
      destinoMock.mockRejectedValue(new ViagemError("Esta viagem já foi encerrada.", 409));

      const { result } = montar();
      await waitFor(() => expect(result.current.viagem).not.toBeNull());

      await act(async () => {
        await result.current.definirDestino("PR-C");
      });

      expect(result.current.viagem).toBeNull();
    });
  });

  describe("encerrar (Cenário 3)", () => {
    it("encerra e volta ao estado normal", async () => {
      buscarMock.mockResolvedValueOnce(EM_VIAGEM).mockResolvedValue(AGUARDANDO);
      encerrarMock.mockResolvedValue(undefined);

      const { result } = montar();
      await waitFor(() => expect(result.current.viagem).not.toBeNull());

      let r: unknown;
      await act(async () => {
        r = await result.current.encerrar();
      });

      expect(r).toEqual({ ok: true });
      expect(encerrarMock).toHaveBeenCalledWith("v-1");
      expect(result.current.viagem).toBeNull();
    });

    it("sem viagem, não chama o servidor e já está tudo certo", async () => {
      buscarMock.mockResolvedValue(AGUARDANDO);

      const { result } = montar();
      await waitFor(() => expect(result.current.carregando).toBe(false));

      let r: unknown;
      await act(async () => {
        r = await result.current.encerrar();
      });

      expect(r).toEqual({ ok: true });
      expect(encerrarMock).not.toHaveBeenCalled();
    });

    it("falha ao encerrar mantém 'em viagem' e devolve a mensagem", async () => {
      buscarMock.mockResolvedValue(EM_VIAGEM);
      encerrarMock.mockRejectedValue(new ViagemError("Não foi possível encerrar a viagem. Tente novamente."));

      const { result } = montar();
      await waitFor(() => expect(result.current.viagem).not.toBeNull());

      let r: { ok: boolean; mensagem?: string } | undefined;
      await act(async () => {
        r = await result.current.encerrar();
      });

      expect(r?.ok).toBe(false);
      expect(r?.mensagem).toMatch(/encerrar a viagem/);
      expect(result.current.viagem?.id).toBe("v-1");
    });
  });

  it("desmontar no meio de uma ação não provoca atualização de estado depois", async () => {
    buscarMock.mockResolvedValue(AGUARDANDO);
    const demorada = adiavel<void>();
    embarcarMock.mockReturnValue(demorada.promessa);
    const erro = jest.spyOn(console, "error").mockImplementation(() => {});

    const { result, unmount } = montar();
    await waitFor(() => expect(result.current.carregando).toBe(false));

    let acao!: Promise<unknown>;
    act(() => {
      acao = result.current.embarcar({ numeroLinha: "0.110", lat: 1, lng: 2 });
    });
    unmount();
    await act(async () => {
      demorada.resolver();
      await acao;
    });

    expect(erro).not.toHaveBeenCalled();
    erro.mockRestore();
  });
});
