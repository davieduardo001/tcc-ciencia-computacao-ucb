import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import OcorrenciasPage from "../page";
import { reportarOcorrencia, ReportarOcorrenciaError } from "@/lib/api";

jest.mock("@/lib/api", () => {
  const actual = jest.requireActual("@/lib/api");
  return {
    ...actual,
    buscarUsuarioAtual: jest.fn().mockResolvedValue(null),
    logoutUsuario: jest.fn(),
    sugerirLinhas: jest.fn().mockResolvedValue([]),
    nomearLugar: jest.fn(),
    reportarOcorrencia: jest.fn(),
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

const reportarOcorrenciaMock = reportarOcorrencia as jest.Mock;

function preencherEEnviar() {
  fireEvent.change(screen.getByPlaceholderText("Ex: 0.110"), {
    target: { value: "0.110" },
  });
  fireEvent.click(screen.getByText("Atraso"));
  fireEvent.click(screen.getByRole("button", { name: /Enviar reporte/ }));
}

describe("OcorrenciasPage", () => {
  beforeEach(() => {
    pushMock.mockReset();
    reportarOcorrenciaMock.mockReset();
    paramsLinha = "";
  });

  it("vindo do atalho 'Reportar nesta linha', já chega com a linha preenchida", () => {
    paramsLinha = "0.312";
    render(<OcorrenciasPage />);

    expect(screen.getByPlaceholderText("Ex: 0.110")).toHaveValue("0.312");
  });

  it("renderiza os 7 tipos de ocorrência do protótipo v3", () => {
    render(<OcorrenciasPage />);

    [
      "Atraso",
      "Ônibus não passou",
      "Lotação",
      "Obra na via",
      "Ônibus quebrou",
      "Acidente",
      "Segurança",
    ].forEach((label) => {
      expect(screen.getByText(label)).toBeInTheDocument();
    });
  });

  it("exige linha e tipo antes de enviar", () => {
    render(<OcorrenciasPage />);

    fireEvent.click(screen.getByRole("button", { name: /Enviar reporte/ }));

    expect(
      screen.getByText("Selecione a linha e o tipo de ocorrência.")
    ).toBeInTheDocument();
    expect(reportarOcorrenciaMock).not.toHaveBeenCalled();
  });

  it("envia o reporte com a linha e o tipo selecionados", async () => {
    reportarOcorrenciaMock.mockResolvedValue({
      id: "1",
      linhaNumero: "0.110",
      tipo: "atraso",
      status: "pendente",
      contadorConfirmacoes: 0,
      criadoEm: "2026-10-01T00:00:00Z",
      expiraEm: "2026-10-01T00:30:00Z",
    });

    render(<OcorrenciasPage />);
    preencherEEnviar();

    await waitFor(() => expect(reportarOcorrenciaMock).toHaveBeenCalledWith(
      expect.objectContaining({ linhaNumero: "0.110", tipo: "atraso" })
    ));
    expect(
      await screen.findByText(/Reporte enviado!/)
    ).toBeInTheDocument();
  });

  it("redireciona para o login quando o reporte exige autenticação", async () => {
    reportarOcorrenciaMock.mockRejectedValue(
      new ReportarOcorrenciaError("Faça login para reportar uma ocorrência.")
    );

    render(<OcorrenciasPage />);
    preencherEEnviar();

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/login"));
  });

  it("mostra o aviso de limite excedido sem redirecionar", async () => {
    reportarOcorrenciaMock.mockRejectedValue(
      new ReportarOcorrenciaError("Você atingiu o limite de reportes. Tente novamente mais tarde.")
    );

    render(<OcorrenciasPage />);
    preencherEEnviar();

    expect(
      await screen.findByText(/limite de reportes/)
    ).toBeInTheDocument();
    expect(pushMock).not.toHaveBeenCalledWith("/login");
  });
});
