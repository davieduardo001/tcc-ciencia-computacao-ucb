import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import OcorrenciasPage from "../page";
import {
  listarOcorrencias,
  ListarOcorrenciasError,
  OcorrenciaListada,
} from "@/lib/api";

jest.mock("@/lib/api", () => {
  const actual = jest.requireActual("@/lib/api");
  return {
    ...actual,
    buscarUsuarioAtual: jest.fn().mockResolvedValue(null),
    logoutUsuario: jest.fn(),
    sugerirLinhas: jest.fn().mockResolvedValue([]),
    listarOcorrencias: jest.fn(),
  };
});

const pushMock = jest.fn();
let paramsLinha = "";
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
  useSearchParams: () => ({
    get: (chave: string) => (chave === "linha" ? paramsLinha || null : null),
  }),
}));

const listarMock = listarOcorrencias as jest.Mock;

const AGORA = new Date("2026-10-14T15:00:00Z").getTime();

function ocorrencia(parcial: Partial<OcorrenciaListada> = {}): OcorrenciaListada {
  return {
    id: "1",
    linhaNumero: "0.110",
    tipo: "atraso",
    descricao: null,
    local: null,
    status: "pendente",
    contadorConfirmacoes: 0,
    criadoEm: "2026-10-14T14:55:00Z",
    expiraEm: "2026-10-14T15:25:00Z",
    ...parcial,
  };
}

describe("OcorrenciasPage (lista — US #24)", () => {
  beforeEach(() => {
    pushMock.mockReset();
    listarMock.mockReset();
    listarMock.mockResolvedValue([]);
    paramsLinha = "";
    jest.spyOn(Date, "now").mockReturnValue(AGORA);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("cenário 1: ocorrência confirmada aparece como confirmada, com o número de confirmações", async () => {
    listarMock.mockResolvedValue([
      ocorrencia({ id: "a", tipo: "nao_passou", status: "confirmada", contadorConfirmacoes: 3 }),
    ]);

    render(<OcorrenciasPage />);

    expect(await screen.findByText("Confirmada · 3 confirmações")).toBeInTheDocument();
    expect(screen.getByText("Ônibus não passou — 0.110").closest("li")).toHaveClass("confirmada");
  });

  it("cenário 2: ocorrência com um reporte aparece como aguardando confirmação", async () => {
    listarMock.mockResolvedValue([ocorrencia({ status: "pendente" })]);

    render(<OcorrenciasPage />);

    expect(await screen.findByText("Aguardando confirmação")).toBeInTheDocument();
    expect(screen.getByText("Atraso — 0.110").closest("li")).toHaveClass("pendente");
  });

  it("confirmada com uma única confirmação usa o singular", async () => {
    listarMock.mockResolvedValue([ocorrencia({ status: "confirmada", contadorConfirmacoes: 1 })]);

    render(<OcorrenciasPage />);

    expect(await screen.findByText("Confirmada · 1 confirmação")).toBeInTheDocument();
  });

  it("tipo de exibição imediata (sem confirmações) aparece só como confirmada", async () => {
    listarMock.mockResolvedValue([
      ocorrencia({ tipo: "acidente", status: "confirmada", contadorConfirmacoes: 0 }),
    ]);

    render(<OcorrenciasPage />);

    expect(await screen.findByText("Confirmada")).toBeInTheDocument();
  });

  it("mostra local e descrição quando existem", async () => {
    listarMock.mockResolvedValue([
      ocorrencia({ local: "Parada W3 Sul", descricao: "Esperando há 25 min" }),
    ]);

    render(<OcorrenciasPage />);

    expect(await screen.findByText("Parada W3 Sul")).toBeInTheDocument();
    expect(screen.getByText("Esperando há 25 min")).toBeInTheDocument();
  });

  it("mostra há quanto tempo foi reportada, lendo o horário em UTC", async () => {
    listarMock.mockResolvedValue([
      ocorrencia({ id: "a", criadoEm: "2026-10-14T14:55:00Z" }),
      ocorrencia({ id: "b", linhaNumero: "0.222", criadoEm: "2026-10-14T12:00:00Z" }),
      ocorrencia({ id: "c", linhaNumero: "0.333", criadoEm: "2026-10-14T14:59:40Z" }),
    ]);

    render(<OcorrenciasPage />);

    expect(await screen.findByText("há 5 min")).toBeInTheDocument();
    expect(screen.getByText("há 3 h")).toBeInTheDocument();
    expect(screen.getByText("agora mesmo")).toBeInTheDocument();
  });

  it("tipo desconhecido não quebra a tela", async () => {
    listarMock.mockResolvedValue([
      ocorrencia({ tipo: "greve" as OcorrenciaListada["tipo"] }),
    ]);

    render(<OcorrenciasPage />);

    expect(await screen.findByText("greve — 0.110")).toBeInTheDocument();
  });

  it("lista vazia mostra o estado vazio", async () => {
    render(<OcorrenciasPage />);

    expect(await screen.findByText("Nenhuma ocorrência ativa no momento.")).toBeInTheDocument();
  });

  it("vindo do detalhe da linha, já filtra por ela", async () => {
    paramsLinha = "0.312";

    render(<OcorrenciasPage />);

    await waitFor(() => expect(listarMock).toHaveBeenCalledWith("0.312"));
    expect(screen.getByPlaceholderText("Ex: 0.110")).toHaveValue("0.312");
    expect(
      await screen.findByText("Nenhuma ocorrência ativa na linha 0.312.")
    ).toBeInTheDocument();
  });

  it("digitar no filtro busca de novo com a linha digitada", async () => {
    render(<OcorrenciasPage />);
    await waitFor(() => expect(listarMock).toHaveBeenCalledTimes(1));

    fireEvent.change(screen.getByPlaceholderText("Ex: 0.110"), { target: { value: "0.222" } });

    await waitFor(() => expect(listarMock).toHaveBeenLastCalledWith("0.222"));
  });

  it("o botão de limpar volta a listar todas", async () => {
    paramsLinha = "0.312";
    render(<OcorrenciasPage />);
    await waitFor(() => expect(listarMock).toHaveBeenCalledWith("0.312"));

    fireEvent.click(screen.getByRole("button", { name: "Limpar filtro de linha" }));

    await waitFor(() => expect(listarMock).toHaveBeenLastCalledWith(""));
    expect(screen.getByPlaceholderText("Ex: 0.110")).toHaveValue("");
  });

  it("o botão Reportar leva a linha filtrada para o formulário", async () => {
    paramsLinha = "0.110";
    render(<OcorrenciasPage />);

    expect(screen.getByRole("link", { name: /Reportar/ })).toHaveAttribute(
      "href",
      "/ocorrencias/reportar?linha=0.110"
    );
    await waitFor(() => expect(listarMock).toHaveBeenCalled());
  });

  it("sem filtro, o botão Reportar abre o formulário em branco", async () => {
    render(<OcorrenciasPage />);

    expect(screen.getByRole("link", { name: /Reportar/ })).toHaveAttribute(
      "href",
      "/ocorrencias/reportar"
    );
    await waitFor(() => expect(listarMock).toHaveBeenCalled());
  });

  it("sessão expirada redireciona para o login", async () => {
    listarMock.mockRejectedValue(
      new ListarOcorrenciasError("Sua sessão expirou. Faça login novamente.", true)
    );

    render(<OcorrenciasPage />);

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/login"));
  });

  it("falha do servidor mostra o erro sem redirecionar", async () => {
    listarMock.mockRejectedValue(new ListarOcorrenciasError("Não foi possível carregar as ocorrências."));

    render(<OcorrenciasPage />);

    expect(await screen.findByText("Não foi possível carregar as ocorrências.")).toBeInTheDocument();
    expect(pushMock).not.toHaveBeenCalled();
  });

  it("falha de rede (erro inesperado) também mostra o erro genérico", async () => {
    listarMock.mockRejectedValue(new TypeError("Failed to fetch"));

    render(<OcorrenciasPage />);

    expect(await screen.findByText("Não foi possível carregar as ocorrências.")).toBeInTheDocument();
  });
});
