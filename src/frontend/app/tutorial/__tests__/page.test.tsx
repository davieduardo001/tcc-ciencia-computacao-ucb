import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import Tutorial from "../page";
import { atualizarFirstAccess, buscarUsuarioAtual } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  atualizarFirstAccess: jest.fn(),
  buscarUsuarioAtual: jest.fn(),
}));

const pushMock = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

const buscarUsuarioAtualMock = buscarUsuarioAtual as jest.Mock;
const atualizarFirstAccessMock = atualizarFirstAccess as jest.Mock;

describe("Tutorial", () => {
  beforeEach(() => {
    pushMock.mockReset();
    atualizarFirstAccessMock.mockReset();
    atualizarFirstAccessMock.mockResolvedValue(undefined);
    buscarUsuarioAtualMock.mockReset();
    buscarUsuarioAtualMock.mockResolvedValue({
      id: "1",
      nome: "Ana",
      email: "ana@teste.com",
      avatarUrl: null,
      firstAccess: true,
    });
  });

  it("mostra o primeiro passo com ícone (lucide-react, não emoji)", async () => {
    const { container } = render(<Tutorial />);

    await waitFor(() => expect(screen.getByText("Buscar Linhas")).toBeInTheDocument());
    expect(container.querySelector(".tutorial-icone svg")).toBeInTheDocument();
  });

  it("avança pelos 4 passos até mostrar o botão Começar", async () => {
    render(<Tutorial />);
    await waitFor(() => expect(screen.getByText("Buscar Linhas")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Próximo"));
    expect(await screen.findByText("Visualizar no Mapa")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Próximo"));
    expect(await screen.findByText("Reportar Ocorrência")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Próximo"));
    expect(await screen.findByText("Salvar Rota Favorita")).toBeInTheDocument();
    expect(screen.getByText("Começar")).toBeInTheDocument();
  });

  it("pular marca first_access=false e volta pro mapa", async () => {
    render(<Tutorial />);
    await waitFor(() => expect(screen.getByText("Buscar Linhas")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Pular"));

    await waitFor(() => {
      expect(atualizarFirstAccessMock).toHaveBeenCalledWith(false);
      expect(pushMock).toHaveBeenCalledWith("/mapa");
    });
  });

  it("redireciona pro login quando não há sessão", async () => {
    buscarUsuarioAtualMock.mockResolvedValue(null);
    render(<Tutorial />);

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/login"));
  });

  it("redireciona pro mapa quando o tutorial já foi visto", async () => {
    buscarUsuarioAtualMock.mockResolvedValue({
      id: "1",
      nome: "Ana",
      email: "ana@teste.com",
      avatarUrl: null,
      firstAccess: false,
    });
    render(<Tutorial />);

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/mapa"));
  });
});
