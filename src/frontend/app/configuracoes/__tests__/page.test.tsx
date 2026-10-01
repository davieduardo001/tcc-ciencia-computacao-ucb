import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import Configuracoes from "../page";
import { atualizarFirstAccess, buscarUsuarioAtual, logoutUsuario } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  buscarUsuarioAtual: jest.fn(),
  atualizarFirstAccess: jest.fn(),
  logoutUsuario: jest.fn(),
}));

const pushMock = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

const buscarUsuarioAtualMock = buscarUsuarioAtual as jest.Mock;
const atualizarFirstAccessMock = atualizarFirstAccess as jest.Mock;
const logoutUsuarioMock = logoutUsuario as jest.Mock;

const USUARIO = {
  nome: "Ana Passageira",
  email: "ana@teste.com",
  avatarUrl: null,
  firstAccess: false,
};

describe("Configuracoes", () => {
  beforeEach(() => {
    pushMock.mockReset();
    atualizarFirstAccessMock.mockReset();
    atualizarFirstAccessMock.mockResolvedValue(undefined);
    logoutUsuarioMock.mockReset();
    logoutUsuarioMock.mockResolvedValue(undefined);
    buscarUsuarioAtualMock.mockReset();
  });

  it("renderiza dentro do AppShell (sidebar continua acessível)", async () => {
    buscarUsuarioAtualMock.mockResolvedValue(USUARIO);
    render(<Configuracoes />);

    await waitFor(() => expect(screen.getByText("Configurações")).toBeInTheDocument());
    expect(document.querySelector(".ms-sidebar")).toBeInTheDocument();
    expect(document.querySelector(".ms-bottomnav")).toBeInTheDocument();
  });

  it("redireciona pro login quando não há sessão", async () => {
    buscarUsuarioAtualMock.mockResolvedValue(null);
    render(<Configuracoes />);

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/login"));
  });

  it("mostra nome e e-mail do usuário", async () => {
    buscarUsuarioAtualMock.mockResolvedValue(USUARIO);
    render(<Configuracoes />);

    // AppShell também mostra o nome (sidebar), por isso getAllByText aqui —
    // o que importa é que o cartão de perfil da própria página tem o seu.
    await waitFor(() => expect(screen.getAllByText("Ana Passageira").length).toBeGreaterThan(0));
    expect(screen.getAllByText("ana@teste.com").length).toBeGreaterThan(0);
  });

  it("ver tutorial novamente marca first_access=true e navega pro tutorial", async () => {
    buscarUsuarioAtualMock.mockResolvedValue(USUARIO);
    render(<Configuracoes />);

    const botao = await screen.findByText("Ver tutorial");
    fireEvent.click(botao);

    await waitFor(() => {
      expect(atualizarFirstAccessMock).toHaveBeenCalledWith(true);
      expect(pushMock).toHaveBeenCalledWith("/tutorial");
    });
  });

  it("desabilita o botão quando o tutorial já está ativo (firstAccess=true)", async () => {
    buscarUsuarioAtualMock.mockResolvedValue({ ...USUARIO, firstAccess: true });
    render(<Configuracoes />);

    const botao = await screen.findByText("Tutorial ativo");
    expect(botao).toBeDisabled();
  });

  it("sair da conta chama logoutUsuario e redireciona pro login", async () => {
    buscarUsuarioAtualMock.mockResolvedValue(USUARIO);
    render(<Configuracoes />);

    const botao = await screen.findByText("Sair da conta");
    fireEvent.click(botao);

    await waitFor(() => {
      expect(logoutUsuarioMock).toHaveBeenCalledTimes(1);
      expect(pushMock).toHaveBeenCalledWith("/login");
    });
  });
});
