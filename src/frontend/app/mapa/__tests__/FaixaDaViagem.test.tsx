import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { buscarViagemAtiva, encerrarViagem, ViagemAtiva, ViagemError } from "@/lib/api";
import FaixaDaViagem from "../FaixaDaViagem";
import { ViagemProvider } from "../ViagemContext";

jest.mock("@/lib/api", () => ({
  ...jest.requireActual("@/lib/api"),
  buscarViagemAtiva: jest.fn(),
  encerrarViagem: jest.fn(),
}));

const buscarMock = buscarViagemAtiva as jest.Mock;
const encerrarMock = encerrarViagem as jest.Mock;

const parada = (codigo: string, nome: string) => ({ codigo, nome, lat: 0, lng: 0 });

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
    proximaParada: parada("PR-B", "W3 Sul 502"),
    paradasRestantes: [],
    ...sobre,
  };
}

function renderizar() {
  return render(
    <ViagemProvider>
      <FaixaDaViagem />
    </ViagemProvider>
  );
}

describe("FaixaDaViagem", () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  it("aguardando: não aparece nada", async () => {
    buscarMock.mockResolvedValue({ falhou: false, viagem: null });

    const { container } = renderizar();
    await waitFor(() => expect(buscarMock).toHaveBeenCalled());

    expect(container).toBeEmptyDOMElement();
  });

  it("em viagem: mostra a linha e a próxima parada, numa região nomeada", async () => {
    buscarMock.mockResolvedValue({ falhou: false, viagem: viagem() });

    renderizar();

    const regiao = await screen.findByRole("region", { name: "Viagem em andamento" });
    expect(regiao).toHaveTextContent("Em viagem · linha 0.110");
    expect(screen.getByRole("status")).toHaveTextContent("Próxima parada: W3 Sul 502");
  });

  it("anuncia o texto numa região de status (leitor de tela acompanha a viagem)", async () => {
    buscarMock.mockResolvedValue({ falhou: false, viagem: viagem() });

    renderizar();

    expect(await screen.findByRole("status")).toBeInTheDocument();
  });

  it("sem sinal, o texto vira alerta", async () => {
    buscarMock.mockResolvedValue({ falhou: false, viagem: viagem({ sinal: "sem_sinal" }) });

    renderizar();

    const texto = await screen.findByText("Sem sinal do ônibus no momento");
    expect(texto).toHaveClass("alerta");
  });

  it("o texto normal não tem a classe de alerta", async () => {
    buscarMock.mockResolvedValue({ falhou: false, viagem: viagem() });

    renderizar();

    expect(await screen.findByText("Próxima parada: W3 Sul 502")).not.toHaveClass("alerta");
  });

  describe("detalhes (paradas que faltam)", () => {
    const COM_DESTINO = viagem({
      paradaDestinoCodigo: "PR-C",
      destino: { ...parada("PR-C", "Terminal"), ultrapassado: false },
      paradasRestantes: [parada("PR-B", "W3 Sul 502"), parada("PR-C", "Terminal")],
    });

    it("o botão tem nome acessível mesmo sem o rótulo visível (no celular só sobra o ícone)", async () => {
      buscarMock.mockResolvedValue({ falhou: false, viagem: COM_DESTINO });

      renderizar();

      // O nome contém o texto visível "Paradas" (WCAG 2.5.3 — rótulo no nome).
      const botao = await screen.findByRole("button", { name: "Paradas que faltam" });
      expect(botao.getAttribute("aria-label")).toContain(botao.textContent!.trim());
    });

    it("começam fechados, e o botão diz a que painel se refere", async () => {
      buscarMock.mockResolvedValue({ falhou: false, viagem: COM_DESTINO });

      renderizar();

      const botao = await screen.findByRole("button", { name: /Paradas/ });
      expect(botao).toHaveAttribute("aria-expanded", "false");
      const painel = document.getElementById(botao.getAttribute("aria-controls")!);
      expect(painel).toHaveAttribute("hidden");
    });

    it("abrem e fecham, mantendo aria-expanded em dia", async () => {
      buscarMock.mockResolvedValue({ falhou: false, viagem: COM_DESTINO });

      renderizar();
      const botao = await screen.findByRole("button", { name: /Paradas/ });

      fireEvent.click(botao);
      expect(botao).toHaveAttribute("aria-expanded", "true");
      expect(document.getElementById(botao.getAttribute("aria-controls")!)).not.toHaveAttribute("hidden");

      fireEvent.click(botao);
      expect(botao).toHaveAttribute("aria-expanded", "false");
    });

    it("listam as paradas até o destino, na ordem, marcando o destino", async () => {
      buscarMock.mockResolvedValue({ falhou: false, viagem: COM_DESTINO });

      renderizar();
      fireEvent.click(await screen.findByRole("button", { name: /Paradas/ }));

      const itens = screen.getAllByRole("listitem");
      expect(itens.map((i) => i.textContent)).toEqual(["W3 Sul 502", "Terminal · seu destino"]);
      expect(itens[1]).toHaveClass("destino");
    });

    it("sem destino, ensina como escolher um", async () => {
      buscarMock.mockResolvedValue({ falhou: false, viagem: viagem() });

      renderizar();
      fireEvent.click(await screen.findByRole("button", { name: /Paradas/ }));

      expect(screen.getByText(/Descer nesta parada/)).toBeInTheDocument();
    });

    it("destino ultrapassado: diz que o ônibus já passou, em vez de listar", async () => {
      buscarMock.mockResolvedValue({
        falhou: false,
        viagem: viagem({
          paradaDestinoCodigo: "PR-A",
          destino: { ...parada("PR-A", "Parada A"), ultrapassado: true },
        }),
      });

      renderizar();
      fireEvent.click(await screen.findByRole("button", { name: /Paradas/ }));

      expect(screen.getByText("O ônibus já passou da sua parada de destino.")).toBeInTheDocument();
      expect(screen.queryByRole("listitem")).not.toBeInTheDocument();
    });

    it("destino escolhido mas sem lista (trajeto indisponível): não diz que falta escolher", async () => {
      buscarMock.mockResolvedValue({
        falhou: false,
        viagem: viagem({
          paradaDestinoCodigo: "PR-C",
          destino: { ...parada("PR-C", "Terminal"), ultrapassado: false },
          paradasRestantes: [],
        }),
      });

      renderizar();
      fireEvent.click(await screen.findByRole("button", { name: /Paradas/ }));

      expect(screen.getByText(/Não conseguimos listar as paradas/)).toBeInTheDocument();
      expect(screen.queryByText(/Descer nesta parada/)).not.toBeInTheDocument();
    });
  });

  describe("Cheguei (Cenário 3)", () => {
    it("encerra a viagem e a faixa some", async () => {
      buscarMock.mockResolvedValueOnce({ falhou: false, viagem: viagem() }).mockResolvedValue({
        falhou: false,
        viagem: null,
      });
      encerrarMock.mockResolvedValue(undefined);

      renderizar();
      fireEvent.click(await screen.findByRole("button", { name: /Cheguei/ }));

      await waitFor(() => expect(screen.queryByRole("region")).not.toBeInTheDocument());
      expect(encerrarMock).toHaveBeenCalledWith("v-1");
    });

    it("falha ao encerrar: mostra o erro num alerta e a viagem continua", async () => {
      buscarMock.mockResolvedValue({ falhou: false, viagem: viagem() });
      encerrarMock.mockRejectedValue(new ViagemError("Não foi possível encerrar a viagem. Tente novamente."));

      renderizar();
      fireEvent.click(await screen.findByRole("button", { name: /Cheguei/ }));

      expect(await screen.findByRole("alert")).toHaveTextContent("Não foi possível encerrar a viagem");
      expect(screen.getByRole("region")).toBeInTheDocument();
    });

    it("tocar de novo depois de uma falha limpa o erro antigo", async () => {
      buscarMock.mockResolvedValueOnce({ falhou: false, viagem: viagem() }).mockResolvedValue({
        falhou: false,
        viagem: null,
      });
      encerrarMock
        .mockRejectedValueOnce(new ViagemError("Não foi possível encerrar a viagem. Tente novamente."))
        .mockResolvedValue(undefined);

      renderizar();
      const botao = await screen.findByRole("button", { name: /Cheguei/ });
      fireEvent.click(botao);
      await screen.findByRole("alert");

      fireEvent.click(botao);

      await waitFor(() => expect(screen.queryByRole("alert")).not.toBeInTheDocument());
    });

    it("o botão trava enquanto encerra (não dá para tocar duas vezes)", async () => {
      buscarMock.mockResolvedValue({ falhou: false, viagem: viagem() });
      let liberar!: () => void;
      encerrarMock.mockReturnValue(new Promise<void>((resolve) => (liberar = resolve)));

      renderizar();
      const botao = await screen.findByRole("button", { name: /Cheguei/ });
      fireEvent.click(botao);

      await waitFor(() => expect(botao).toBeDisabled());
      liberar();
      await waitFor(() => expect(botao).not.toBeDisabled());
    });
  });
});
