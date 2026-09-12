import { render, screen, waitFor } from "@testing-library/react";
import AppShell from "../AppShell";
import { buscarUsuarioAtual } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  buscarUsuarioAtual: jest.fn(),
}));

const buscarUsuarioAtualMock = buscarUsuarioAtual as jest.Mock;

describe("AppShell", () => {
  beforeEach(() => {
    buscarUsuarioAtualMock.mockReset();
    buscarUsuarioAtualMock.mockResolvedValue(null);
  });


  it("renderiza o item ativo como link navegável", () => {
    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    const links = screen.getAllByRole("link", { name: "Mapa Interativo" });
    expect(links.length).toBeGreaterThan(0);
    links.forEach((link) => expect(link).toHaveAttribute("href", "/mapa"));
  });

  it("marca itens ainda não implementados como indisponíveis, sem link de navegação", () => {
    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    expect(
      screen.queryByRole("link", { name: "Linhas de Ônibus" })
    ).not.toBeInTheDocument();

    const itensIndisponiveis = screen.getAllByLabelText(
      /Linhas de Ônibus/i
    );
    itensIndisponiveis.forEach((item) => {
      expect(item).toHaveAttribute("aria-disabled", "true");
    });
  });

  it("mostra o selo 'Em breve' na sidebar para itens indisponíveis", () => {
    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    expect(screen.getAllByText("Em breve").length).toBeGreaterThan(0);
  });

  it("mostra 'Visitante' quando não há sessão autenticada", async () => {
    buscarUsuarioAtualMock.mockResolvedValue(null);

    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    await waitFor(() => {
      expect(screen.getByText("Visitante")).toBeInTheDocument();
    });
    expect(screen.getByText("Não autenticado")).toBeInTheDocument();
  });

  it("mostra nome e e-mail do usuário autenticado", async () => {
    buscarUsuarioAtualMock.mockResolvedValue({
      id: "1",
      nome: "Ana Passageira",
      email: "ana@teste.com",
      avatarUrl: null,
    });

    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    await waitFor(() => {
      expect(screen.getByText("Ana Passageira")).toBeInTheDocument();
    });
    expect(screen.getByText("ana@teste.com")).toBeInTheDocument();
    expect(screen.getByText("AP")).toBeInTheDocument();
  });
});
