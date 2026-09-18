import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import AppShell from "../AppShell";
import { buscarUsuarioAtual, logoutUsuario } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  buscarUsuarioAtual: jest.fn(),
  logoutUsuario: jest.fn(),
}));

const pushMock = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

const buscarUsuarioAtualMock = buscarUsuarioAtual as jest.Mock;
const logoutUsuarioMock = logoutUsuario as jest.Mock;

describe("AppShell", () => {
  beforeEach(() => {
    buscarUsuarioAtualMock.mockReset();
    buscarUsuarioAtualMock.mockResolvedValue(null);
    logoutUsuarioMock.mockReset();
    logoutUsuarioMock.mockResolvedValue(undefined);
    pushMock.mockReset();
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

    // "Rotas Salvas" segue não implementada (US #25).
    expect(
      screen.queryByRole("link", { name: "Rotas Salvas" })
    ).not.toBeInTheDocument();

    // Na barra lateral o item é inerte.
    const sidebar = document.querySelector(".ms-sidebar") as HTMLElement;
    const item = within(sidebar)
      .getByText("Rotas Salvas")
      .closest(".ms-nav-item");
    expect(item).toHaveAttribute("aria-disabled", "true");
  });

  it("linhas e rotas navegam para o mapa com o painel certo", () => {
    // As duas funcionalidades vivem dentro do mapa, não em páginas
    // separadas — marcá-las como "em breve" dizia ao usuário que não
    // existiam, sendo que as US #15, #17 e #20 estão entregues.
    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    const linhas = screen.getAllByRole("link", { name: /Linhas de Ônibus/i });
    expect(linhas.length).toBeGreaterThan(0);
    linhas.forEach((l) =>
      expect(l).toHaveAttribute("href", "/mapa?painel=linhas")
    );

    const rotas = screen.getAllByRole("link", { name: /^Rotas$/i });
    expect(rotas.length).toBeGreaterThan(0);
    rotas.forEach((l) => expect(l).toHaveAttribute("href", "/mapa?painel=rotas"));
  });

  it("perfil fica na navegação inferior, não na barra lateral", () => {
    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    const sidebar = document.querySelector(".ms-sidebar") as HTMLElement;
    expect(within(sidebar).queryByText("Perfil")).not.toBeInTheDocument();

    const inferior = document.querySelector(".ms-bottomnav") as HTMLElement;
    expect(within(inferior).getByText("Perfil")).toBeInTheDocument();

    // O botão de perfil da topbar continua no DOM (o CSS o esconde no mobile).
    expect(screen.getByTitle("Perfil")).toBeInTheDocument();
  });

  it("marca o destino atual da navegação inferior com aria-current", () => {
    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    const inferior = document.querySelector(".ms-bottomnav") as HTMLElement;
    const atual = within(inferior).getByRole("link", { name: /Mapa/ });
    expect(atual).toHaveAttribute("aria-current", "page");
  });

  it("botão de ação central abre e fecha o arco de ações rápidas", () => {
    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    const fab = screen.getByRole("button", { name: "Ações rápidas" });
    expect(fab).toHaveAttribute("aria-expanded", "false");

    fireEvent.click(fab);
    const aberto = screen.getByRole("button", { name: "Fechar ações rápidas" });
    expect(aberto).toHaveAttribute("aria-expanded", "true");

    fireEvent.click(aberto);
    expect(
      screen.getByRole("button", { name: "Ações rápidas" })
    ).toHaveAttribute("aria-expanded", "false");
  });

  it("ação ainda não entregue explica que está em breve", async () => {
    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    fireEvent.click(screen.getByRole("button", { name: "Ações rápidas" }));

    const inferior = document.querySelector(".ms-bottomnav") as HTMLElement;
    fireEvent.click(within(inferior).getByText("Ocorrências"));

    const dialogo = await screen.findByRole("dialog");
    expect(within(dialogo).getByText("Ocorrências")).toBeInTheDocument();
    expect(within(dialogo).getByText("Em breve")).toBeInTheDocument();
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

  it("não mostra botão de sair para visitante", async () => {
    buscarUsuarioAtualMock.mockResolvedValue(null);

    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    await waitFor(() => {
      expect(screen.getByText("Visitante")).toBeInTheDocument();
    });
    expect(screen.queryByTitle("Sair")).not.toBeInTheDocument();
  });

  const PLACEHOLDER_BUSCA = "Buscar linha ou destino (ex: 0.110 ou Ceilândia)";

  it("submete a busca de linha chamando onBuscarLinha com o termo digitado", () => {
    const onBuscarLinha = jest.fn();

    render(
      <AppShell active="mapa" onBuscarLinha={onBuscarLinha}>
        <div>conteúdo</div>
      </AppShell>
    );

    const input = screen.getByPlaceholderText(PLACEHOLDER_BUSCA);
    fireEvent.change(input, { target: { value: "0.110" } });
    fireEvent.submit(input.closest("form")!);

    expect(onBuscarLinha).toHaveBeenCalledWith("0.110");
  });

  it("desabilita o campo de busca enquanto buscandoLinha é true", () => {
    render(
      <AppShell active="mapa" buscandoLinha>
        <div>conteúdo</div>
      </AppShell>
    );

    expect(screen.getByPlaceholderText(PLACEHOLDER_BUSCA)).toBeDisabled();
  });

  // ---------------------------------------------------------------------
  // US #17 (autocomplete) — sugestões de linha no topbar
  // ---------------------------------------------------------------------

  const SUGESTOES = [
    { numero: "0.108", nome: "0.108 — Ceilândia / Plano Piloto", sentido: "Ceilândia → Plano Piloto" },
    { numero: "0.110", nome: "0.110 — Taguatinga / Rodoviária", sentido: "Taguatinga → Rodoviária" },
  ];

  it("chama onDigitarBuscaLinha a cada tecla digitada", () => {
    const onDigitarBuscaLinha = jest.fn();

    render(
      <AppShell active="mapa" onDigitarBuscaLinha={onDigitarBuscaLinha}>
        <div>conteúdo</div>
      </AppShell>
    );

    fireEvent.change(screen.getByPlaceholderText(PLACEHOLDER_BUSCA), {
      target: { value: "ceil" },
    });

    expect(onDigitarBuscaLinha).toHaveBeenCalledWith("ceil");
  });

  it("mostra as sugestões (número, nome e sentido) quando o campo tem foco", () => {
    render(
      <AppShell active="mapa" sugestoesLinha={SUGESTOES}>
        <div>conteúdo</div>
      </AppShell>
    );

    fireEvent.focus(screen.getByPlaceholderText(PLACEHOLDER_BUSCA));

    expect(screen.getByText("0.108 — Ceilândia / Plano Piloto")).toBeInTheDocument();
    expect(screen.getByText("Ceilândia → Plano Piloto")).toBeInTheDocument();
    expect(screen.getByText("0.110 — Taguatinga / Rodoviária")).toBeInTheDocument();
  });

  it("chama onSelecionarSugestaoLinha ao clicar numa sugestão", () => {
    const onSelecionarSugestaoLinha = jest.fn();

    render(
      <AppShell
        active="mapa"
        sugestoesLinha={SUGESTOES}
        onSelecionarSugestaoLinha={onSelecionarSugestaoLinha}
      >
        <div>conteúdo</div>
      </AppShell>
    );

    fireEvent.focus(screen.getByPlaceholderText(PLACEHOLDER_BUSCA));
    fireEvent.click(screen.getByText("Ceilândia → Plano Piloto"));

    expect(onSelecionarSugestaoLinha).toHaveBeenCalledWith("0.108");
  });

  it("Enter com sugestão única seleciona ela em vez de buscar o texto digitado", () => {
    const onBuscarLinha = jest.fn();
    const onSelecionarSugestaoLinha = jest.fn();

    render(
      <AppShell
        active="mapa"
        sugestoesLinha={[SUGESTOES[0]]}
        onBuscarLinha={onBuscarLinha}
        onSelecionarSugestaoLinha={onSelecionarSugestaoLinha}
      >
        <div>conteúdo</div>
      </AppShell>
    );

    const input = screen.getByPlaceholderText(PLACEHOLDER_BUSCA);
    fireEvent.change(input, { target: { value: "ceilandia" } });
    fireEvent.submit(input.closest("form")!);

    expect(onSelecionarSugestaoLinha).toHaveBeenCalledWith("0.108");
    expect(onBuscarLinha).not.toHaveBeenCalled();
  });

  it("não mostra a lista de sugestões quando não há nenhuma", () => {
    render(
      <AppShell active="mapa" sugestoesLinha={[]}>
        <div>conteúdo</div>
      </AppShell>
    );

    fireEvent.focus(screen.getByPlaceholderText(PLACEHOLDER_BUSCA));

    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("botão de sair chama logoutUsuario e redireciona para /login", async () => {
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

    const botaoSair = await screen.findByTitle("Sair");
    fireEvent.click(botaoSair);

    await waitFor(() => {
      expect(logoutUsuarioMock).toHaveBeenCalledTimes(1);
      expect(pushMock).toHaveBeenCalledWith("/login");
    });
  });
});
