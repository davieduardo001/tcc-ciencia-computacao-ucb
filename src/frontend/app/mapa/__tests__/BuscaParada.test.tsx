import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import BuscaParada, { formatarDistancia } from "../BuscaParada";
import { buscarParadas } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  buscarParadas: jest.fn(),
  BuscarParadasError: class BuscarParadasError extends Error {},
}));

const buscarParadasMock = buscarParadas as jest.Mock;

const PARADA_A = {
  codigo: "PR-1",
  nome: "Estação Ceilândia Centro",
  lat: -15.81,
  lng: -48.1,
  qtdLinhas: 8,
  distanciaM: null,
};

const PARADA_SEM_NOME = {
  codigo: "PR-2",
  nome: "",
  lat: -15.82,
  lng: -48.11,
  qtdLinhas: 1,
  distanciaM: 1240,
};

function montar() {
  const props = {
    onFechar: jest.fn(),
    onResultado: jest.fn(),
    onSelecionar: jest.fn(),
  };
  render(<BuscaParada {...props} />);
  return props;
}

function buscar(termo: string) {
  fireEvent.change(screen.getByLabelText("Nome, referência ou endereço"), {
    target: { value: termo },
  });
  fireEvent.submit(screen.getByRole("search"));
}

describe("BuscaParada (US #21)", () => {
  beforeEach(() => {
    buscarParadasMock.mockReset();
  });

  it("Cenário 1: lista as paradas encontradas pelo nome e avisa o mapa", async () => {
    const resultado = { tipo: "nome", paradas: [PARADA_A], referencia: null };
    buscarParadasMock.mockResolvedValue(resultado);
    const props = montar();

    buscar("estacao ceilandia");

    expect(await screen.findByText("Estação Ceilândia Centro")).toBeInTheDocument();
    expect(screen.getByText("1 parada encontrada")).toBeInTheDocument();
    expect(screen.getByText("8 linhas")).toBeInTheDocument();
    expect(buscarParadasMock).toHaveBeenCalledWith("estacao ceilandia");
    expect(props.onResultado).toHaveBeenCalledWith(resultado);
  });

  it("Cenário 2: diz que as paradas estão perto do lugar e mostra a distância", async () => {
    buscarParadasMock.mockResolvedValue({
      tipo: "endereco",
      paradas: [PARADA_SEM_NOME],
      referencia: { nome: "Hospital de Taguatinga", endereco: "", lat: -15.8, lng: -48.1 },
    });
    montar();

    buscar("hospital de taguatinga");

    expect(
      await screen.findByText(/1 parada encontrada perto de Hospital de Taguatinga/)
    ).toBeInTheDocument();
    expect(screen.getByText("1,2 km · 1 linha")).toBeInTheDocument();
    // Abrigo só com CEP no SEMOB: rótulo neutro em vez de vazio.
    expect(screen.getByText("Parada sem nome cadastrado")).toBeInTheDocument();
  });

  it("Cenário 3: mostra a mensagem de nenhum resultado e limpa o mapa", async () => {
    buscarParadasMock.mockResolvedValue({ tipo: "nenhum", paradas: [], referencia: null });
    const props = montar();

    buscar("xyzw");

    expect(await screen.findByText(/Nenhuma parada encontrada para “xyzw”/)).toBeInTheDocument();
    expect(props.onResultado).toHaveBeenCalledWith(null);
  });

  it("tocar numa parada da lista pede ao mapa para abri-la", async () => {
    buscarParadasMock.mockResolvedValue({ tipo: "nome", paradas: [PARADA_A], referencia: null });
    const props = montar();

    buscar("estacao");
    fireEvent.click(await screen.findByText("Estação Ceilândia Centro"));

    expect(props.onSelecionar).toHaveBeenCalledWith(PARADA_A);
  });

  it("falha de rede vira mensagem de erro, diferente de 'nenhum resultado'", async () => {
    const { BuscarParadasError } = jest.requireMock("@/lib/api");
    buscarParadasMock.mockRejectedValue(new BuscarParadasError("Sem conexão."));
    montar();

    buscar("estacao");

    expect(await screen.findByRole("alert")).toHaveTextContent("Sem conexão.");
    expect(screen.queryByText(/Nenhuma parada encontrada/)).not.toBeInTheDocument();
  });

  it("avisa que a busca sai pelo Enter enquanto o termo não foi buscado (#236)", async () => {
    buscarParadasMock.mockResolvedValue({ paradas: [], origem: "banco" });
    montar();
    const campo = screen.getByLabelText("Nome, referência ou endereço");

    fireEvent.change(campo, { target: { value: "terminal" } });
    expect(screen.getByText("Pressione Enter para buscar.")).toBeInTheDocument();
    expect(buscarParadasMock).not.toHaveBeenCalled();

    fireEvent.submit(screen.getByRole("search"));
    await waitFor(() =>
      expect(screen.queryByText("Pressione Enter para buscar.")).not.toBeInTheDocument()
    );

    fireEvent.change(campo, { target: { value: "terminal sul" } });
    expect(screen.getByText("Pressione Enter para buscar.")).toBeInTheDocument();
  });

  it("não busca com menos de 3 letras", () => {
    montar();

    buscar("ab");

    expect(screen.getByText("Digite pelo menos 3 letras.")).toBeInTheDocument();
    expect(buscarParadasMock).not.toHaveBeenCalled();
  });

  it("ignora a resposta de uma busca antiga que chega depois da mais recente", async () => {
    let resolverAntiga: (v: unknown) => void = () => {};
    buscarParadasMock
      .mockImplementationOnce(() => new Promise((resolve) => (resolverAntiga = resolve)))
      .mockResolvedValueOnce({ tipo: "nome", paradas: [PARADA_A], referencia: null });
    montar();

    buscar("primeira");
    buscar("estacao");
    expect(await screen.findByText("Estação Ceilândia Centro")).toBeInTheDocument();

    await act(async () => {
      resolverAntiga({ tipo: "nenhum", paradas: [], referencia: null });
    });

    expect(screen.getByText("Estação Ceilândia Centro")).toBeInTheDocument();
    expect(screen.queryByText(/Nenhuma parada encontrada/)).not.toBeInTheDocument();
  });

  it("fechar limpa os destaques do mapa", async () => {
    const props = montar();

    fireEvent.click(screen.getByRole("button", { name: "Fechar busca de parada" }));

    await waitFor(() => expect(props.onFechar).toHaveBeenCalled());
    expect(props.onResultado).toHaveBeenCalledWith(null);
  });
});

describe("formatarDistancia", () => {
  it("usa metros abaixo de 1 km e km com vírgula acima", () => {
    expect(formatarDistancia(120)).toBe("120 m");
    expect(formatarDistancia(999.6)).toBe("1 km");
    expect(formatarDistancia(1240)).toBe("1,2 km");
  });
});
