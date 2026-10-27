import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import AlertasPage from "../page";
import {
  alternarTodasNotificacoes,
  atualizarTipoNotificacao,
  buscarPreferencias,
  buscarUsuarioAtual,
  salvarAntecedencia,
} from "@/lib/api";

jest.mock("@/lib/api", () => ({
  ANTECEDENCIAS_ALERTA: [5, 10, 30, 60],
  buscarUsuarioAtual: jest.fn(),
  buscarPreferencias: jest.fn(),
  salvarAntecedencia: jest.fn(),
  atualizarTipoNotificacao: jest.fn(),
  alternarTodasNotificacoes: jest.fn(),
  // Usados pelo AppShell.
  logoutUsuario: jest.fn(),
  atualizarFirstAccess: jest.fn(),
  buscarViagemAtiva: jest.fn().mockResolvedValue({ falhou: false, viagem: null }),
}));

// O controle de push tem testes próprios; aqui só importa o texto exibido.
jest.mock("../../configuracoes/useAvisosPush", () => ({
  ...jest.requireActual("../../configuracoes/useAvisosPush"),
  useAvisosPush: () => ({
    estado: { tipo: "desativado" },
    ocupado: false,
    erro: null,
    ativar: jest.fn(),
    desativar: jest.fn(),
  }),
}));

const pushMock = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

const buscarUsuarioAtualMock = buscarUsuarioAtual as jest.Mock;
const buscarPreferenciasMock = buscarPreferencias as jest.Mock;
const salvarAntecedenciaMock = salvarAntecedencia as jest.Mock;
const atualizarTipoMock = atualizarTipoNotificacao as jest.Mock;
const alternarTodasMock = alternarTodasNotificacoes as jest.Mock;

const USUARIO = { id: "u-1", nome: "Ana", email: "ana@teste.com", avatarUrl: null, firstAccess: false };
const PADRAO = {
  antecedenciaMinutos: 10,
  notificacoesAtivas: true,
  alertaChegada: true,
  alertaCancelamento: true,
};

async function abrir(prefs = PADRAO) {
  buscarPreferenciasMock.mockResolvedValue(prefs);
  render(<AlertasPage />);
  await screen.findByRole("radiogroup");
}

describe("Alertas (US #29)", () => {
  beforeEach(() => {
    pushMock.mockReset();
    buscarUsuarioAtualMock.mockReset().mockResolvedValue(USUARIO);
    buscarPreferenciasMock.mockReset();
    salvarAntecedenciaMock.mockReset();
    atualizarTipoMock.mockReset();
    alternarTodasMock.mockReset();
  });

  it("renderiza dentro do AppShell e carrega as preferências do usuário logado", async () => {
    await abrir();

    expect(buscarPreferenciasMock).toHaveBeenCalledWith("u-1");
    expect(document.querySelector(".ms-sidebar")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Alertas" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "10 min" })).toBeChecked();
    expect(screen.getByRole("switch", { name: "Chegada do ônibus" })).toBeChecked();
    expect(screen.getByRole("switch", { name: "Cancelamento de viagem" })).toBeChecked();
  });

  it("mostra o carregamento enquanto busca", () => {
    buscarPreferenciasMock.mockReturnValue(new Promise(() => {}));
    render(<AlertasPage />);

    expect(screen.getByText("Carregando suas preferências...")).toBeInTheDocument();
  });

  it("redireciona para o login quando não há sessão", async () => {
    buscarUsuarioAtualMock.mockResolvedValue(null);
    render(<AlertasPage />);

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/login"));
    expect(buscarPreferenciasMock).not.toHaveBeenCalled();
  });

  it("erro de carga mostra mensagem e permite tentar de novo", async () => {
    buscarPreferenciasMock.mockRejectedValueOnce(new Error("Falha no servidor"));
    render(<AlertasPage />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Falha no servidor");

    buscarPreferenciasMock.mockResolvedValueOnce(PADRAO);
    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));

    expect(await screen.findByRole("radiogroup")).toBeInTheDocument();
  });

  it("cenário 1: escolher 30 min salva e confirma", async () => {
    await abrir();
    salvarAntecedenciaMock.mockResolvedValue({ ...PADRAO, antecedenciaMinutos: 30 });

    fireEvent.click(screen.getByRole("radio", { name: "30 min" }));

    await waitFor(() => expect(salvarAntecedenciaMock).toHaveBeenCalledWith("u-1", 30));
    expect(
      await screen.findByText("Alertas serão enviados com 30 minutos de antecedência.")
    ).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "30 min" })).toBeChecked();
  });

  it("oferece exatamente 5, 10, 30 e 60 min", async () => {
    await abrir();

    const grupo = screen.getByRole("radiogroup");
    const rotulos = within(grupo).getAllByRole("radio").map((r) => r.getAttribute("value"));
    expect(rotulos).toEqual(["5", "10", "30", "60"]);
  });

  it("cenário 2: desativar cancelamento mantém chegada ativa", async () => {
    await abrir();
    atualizarTipoMock.mockResolvedValue({ ...PADRAO, alertaCancelamento: false });

    fireEvent.click(screen.getByRole("switch", { name: "Cancelamento de viagem" }));

    await waitFor(() =>
      expect(atualizarTipoMock).toHaveBeenCalledWith("u-1", "cancelamento", false)
    );
    expect(await screen.findByText("Notificações de cancelamento desativadas.")).toBeInTheDocument();
    expect(screen.getByRole("switch", { name: "Cancelamento de viagem" })).not.toBeChecked();
    expect(screen.getByRole("switch", { name: "Chegada do ônibus" })).toBeChecked();
  });

  it("cenário 3: desativar todas e reativar manualmente", async () => {
    await abrir();
    alternarTodasMock.mockResolvedValueOnce({ ...PADRAO, notificacoesAtivas: false });

    fireEvent.click(screen.getByRole("button", { name: /Desativar todas/ }));

    await waitFor(() => expect(alternarTodasMock).toHaveBeenCalledWith("u-1", false));
    expect(await screen.findByText("Todas as notificações foram desativadas.")).toBeInTheDocument();
    expect(screen.getByText(/Todas as notificações estão desativadas/)).toBeInTheDocument();

    alternarTodasMock.mockResolvedValueOnce(PADRAO);
    fireEvent.click(screen.getByRole("button", { name: /Reativar notificações/ }));

    await waitFor(() => expect(alternarTodasMock).toHaveBeenLastCalledWith("u-1", true));
    expect(await screen.findByText("Notificações reativadas.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Desativar todas/ })).toBeInTheDocument();
  });

  it("erro ao salvar mostra a mensagem e mantém o valor anterior", async () => {
    await abrir();
    salvarAntecedenciaMock.mockRejectedValue(new Error("Sem conexão. Verifique sua internet e tente novamente."));

    fireEvent.click(screen.getByRole("radio", { name: "60 min" }));

    expect(await screen.findByText(/Sem conexão/)).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "10 min" })).toBeChecked();
  });

  it("mostra o estado do aviso com a tela bloqueada e leva às Configurações", async () => {
    await abrir();

    expect(screen.getByText("Avisos com a tela bloqueada")).toBeInTheDocument();
    expect(
      screen.getByText("Receba o aviso de que sua parada está chegando, mesmo com o app fechado.")
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Gerenciar em Configurações" })).toHaveAttribute(
      "href",
      "/configuracoes"
    );
  });
});
