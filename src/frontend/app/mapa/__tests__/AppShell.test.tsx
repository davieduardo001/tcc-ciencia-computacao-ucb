import { render, screen } from "@testing-library/react";
import AppShell from "../AppShell";

describe("AppShell", () => {
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
});
