import { ReactNode } from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { buscarViagemAtiva, confirmarAvisoDeProximidade, ViagemAtiva } from "@/lib/api";
import AvisoDeProximidade from "../AvisoDeProximidade";
import { INTERVALO_VIAGEM_MS, ViagemProvider } from "../ViagemContext";

jest.mock("@/lib/api", () => ({
  ...jest.requireActual("@/lib/api"),
  buscarViagemAtiva: jest.fn(),
  confirmarAvisoDeProximidade: jest.fn(),
}));

const buscarMock = buscarViagemAtiva as jest.Mock;
const confirmarMock = confirmarAvisoDeProximidade as jest.Mock;

const AVISO = {
  id: "a-1",
  paradaCodigo: "PR-C",
  paradaNome: "Terminal Central",
  etaMinutos: 2.5,
  disparadoEm: "2026-10-14T15:30:00Z",
};

function viagem(sobre: Partial<ViagemAtiva> = {}): ViagemAtiva {
  return {
    id: "v-1",
    numeroLinha: "0.110",
    sentido: "IDA",
    veiculoPrefixo: "440001",
    paradaDestinoCodigo: "PR-C",
    embarcouEm: "2026-10-14T15:00:00Z",
    sinal: "ao_vivo",
    veiculo: null,
    destino: null,
    proximaParada: null,
    paradasRestantes: [],
    avisoProximidade: AVISO,
    ...sobre,
  };
}

function emViagem(sobre: Partial<ViagemAtiva> = {}) {
  return { falhou: false, viagem: viagem(sobre) };
}

function Tela({ children }: { children?: ReactNode }) {
  return (
    <ViagemProvider>
      <AvisoDeProximidade />
      {children}
    </ViagemProvider>
  );
}

describe("AvisoDeProximidade (US #172)", () => {
  beforeEach(() => {
    jest.resetAllMocks();
    confirmarMock.mockResolvedValue(undefined);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("sem aviso pendente, não mostra nada", async () => {
    buscarMock.mockResolvedValue(emViagem({ avisoProximidade: null }));

    render(<Tela />);

    await waitFor(() => expect(buscarMock).toHaveBeenCalled());
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("fora de viagem, não mostra nada", async () => {
    buscarMock.mockResolvedValue({ falhou: false, viagem: null });

    render(<Tela />);

    await waitFor(() => expect(buscarMock).toHaveBeenCalled());
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("com aviso pendente, anuncia que o ônibus está chegando e diz a parada", async () => {
    buscarMock.mockResolvedValue(emViagem());

    render(<Tela />);

    const aviso = await screen.findByRole("alert");
    expect(aviso).toHaveTextContent("Seu ônibus está chegando");
    expect(aviso).toHaveTextContent("Terminal Central");
    expect(screen.getByRole("button", { name: "Entendi" })).toBeInTheDocument();
  });

  it("não exibe o ETA do disparo, que envelhece", async () => {
    buscarMock.mockResolvedValue(emViagem());

    render(<Tela />);

    const aviso = await screen.findByRole("alert");
    expect(aviso).not.toHaveTextContent(/\d+\s*min/);
    expect(aviso).not.toHaveTextContent(/2[.,]5/);
  });

  it("parada sem nome: fala 'a sua parada' em vez de deixar um buraco", async () => {
    buscarMock.mockResolvedValue(
      emViagem({ avisoProximidade: { ...AVISO, paradaNome: null } })
    );

    render(<Tela />);

    expect(await screen.findByRole("alert")).toHaveTextContent("a sua parada");
  });

  it("'Entendi' esconde o aviso na hora e confirma com o servidor", async () => {
    buscarMock.mockResolvedValue(emViagem());
    render(<Tela />);
    await screen.findByRole("alert");

    fireEvent.click(screen.getByRole("button", { name: "Entendi" }));

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(confirmarMock).toHaveBeenCalledTimes(1);
    expect(confirmarMock).toHaveBeenCalledWith("v-1");
  });

  it("se a consulta seguinte ainda trouxer o mesmo aviso, ele não volta", async () => {
    // Ex.: a confirmação ao servidor ainda não chegou, ou falhou.
    jest.useFakeTimers();
    buscarMock.mockResolvedValue(emViagem());
    render(<Tela />);
    await screen.findByRole("alert");
    fireEvent.click(screen.getByRole("button", { name: "Entendi" }));

    await act(async () => {
      jest.advanceTimersByTime(INTERVALO_VIAGEM_MS);
    });

    expect(buscarMock.mock.calls.length).toBeGreaterThan(1);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(confirmarMock).toHaveBeenCalledTimes(1);
  });

  it("um aviso novo (outro id) aparece mesmo depois de dispensar o anterior", async () => {
    jest.useFakeTimers();
    buscarMock.mockResolvedValue(emViagem());
    render(<Tela />);
    await screen.findByRole("alert");
    fireEvent.click(screen.getByRole("button", { name: "Entendi" }));

    buscarMock.mockResolvedValue(
      emViagem({
        avisoProximidade: { ...AVISO, id: "a-2", paradaNome: "Hospital Regional" },
      })
    );
    await act(async () => {
      jest.advanceTimersByTime(INTERVALO_VIAGEM_MS);
    });

    expect(await screen.findByRole("alert")).toHaveTextContent("Hospital Regional");
  });

  it("encerrada a viagem, o aviso some", async () => {
    jest.useFakeTimers();
    buscarMock.mockResolvedValue(emViagem());
    render(<Tela />);
    await screen.findByRole("alert");

    buscarMock.mockResolvedValue({ falhou: false, viagem: null });
    await act(async () => {
      jest.advanceTimersByTime(INTERVALO_VIAGEM_MS);
    });

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("falha de rede na consulta não apaga um aviso que ainda não foi visto", async () => {
    jest.useFakeTimers();
    buscarMock.mockResolvedValue(emViagem());
    render(<Tela />);
    await screen.findByRole("alert");

    buscarMock.mockResolvedValue({ falhou: true });
    await act(async () => {
      jest.advanceTimersByTime(INTERVALO_VIAGEM_MS);
    });

    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("sem Provider (tela solta), não renderiza nada e não quebra", () => {
    render(<AvisoDeProximidade />);

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
