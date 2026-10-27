import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import AppShell from "../AppShell";
import {
  atualizarFirstAccess,
  buscarUsuarioAtual,
  buscarViagemAtiva,
  logoutUsuario,
  ViagemAtiva,
} from "@/lib/api";

jest.mock("@/lib/api", () => ({
  buscarUsuarioAtual: jest.fn(),
  logoutUsuario: jest.fn(),
  atualizarFirstAccess: jest.fn(),
  // O AppShell consulta a viagem em andamento (US #171). Por padrão a
  // consulta nunca responde: os testes antigos, síncronos, não esperam a
  // resposta e gerariam avisos de `act`. Quem testa a viagem define o retorno.
  buscarViagemAtiva: jest.fn(() => new Promise(() => {})),
}));

const pushMock = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

const buscarUsuarioAtualMock = buscarUsuarioAtual as jest.Mock;
const logoutUsuarioMock = logoutUsuario as jest.Mock;
const atualizarFirstAccessMock = atualizarFirstAccess as jest.Mock;

describe("AppShell", () => {
  beforeEach(() => {
    buscarUsuarioAtualMock.mockReset();
    buscarUsuarioAtualMock.mockResolvedValue(null);
    logoutUsuarioMock.mockReset();
    logoutUsuarioMock.mockResolvedValue(undefined);
    atualizarFirstAccessMock.mockReset();
    atualizarFirstAccessMock.mockResolvedValue(undefined);
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

  it("'Rotas Salvas' agora é link navegável apontando para /favoritos (US #25)", () => {
    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    // Com disponivel: true, "Rotas Salvas" deve ser um link.
    const links = screen.getAllByRole("link", { name: "Rotas Salvas" });
    expect(links.length).toBeGreaterThan(0);
    links.forEach((link) => expect(link).toHaveAttribute("href", "/favoritos"));
  });

  it("não tem item de menu 'Linhas de Ônibus' nem 'Rotas' (card #179)", () => {
    // Os dois só repetiam entradas que já existem no mapa: "Linhas" apenas
    // dava foco na busca do topo e "Rotas" apenas abria o planejador. Uma
    // função, um ponto de entrada.
    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    expect(screen.queryByRole("link", { name: /Linhas/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /^Rotas$/i })).not.toBeInTheDocument();
    // "Rotas Salvas" é outra coisa (US #25) e continua.
    expect(screen.getAllByRole("link", { name: "Rotas Salvas" }).length).toBeGreaterThan(0);
  });

  it("a busca de linha continua na barra do topo", () => {
    render(
      <AppShell active="mapa" onBuscarLinha={jest.fn()}>
        <div>conteúdo</div>
      </AppShell>
    );

    expect(screen.getByPlaceholderText(/Buscar linha ou destino/)).toBeInTheDocument();
  });

  it("navegação inferior: Mapa e Perfil, com o vão do botão central entre os dois", () => {
    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    const inferior = document.querySelector(".ms-bottomnav") as HTMLElement;
    const destinos = [...inferior.querySelectorAll(".ms-bottomnav-rotulo")].map(
      (e) => e.textContent
    );
    expect(destinos).toEqual(["Mapa", "Perfil"]);

    const vao = inferior.querySelector(".ms-bottomnav-vao") as HTMLElement;
    expect(vao.previousElementSibling).toHaveTextContent("Mapa");
    expect(vao.nextElementSibling).toHaveTextContent("Perfil");
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

  it("ação 'Rotas salvas' do arco agora navega para /favoritos (US #25)", () => {
    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    fireEvent.click(screen.getByRole("button", { name: "Ações rápidas" }));

    const inferior = document.querySelector(".ms-bottomnav") as HTMLElement;
    fireEvent.click(within(inferior).getByText("Rotas salvas"));

    expect(pushMock).toHaveBeenCalledWith("/favoritos");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("ação 'Alertas' do arco navega para /alertas (US #29)", () => {
    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    fireEvent.click(screen.getByRole("button", { name: "Ações rápidas" }));

    const inferior = document.querySelector(".ms-bottomnav") as HTMLElement;
    fireEvent.click(within(inferior).getByText("Alertas"));

    expect(pushMock).toHaveBeenCalledWith("/alertas");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("'Alertas' é link para /alertas na sidebar e no sino do topo (US #29)", () => {
    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    const sidebar = document.querySelector(".ms-sidebar") as HTMLElement;
    expect(within(sidebar).getByRole("link", { name: "Alertas" })).toHaveAttribute(
      "href",
      "/alertas"
    );
    expect(screen.getByTitle("Alertas")).toHaveAttribute("href", "/alertas");
  });

  it("sidebar de desktop também linka para Ocorrências — único acesso em telas >920px (US #23)", () => {
    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    const sidebar = document.querySelector(".ms-sidebar") as HTMLElement;
    const link = within(sidebar).getByRole("link", { name: "Ocorrências" });
    expect(link).toHaveAttribute("href", "/ocorrencias");
  });

  it("ação 'Ocorrências' do arco já navega para a tela real (US #23)", () => {
    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    fireEvent.click(screen.getByRole("button", { name: "Ações rápidas" }));

    const inferior = document.querySelector(".ms-bottomnav") as HTMLElement;
    fireEvent.click(within(inferior).getByText("Ocorrências"));

    expect(pushMock).toHaveBeenCalledWith("/ocorrencias");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("não mostra selo 'Em breve' na sidebar: todos os itens têm tela (US #29)", () => {
    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    const sidebar = document.querySelector(".ms-sidebar") as HTMLElement;
    expect(within(sidebar).queryByText("Em breve")).not.toBeInTheDocument();
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

  it("botão de ajuda marca first_access=true e abre o tutorial (US #30)", async () => {
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

    const botaoAjuda = await screen.findByTitle("Rever o guia");
    fireEvent.click(botaoAjuda);

    await waitFor(() => {
      expect(atualizarFirstAccessMock).toHaveBeenCalledWith(true);
      expect(pushMock).toHaveBeenCalledWith("/tutorial");
    });
  });

  it("não mostra o botão de ajuda para visitante não autenticado", async () => {
    buscarUsuarioAtualMock.mockResolvedValue(null);

    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    await waitFor(() => {
      expect(screen.getByText("Visitante")).toBeInTheDocument();
    });
    expect(screen.queryByTitle("Rever o guia")).not.toBeInTheDocument();
  });
});

describe("AppShell — viagem em andamento (US #171)", () => {
  const buscarViagemMock = buscarViagemAtiva as jest.Mock;

  const VIAGEM: ViagemAtiva = {
    id: "v-1",
    numeroLinha: "0.110",
    sentido: "IDA",
    veiculoPrefixo: "440001",
    paradaDestinoCodigo: null,
    embarcouEm: "2026-10-14T15:00:00Z",
    sinal: "ao_vivo",
    veiculo: null,
    destino: null,
    proximaParada: null,
    paradasRestantes: [],
  };

  beforeEach(() => {
    buscarUsuarioAtualMock.mockReset().mockResolvedValue(null);
  });

  afterEach(() => {
    buscarViagemMock.mockReset().mockImplementation(() => new Promise(() => {}));
  });

  it("fora do mapa, em viagem: o chip lembra da viagem e leva de volta ao mapa", async () => {
    buscarViagemMock.mockResolvedValue({ falhou: false, viagem: VIAGEM });

    render(
      <AppShell active="favoritos">
        <div>conteúdo</div>
      </AppShell>
    );

    const chip = await screen.findByRole("link", { name: "Em viagem na linha 0.110. Voltar ao mapa" });
    expect(chip).toHaveAttribute("href", "/mapa");
    expect(chip).toHaveTextContent("0.110");
  });

  it("no mapa, o chip sai (a faixa do próprio mapa já diz isso)", async () => {
    buscarViagemMock.mockResolvedValue({ falhou: false, viagem: VIAGEM });

    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    await waitFor(() => expect(buscarViagemMock).toHaveBeenCalled());
    await waitFor(() => expect(document.querySelector(".ms-content.com-viagem")).not.toBeNull());
    expect(screen.queryByRole("link", { name: /Em viagem na linha/ })).not.toBeInTheDocument();
  });

  it("aguardando: nem chip nem a marca de viagem no conteúdo", async () => {
    buscarViagemMock.mockResolvedValue({ falhou: false, viagem: null });

    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    await waitFor(() => expect(buscarViagemMock).toHaveBeenCalled());
    expect(screen.queryByRole("link", { name: /Em viagem na linha/ })).not.toBeInTheDocument();
    expect(document.querySelector(".ms-content")).not.toHaveClass("com-viagem");
  });

  it("em viagem no mapa, o conteúdo ganha 'com-viagem' — é o que desce o planejador e os painéis", async () => {
    buscarViagemMock.mockResolvedValue({ falhou: false, viagem: VIAGEM });

    render(
      <AppShell active="mapa">
        <div>conteúdo</div>
      </AppShell>
    );

    await waitFor(() => expect(document.querySelector(".ms-content")).toHaveClass("com-viagem"));
  });

  it("em viagem, fora do mapa, o conteúdo NÃO ganha 'com-viagem' (não há faixa para abrir espaço)", async () => {
    buscarViagemMock.mockResolvedValue({ falhou: false, viagem: VIAGEM });

    render(
      <AppShell active="favoritos">
        <div>conteúdo</div>
      </AppShell>
    );

    await screen.findByRole("link", { name: /Em viagem na linha/ });
    expect(document.querySelector(".ms-content")).not.toHaveClass("com-viagem");
  });
});
