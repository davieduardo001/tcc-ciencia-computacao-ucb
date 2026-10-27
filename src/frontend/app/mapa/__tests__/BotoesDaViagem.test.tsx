import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import {
  buscarViagemAtiva,
  definirDestinoDaViagem,
  embarcarNoOnibus,
  ViagemAtiva,
  ViagemError,
} from "@/lib/api";
import { BotaoDescerNestaParada, BotaoPegueiNaRota, BotaoPegueiOnibus } from "../BotoesDaViagem";
import { ViagemProvider } from "../ViagemContext";

jest.mock("@/lib/api", () => ({
  ...jest.requireActual("@/lib/api"),
  buscarViagemAtiva: jest.fn(),
  embarcarNoOnibus: jest.fn(),
  definirDestinoDaViagem: jest.fn(),
}));

const buscarMock = buscarViagemAtiva as jest.Mock;
const embarcarMock = embarcarNoOnibus as jest.Mock;
const destinoMock = definirDestinoDaViagem as jest.Mock;

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
const POSICAO = { lat: -15.8, lng: -48.05 };

function comProvider(ui: React.ReactNode) {
  return render(<ViagemProvider>{ui}</ViagemProvider>);
}

describe("BotaoPegueiOnibus", () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  it("aguardando e com localização: oferece 'Peguei este ônibus'", async () => {
    buscarMock.mockResolvedValue(AGUARDANDO);

    comProvider(<BotaoPegueiOnibus numeroLinha="0.110" prefixo="440001" posicaoDoUsuario={POSICAO} />);

    expect(await screen.findByRole("button", { name: "Peguei este ônibus" })).toBeEnabled();
  });

  it("tocar manda a linha DESTE ônibus e a posição do usuário (que o servidor só confere)", async () => {
    buscarMock.mockResolvedValueOnce(AGUARDANDO).mockResolvedValue({ falhou: false, viagem: viagem() });
    embarcarMock.mockResolvedValue(undefined);

    comProvider(<BotaoPegueiOnibus numeroLinha="0.110" prefixo="440001" posicaoDoUsuario={POSICAO} />);
    fireEvent.click(await screen.findByRole("button", { name: "Peguei este ônibus" }));

    await waitFor(() =>
      expect(embarcarMock).toHaveBeenCalledWith({
        numeroLinha: "0.110",
        lat: -15.8,
        lng: -48.05,
        veiculoPrefixo: "440001", // issue #216: só ESTE ônibus confirma o embarque
      })
    );
    // Espera a tela assentar no estado novo (e o botão virar o aviso).
    expect(await screen.findByText("Você está neste ônibus.")).toBeInTheDocument();
  });

  it("sem localização, não há como confirmar: explica em vez de oferecer um botão que nunca funciona", async () => {
    buscarMock.mockResolvedValue(AGUARDANDO);

    comProvider(<BotaoPegueiOnibus numeroLinha="0.110" prefixo="440001" posicaoDoUsuario={null} />);

    expect(await screen.findByText(/Ative a localização/)).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("Cenário 4 — sem veículo perto: mostra a frase do servidor num alerta e o botão volta a funcionar", async () => {
    buscarMock.mockResolvedValue(AGUARDANDO);
    embarcarMock.mockRejectedValue(new ViagemError("Não conseguimos confirmar seu embarque.", 422));

    comProvider(<BotaoPegueiOnibus numeroLinha="0.110" prefixo="440001" posicaoDoUsuario={POSICAO} />);
    const botao = await screen.findByRole("button", { name: "Peguei este ônibus" });
    fireEvent.click(botao);

    expect(await screen.findByRole("alert")).toHaveTextContent("Não conseguimos confirmar seu embarque.");
    expect(botao).toBeEnabled();
  });

  it("tentar de novo limpa o erro anterior", async () => {
    buscarMock.mockResolvedValue(AGUARDANDO);
    embarcarMock
      .mockRejectedValueOnce(new ViagemError("Não conseguimos confirmar seu embarque.", 422))
      .mockImplementation(() => new Promise(() => {})); // segunda tentativa fica pendente

    comProvider(<BotaoPegueiOnibus numeroLinha="0.110" prefixo="440001" posicaoDoUsuario={POSICAO} />);
    const botao = await screen.findByRole("button", { name: "Peguei este ônibus" });
    fireEvent.click(botao);
    await screen.findByRole("alert");

    fireEvent.click(botao);

    await waitFor(() => expect(screen.queryByRole("alert")).not.toBeInTheDocument());
  });

  it("depois de embarcar NESTE ônibus, diz 'Você está neste ônibus' e some o botão", async () => {
    buscarMock.mockResolvedValue({ falhou: false, viagem: viagem() });

    comProvider(<BotaoPegueiOnibus numeroLinha="0.110" prefixo="440001" posicaoDoUsuario={POSICAO} />);

    expect(await screen.findByText("Você está neste ônibus.")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("em viagem em OUTRO ônibus, o popup deste não oferece nada (uma viagem por vez)", async () => {
    buscarMock.mockResolvedValue({ falhou: false, viagem: viagem({ veiculoPrefixo: "999999" }) });

    const { container } = comProvider(
      <BotaoPegueiOnibus numeroLinha="0.110" prefixo="440001" posicaoDoUsuario={POSICAO} />
    );

    await waitFor(() => expect(buscarMock).toHaveBeenCalled());
    await waitFor(() => expect(container).toBeEmptyDOMElement());
  });

  it("outro ônibus da MESMA linha com prefixo diferente também não é 'este ônibus'", async () => {
    buscarMock.mockResolvedValue({ falhou: false, viagem: viagem({ veiculoPrefixo: "999999" }) });

    comProvider(<BotaoPegueiOnibus numeroLinha="0.110" prefixo="440001" posicaoDoUsuario={POSICAO} />);

    await waitFor(() => expect(buscarMock).toHaveBeenCalled());
    expect(screen.queryByText("Você está neste ônibus.")).not.toBeInTheDocument();
  });

  it("o botão trava durante o pedido", async () => {
    buscarMock.mockResolvedValue(AGUARDANDO);
    let liberar!: () => void;
    embarcarMock.mockReturnValue(new Promise<void>((resolve) => (liberar = resolve)));

    comProvider(<BotaoPegueiOnibus numeroLinha="0.110" prefixo="440001" posicaoDoUsuario={POSICAO} />);
    const botao = await screen.findByRole("button", { name: "Peguei este ônibus" });
    fireEvent.click(botao);

    await waitFor(() => expect(botao).toBeDisabled());
    await act(async () => {
      liberar();
    });
    await waitFor(() => expect(botao).toBeEnabled());
  });
});

describe("BotaoDescerNestaParada", () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  it("aguardando: não aparece (só faz sentido em viagem)", async () => {
    buscarMock.mockResolvedValue(AGUARDANDO);

    const { container } = comProvider(
      <BotaoDescerNestaParada codigoDaParada="PR-C" numerosDasLinhas={["0.110"]} />
    );

    await waitFor(() => expect(buscarMock).toHaveBeenCalled());
    expect(container).toBeEmptyDOMElement();
  });

  it("em viagem, numa parada da linha: oferece 'Descer nesta parada'", async () => {
    buscarMock.mockResolvedValue({ falhou: false, viagem: viagem() });

    comProvider(<BotaoDescerNestaParada codigoDaParada="PR-C" numerosDasLinhas={["0.110", "875A"]} />);

    expect(await screen.findByRole("button", { name: "Descer nesta parada" })).toBeInTheDocument();
    expect(screen.getByText("Você está na linha 0.110.")).toBeInTheDocument();
  });

  it("parada por onde a linha da viagem NÃO passa: não aparece (o servidor recusaria)", async () => {
    buscarMock.mockResolvedValue({ falhou: false, viagem: viagem() });

    const { container } = comProvider(
      <BotaoDescerNestaParada codigoDaParada="PR-Z" numerosDasLinhas={["875A"]} />
    );

    await waitFor(() => expect(buscarMock).toHaveBeenCalled());
    await waitFor(() => expect(container).toBeEmptyDOMElement());
  });

  it("tocar define o destino com o CÓDIGO da parada", async () => {
    buscarMock
      .mockResolvedValueOnce({ falhou: false, viagem: viagem() })
      .mockResolvedValue({ falhou: false, viagem: viagem({ paradaDestinoCodigo: "PR-C" }) });
    destinoMock.mockResolvedValue(undefined);

    comProvider(<BotaoDescerNestaParada codigoDaParada="PR-C" numerosDasLinhas={["0.110"]} />);
    fireEvent.click(await screen.findByRole("button", { name: "Descer nesta parada" }));

    await waitFor(() => expect(destinoMock).toHaveBeenCalledWith("v-1", "PR-C"));
    // A tela assenta: a parada passa a ser o destino.
    expect(await screen.findByRole("button", { name: "Tirar destino" })).toBeInTheDocument();
  });

  it("se esta já é o destino, diz isso e oferece 'Tirar destino' (que manda null)", async () => {
    buscarMock
      .mockResolvedValueOnce({ falhou: false, viagem: viagem({ paradaDestinoCodigo: "PR-C" }) })
      .mockResolvedValue({ falhou: false, viagem: viagem() });
    destinoMock.mockResolvedValue(undefined);

    comProvider(<BotaoDescerNestaParada codigoDaParada="PR-C" numerosDasLinhas={["0.110"]} />);

    expect(await screen.findByText("Esta é a sua parada de destino na linha 0.110.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Tirar destino" }));
    await waitFor(() => expect(destinoMock).toHaveBeenCalledWith("v-1", null));
    expect(await screen.findByRole("button", { name: "Descer nesta parada" })).toBeInTheDocument();
  });

  it("outra parada diferente do destino atual continua oferecendo 'Descer nesta parada' (troca)", async () => {
    buscarMock.mockResolvedValue({ falhou: false, viagem: viagem({ paradaDestinoCodigo: "PR-C" }) });

    comProvider(<BotaoDescerNestaParada codigoDaParada="PR-D" numerosDasLinhas={["0.110"]} />);

    expect(await screen.findByRole("button", { name: "Descer nesta parada" })).toBeInTheDocument();
  });

  it("422: mostra a frase do servidor num alerta", async () => {
    buscarMock.mockResolvedValue({ falhou: false, viagem: viagem() });
    destinoMock.mockRejectedValue(new ViagemError("A parada de destino não faz parte desta linha.", 422));

    comProvider(<BotaoDescerNestaParada codigoDaParada="PR-C" numerosDasLinhas={["0.110"]} />);
    fireEvent.click(await screen.findByRole("button", { name: "Descer nesta parada" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("não faz parte desta linha");
  });
});

// ---------------------------------------------------------------------------
// Issue #190 — "Peguei este ônibus" a partir de um trecho da rota
// ---------------------------------------------------------------------------

describe("BotaoPegueiNaRota", () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  it("aguardando e com localização: oferece 'Peguei este ônibus'", async () => {
    buscarMock.mockResolvedValue(AGUARDANDO);

    comProvider(<BotaoPegueiNaRota numeroLinha="0.110" paradaDestinoCodigo="PR-D" posicaoDoUsuario={POSICAO} />);

    expect(await screen.findByRole("button", { name: "Peguei este ônibus" })).toBeEnabled();
  });

  it("tocar manda a linha do trecho, a posição e a parada de DESEMBARQUE como destino", async () => {
    buscarMock.mockResolvedValueOnce(AGUARDANDO).mockResolvedValue({ falhou: false, viagem: viagem() });
    embarcarMock.mockResolvedValue(undefined);

    comProvider(<BotaoPegueiNaRota numeroLinha="0.110" paradaDestinoCodigo="PR-D" posicaoDoUsuario={POSICAO} />);
    fireEvent.click(await screen.findByRole("button", { name: "Peguei este ônibus" }));

    await waitFor(() =>
      expect(embarcarMock).toHaveBeenCalledWith({
        numeroLinha: "0.110",
        lat: -15.8,
        lng: -48.05,
        paradaDestinoCodigo: "PR-D",
      })
    );
    expect(await screen.findByText("Você está nesta linha.")).toBeInTheDocument();
  });

  it("trecho sem código de parada: embarca sem destino (a pessoa escolhe depois, no mapa)", async () => {
    buscarMock.mockResolvedValueOnce(AGUARDANDO).mockResolvedValue({ falhou: false, viagem: viagem() });
    embarcarMock.mockResolvedValue(undefined);

    comProvider(<BotaoPegueiNaRota numeroLinha="0.110" paradaDestinoCodigo={null} posicaoDoUsuario={POSICAO} />);
    fireEvent.click(await screen.findByRole("button", { name: "Peguei este ônibus" }));

    await waitFor(() => expect(embarcarMock).toHaveBeenCalledTimes(1));
    const enviado = embarcarMock.mock.calls[0][0];
    expect(enviado).toEqual({ numeroLinha: "0.110", lat: -15.8, lng: -48.05 });
    expect("paradaDestinoCodigo" in enviado).toBe(false);
  });

  it("sem localização, explica em vez de oferecer um botão que nunca funciona", async () => {
    buscarMock.mockResolvedValue(AGUARDANDO);

    comProvider(<BotaoPegueiNaRota numeroLinha="0.110" paradaDestinoCodigo="PR-D" posicaoDoUsuario={null} />);

    expect(await screen.findByText(/Ative a localização/)).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("sem ônibus perto: mostra a frase do servidor num alerta e o botão volta a funcionar", async () => {
    buscarMock.mockResolvedValue(AGUARDANDO);
    embarcarMock.mockRejectedValue(new ViagemError("Não conseguimos confirmar seu embarque.", 422));

    comProvider(<BotaoPegueiNaRota numeroLinha="0.110" paradaDestinoCodigo="PR-D" posicaoDoUsuario={POSICAO} />);
    const botao = await screen.findByRole("button", { name: "Peguei este ônibus" });
    fireEvent.click(botao);

    expect(await screen.findByRole("alert")).toHaveTextContent("Não conseguimos confirmar seu embarque.");
    expect(botao).toBeEnabled();
  });

  it("já em viagem NESTA linha: diz isso e não oferece o botão", async () => {
    buscarMock.mockResolvedValue({ falhou: false, viagem: viagem({ numeroLinha: "0.110" }) });

    comProvider(<BotaoPegueiNaRota numeroLinha="0.110" paradaDestinoCodigo="PR-D" posicaoDoUsuario={POSICAO} />);

    expect(await screen.findByText("Você está nesta linha.")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("em viagem em OUTRA linha (ex.: o 2º trecho de uma baldeação): não mostra nada", async () => {
    buscarMock.mockResolvedValue({ falhou: false, viagem: viagem({ numeroLinha: "0.186" }) });

    const { container } = comProvider(
      <BotaoPegueiNaRota numeroLinha="0.110" paradaDestinoCodigo="PR-D" posicaoDoUsuario={POSICAO} />
    );

    await waitFor(() => expect(buscarMock).toHaveBeenCalled());
    await waitFor(() => expect(container).toBeEmptyDOMElement());
  });

  it("enquanto a ação está em andamento, o botão fica desabilitado (sem toque duplo)", async () => {
    buscarMock.mockResolvedValue(AGUARDANDO);
    let concluir!: () => void;
    embarcarMock.mockReturnValue(new Promise<void>((resolve) => (concluir = resolve)));

    comProvider(<BotaoPegueiNaRota numeroLinha="0.110" paradaDestinoCodigo="PR-D" posicaoDoUsuario={POSICAO} />);
    const botao = await screen.findByRole("button", { name: "Peguei este ônibus" });
    fireEvent.click(botao);

    await waitFor(() => expect(botao).toBeDisabled());
    await act(async () => {
      concluir();
    });
  });
});
