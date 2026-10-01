import { render, waitFor } from "@testing-library/react";
import Home from "../page";
import { buscarUsuarioAtual } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  buscarUsuarioAtual: jest.fn(),
}));

const replaceMock = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ replace: replaceMock }),
}));

const buscarUsuarioAtualMock = buscarUsuarioAtual as jest.Mock;

describe("Home (/)", () => {
  beforeEach(() => {
    replaceMock.mockReset();
    buscarUsuarioAtualMock.mockReset();
  });

  it("redireciona pro mapa quando já existe sessão", async () => {
    buscarUsuarioAtualMock.mockResolvedValue({
      id: "1",
      nome: "Ana",
      email: "ana@teste.com",
      avatarUrl: null,
      firstAccess: false,
    });

    render(<Home />);

    await waitFor(() => expect(replaceMock).toHaveBeenCalledWith("/mapa"));
  });

  it("redireciona pro login quando não há sessão", async () => {
    buscarUsuarioAtualMock.mockResolvedValue(null);

    render(<Home />);

    await waitFor(() => expect(replaceMock).toHaveBeenCalledWith("/login"));
  });
});
