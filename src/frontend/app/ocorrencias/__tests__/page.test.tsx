import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import OcorrenciasPage from "../page";
import {
  listarOcorrencias,
  confirmarOcorrencia,
  ListarOcorrenciasError,
  ConfirmarOcorrenciaError,
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
    confirmarOcorrencia: jest.fn(),
    ConfirmarOcorrenciaError: class ConfirmarOcorrenciaError extends Error {
      status: number;
      constructor(message: string, status: number) {
        super(message);
        this.status = status;
      }
    },
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
const confirmarMock = confirmarOcorrencia as jest.Mock;

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
    ehAutor: false,
    ...parcial,
  };
}

describe("OcorrenciasPage (lista — US #24)", () => {
  beforeEach(() => {
    pushMock.mockReset();
    listarMock.mockReset();
    confirmarMock.mockReset();
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


// ---------------------------------------------------------------------------
// US #26 — Botão de confirmação de ocorrência
// ---------------------------------------------------------------------------

describe("OcorrenciasPage — confirmar ocorrência (US #26)", () => {
  beforeEach(() => {
    pushMock.mockReset();
    listarMock.mockReset();
    confirmarMock.mockReset();
    listarMock.mockResolvedValue([]); // default: lista vazia para evitar erro no carregamento
    paramsLinha = "";
    jest.spyOn(Date, "now").mockReturnValue(AGORA);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("exibe o botão 'Eu também vi isso' para ocorrência pendente de outro usuário", async () => {
    listarMock.mockResolvedValue([
      ocorrencia({ id: "oc1", status: "pendente", ehAutor: false }),
    ]);

    render(<OcorrenciasPage />);

    // O aria-label inclui o tipo/linha; buscamos pelo texto visível do botão.
    await screen.findByText("Atraso — 0.110");
    expect(screen.getByText("Eu também vi isso")).toBeInTheDocument();
  });

  it("NÃO exibe o botão para o autor da própria ocorrência (Cenário 2)", async () => {
    listarMock.mockResolvedValue([
      ocorrencia({ id: "oc1", status: "pendente", ehAutor: true }),
    ]);

    render(<OcorrenciasPage />);

    await screen.findByText("Aguardando confirmação");
    expect(screen.queryByText("Eu também vi isso")).not.toBeInTheDocument();
  });

  it("NÃO exibe o botão para ocorrência já confirmada", async () => {
    listarMock.mockResolvedValue([
      ocorrencia({ id: "oc1", status: "confirmada", contadorConfirmacoes: 3, ehAutor: false }),
    ]);

    render(<OcorrenciasPage />);

    await screen.findByText("Confirmada · 3 confirmações");
    expect(screen.queryByText("Eu também vi isso")).not.toBeInTheDocument();
  });

  it("ao clicar, chama confirmarOcorrencia com o id correto", async () => {
    listarMock.mockResolvedValue([
      ocorrencia({ id: "oc-abc", status: "pendente", ehAutor: false }),
    ]);
    confirmarMock.mockResolvedValue({
      ocorrencia_id: "oc-abc",
      status: "pendente",
      contador_confirmacoes: 1,
      mensagem: "Confirmação registrada.",
    });

    render(<OcorrenciasPage />);
    await screen.findByText("Eu também vi isso");
    fireEvent.click(screen.getByText("Eu também vi isso"));

    await waitFor(() => {
      expect(confirmarMock).toHaveBeenCalledWith("oc-abc");
    });
  });

  it("exibe indicador de carregamento durante a confirmação", async () => {
    listarMock.mockResolvedValue([
      ocorrencia({ id: "oc1", status: "pendente", ehAutor: false }),
    ]);
    confirmarMock.mockReturnValue(new Promise(() => {}));

    render(<OcorrenciasPage />);
    await screen.findByText("Eu também vi isso");
    fireEvent.click(screen.getByText("Eu também vi isso"));

    expect(await screen.findByText(/Confirmando/i)).toBeInTheDocument();
    // Após clicar, o botão deve estar desabilitado
    expect(screen.getByRole("button", { name: /Confirmar ocorr/i })).toBeDisabled();
  });

  it("NÃO exibe o botão para o autor da própria ocorrência (Cenário 2)", async () => {
    listarMock.mockResolvedValue([
      ocorrencia({ id: "oc1", status: "pendente", ehAutor: true }),
    ]);

    render(<OcorrenciasPage />);

    await screen.findByText("Aguardando confirmação");
    expect(
      screen.queryByRole("button", { name: /Eu também vi isso/i })
    ).not.toBeInTheDocument();
  });

  it("NÃO exibe o botão para ocorrência já confirmada", async () => {
    listarMock.mockResolvedValue([
      ocorrencia({ id: "oc1", status: "confirmada", contadorConfirmacoes: 3, ehAutor: false }),
    ]);

    render(<OcorrenciasPage />);

    await screen.findByText("Confirmada · 3 confirmações");
    expect(
      screen.queryByRole("button", { name: /Eu também vi isso/i })
    ).not.toBeInTheDocument();
  });

  it("ao clicar, chama confirmarOcorrencia com o id correto", async () => {
    listarMock.mockResolvedValue([
      ocorrencia({ id: "oc-abc", status: "pendente", ehAutor: false }),
    ]);
    confirmarMock.mockResolvedValue({
      ocorrencia_id: "oc-abc",
      status: "pendente",
      contador_confirmacoes: 1,
      mensagem: "Confirmação registrada.",
    });

    render(<OcorrenciasPage />);
    await screen.findByText("Eu também vi isso");
    fireEvent.click(screen.getByText("Eu também vi isso"));

    await waitFor(() => {
      expect(confirmarMock).toHaveBeenCalledWith("oc-abc");
    });
  });

  it("exibe indicador de carregamento durante a confirmação", async () => {
    listarMock.mockResolvedValue([
      ocorrencia({ id: "oc1", status: "pendente", ehAutor: false }),
    ]);
    confirmarMock.mockReturnValue(new Promise(() => {}));

    render(<OcorrenciasPage />);
    await screen.findByText("Eu também vi isso");
    fireEvent.click(screen.getByText("Eu também vi isso"));

    expect(await screen.findByText(/Confirmando/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Confirmar ocorr/i })).toBeDisabled();
  });

  it("exibe mensagem de sucesso e atualiza o contador após confirmação", async () => {
    listarMock.mockResolvedValue([
      ocorrencia({ id: "oc1", status: "pendente", contadorConfirmacoes: 0, ehAutor: false }),
    ]);
    confirmarMock.mockResolvedValue({
      ocorrencia_id: "oc1",
      status: "pendente",
      contador_confirmacoes: 1,
      mensagem: "Confirmação registrada.",
    });

    render(<OcorrenciasPage />);
    await screen.findByText("Eu também vi isso");
    fireEvent.click(screen.getByText("Eu também vi isso"));

    await waitFor(() => {
      expect(screen.getByText("Confirmação registrada.")).toBeInTheDocument();
    });
  });

  it("ao atingir 3 confirmações, status muda para confirmada e botão some", async () => {
    listarMock.mockResolvedValue([
      ocorrencia({ id: "oc1", status: "pendente", contadorConfirmacoes: 2, ehAutor: false }),
    ]);
    confirmarMock.mockResolvedValue({
      ocorrencia_id: "oc1",
      status: "confirmada",
      contador_confirmacoes: 3,
      mensagem: "Ocorrência confirmada pela comunidade.",
    });

    render(<OcorrenciasPage />);
    await screen.findByText("Eu também vi isso");
    fireEvent.click(screen.getByText("Eu também vi isso"));

    await waitFor(() => {
      expect(screen.getByText("Ocorrência confirmada pela comunidade.")).toBeInTheDocument();
      expect(screen.queryByText("Eu também vi isso")).not.toBeInTheDocument();
    });
  });

  it("exibe mensagem de erro 403 — autor tentando confirmar", async () => {
    listarMock.mockResolvedValue([
      ocorrencia({ id: "oc1", status: "pendente", ehAutor: false }),
    ]);
    confirmarMock.mockRejectedValue(
      new ConfirmarOcorrenciaError("Você não pode confirmar uma ocorrência que reportou.", 403)
    );

    render(<OcorrenciasPage />);
    await screen.findByText("Eu também vi isso");
    fireEvent.click(screen.getByText("Eu também vi isso"));

    await waitFor(() => {
      expect(
        screen.getByText("Você não pode confirmar uma ocorrência que reportou.")
      ).toBeInTheDocument();
    });
  });

  it("exibe mensagem de erro 409 — já confirmou", async () => {
    listarMock.mockResolvedValue([
      ocorrencia({ id: "oc1", status: "pendente", ehAutor: false }),
    ]);
    confirmarMock.mockRejectedValue(
      new ConfirmarOcorrenciaError("Você já confirmou esta ocorrência.", 409)
    );

    render(<OcorrenciasPage />);
    await screen.findByText("Eu também vi isso");
    fireEvent.click(screen.getByText("Eu também vi isso"));

    await waitFor(() => {
      expect(screen.getByText("Você já confirmou esta ocorrência.")).toBeInTheDocument();
    });
  });

  it("exibe mensagem de expiração (422) — alerta não está mais ativo", async () => {
    listarMock.mockResolvedValue([
      ocorrencia({ id: "oc1", status: "pendente", ehAutor: false }),
    ]);
    confirmarMock.mockRejectedValue(
      new ConfirmarOcorrenciaError("Este alerta não está mais ativo.", 422)
    );

    render(<OcorrenciasPage />);
    await screen.findByText("Eu também vi isso");
    fireEvent.click(screen.getByText("Eu também vi isso"));

    await waitFor(() => {
      expect(screen.getByText("Este alerta não está mais ativo.")).toBeInTheDocument();
    });
  });

  it("erro 401 redireciona para login sem quebrar a tela", async () => {
    listarMock.mockResolvedValue([
      ocorrencia({ id: "oc1", status: "pendente", ehAutor: false }),
    ]);
    confirmarMock.mockRejectedValue(
      new ConfirmarOcorrenciaError("Faça login para confirmar ocorrências.", 401)
    );

    render(<OcorrenciasPage />);
    await screen.findByText("Eu também vi isso");
    fireEvent.click(screen.getByText("Eu também vi isso"));

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/login");
    });
  });
});
