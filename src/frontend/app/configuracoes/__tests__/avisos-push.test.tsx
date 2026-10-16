import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import Configuracoes from "../page";
import { buscarUsuarioAtual } from "@/lib/api";
import { ativarPush, desativarPush, lerEstadoPush } from "@/lib/push";

/**
 * Seção "Avisos com a tela bloqueada" das Configurações (US #172).
 *
 * `@/lib/push` é dublê: o que importa aqui é o que a TELA faz com cada estado
 * e, principalmente, QUANDO ela chama `ativarPush` — a permissão do navegador
 * só pode ser pedida depois de um clique.
 */

jest.mock("@/lib/api", () => {
  class PushError extends Error {}
  return {
    PushError,
    buscarUsuarioAtual: jest.fn(),
    atualizarFirstAccess: jest.fn(),
    logoutUsuario: jest.fn(),
    // O AppShell consulta a viagem em andamento (US #171): sem viagem.
    buscarViagemAtiva: jest.fn().mockResolvedValue({ falhou: false, viagem: null }),
  };
});

jest.mock("@/lib/push", () => ({
  lerEstadoPush: jest.fn(),
  ativarPush: jest.fn(),
  desativarPush: jest.fn(),
}));

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
}));

const lerMock = lerEstadoPush as jest.Mock;
const ativarMock = ativarPush as jest.Mock;
const desativarMock = desativarPush as jest.Mock;
const usuarioMock = buscarUsuarioAtual as jest.Mock;

// A classe de erro do mock de "@/lib/api" é a mesma que o hook compara.
// eslint-disable-next-line @typescript-eslint/no-require-imports
const { PushError } = require("@/lib/api");

const USUARIO = { nome: "Ana Passageira", email: "ana@teste.com", avatarUrl: null, firstAccess: false };

async function abrir(estado: { tipo: string }) {
  lerMock.mockResolvedValue(estado);
  render(<Configuracoes />);
  await screen.findByText("Avisos com a tela bloqueada");
}

beforeEach(() => {
  jest.clearAllMocks();
  usuarioMock.mockResolvedValue(USUARIO);
  ativarMock.mockResolvedValue({ tipo: "ativo" });
  desativarMock.mockResolvedValue({ tipo: "desativado" });
});

describe("estados da seção", () => {
  it("desativado: oferece o botão Ativar", async () => {
    await abrir({ tipo: "desativado" });

    expect(screen.getByRole("button", { name: "Ativar" })).toBeEnabled();
    expect(screen.getByText(/mesmo com o app fechado/)).toBeInTheDocument();
  });

  it("ativo: diz que está ativo e oferece Desativar", async () => {
    await abrir({ tipo: "ativo" });

    expect(screen.getByText(/Ativo neste aparelho/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Desativar" })).toBeEnabled();
    expect(screen.queryByRole("button", { name: "Ativar" })).not.toBeInTheDocument();
  });

  it("iPhone sem o app instalado: explica como instalar e não oferece botão", async () => {
    await abrir({ tipo: "ios-instalar" });

    expect(screen.getByText(/instalar o Movecity/)).toBeInTheDocument();
    expect(screen.getByText(/Adicionar à Tela de Início/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Ativar|Desativar/ })).not.toBeInTheDocument();
  });

  it("permissão negada: explica como liberar e não tenta pedir de novo", async () => {
    await abrir({ tipo: "negado" });

    expect(screen.getByText(/bloqueadas neste navegador/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Ativar|Desativar/ })).not.toBeInTheDocument();
  });

  it("servidor sem chaves: diz que está indisponível, sem botão e sem erro", async () => {
    await abrir({ tipo: "indisponivel" });

    expect(screen.getByText(/não estão disponíveis no momento/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Ativar|Desativar/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("navegador sem suporte: avisa e não oferece botão", async () => {
    await abrir({ tipo: "nao-suportado" });

    expect(screen.getByText(/não permite avisos com a tela bloqueada/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Ativar|Desativar/ })).not.toBeInTheDocument();
  });

  it("enquanto verifica, mostra o texto de espera e nenhum botão", async () => {
    lerMock.mockReturnValue(new Promise(() => {}));
    render(<Configuracoes />);
    await screen.findByText("Avisos com a tela bloqueada");

    expect(screen.getByText(/Verificando este aparelho/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Ativar|Desativar/ })).not.toBeInTheDocument();
  });

  it("se ler o estado falhar, trata como sem suporte em vez de quebrar a tela", async () => {
    lerMock.mockRejectedValue(new Error("falhou"));
    render(<Configuracoes />);
    await screen.findByText("Avisos com a tela bloqueada");

    await waitFor(() =>
      expect(screen.getByText(/não permite avisos com a tela bloqueada/)).toBeInTheDocument()
    );
  });
});

describe("permissão só depois do clique", () => {
  it("abrir a tela NUNCA chama ativarPush (que é quem pede a permissão)", async () => {
    await abrir({ tipo: "desativado" });
    await new Promise((r) => setTimeout(r, 20));

    expect(ativarMock).not.toHaveBeenCalled();
    expect(lerMock).toHaveBeenCalled(); // só leu o estado
  });

  it("tocar em Ativar chama ativarPush uma vez e passa para Ativo", async () => {
    await abrir({ tipo: "desativado" });

    fireEvent.click(screen.getByRole("button", { name: "Ativar" }));

    await waitFor(() => expect(screen.getByText(/Ativo neste aparelho/)).toBeInTheDocument());
    expect(ativarMock).toHaveBeenCalledTimes(1);
  });

  it("durante a ativação o botão fica desabilitado, para não pedir duas vezes", async () => {
    let concluir: (valor: { tipo: string }) => void = () => {};
    ativarMock.mockReturnValue(new Promise((resolve) => (concluir = resolve)));
    await abrir({ tipo: "desativado" });

    fireEvent.click(screen.getByRole("button", { name: "Ativar" }));

    const ocupado = await screen.findByRole("button", { name: "Ativando..." });
    expect(ocupado).toBeDisabled();
    fireEvent.click(ocupado);
    expect(ativarMock).toHaveBeenCalledTimes(1);

    concluir({ tipo: "ativo" });
    await screen.findByText(/Ativo neste aparelho/);
  });

  it("se a pessoa negar a permissão, a tela passa para o estado negado", async () => {
    ativarMock.mockResolvedValue({ tipo: "negado" });
    await abrir({ tipo: "desativado" });

    fireEvent.click(screen.getByRole("button", { name: "Ativar" }));

    await screen.findByText(/bloqueadas neste navegador/);
    expect(screen.queryByRole("button", { name: "Ativar" })).not.toBeInTheDocument();
  });
});

describe("erros", () => {
  it("mostra a frase do servidor e continua podendo tentar de novo", async () => {
    ativarMock.mockRejectedValue(new PushError("Este navegador usa um serviço que o Movecity não aceita."));
    await abrir({ tipo: "desativado" });

    fireEvent.click(screen.getByRole("button", { name: "Ativar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("não aceita");
    expect(screen.getByRole("button", { name: "Ativar" })).toBeEnabled();
  });

  it("erro inesperado vira texto genérico, sem vazar a mensagem técnica", async () => {
    ativarMock.mockRejectedValue(new TypeError("Cannot read properties of undefined"));
    await abrir({ tipo: "desativado" });

    fireEvent.click(screen.getByRole("button", { name: "Ativar" }));

    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent("Não foi possível ativar os avisos");
    expect(alerta).not.toHaveTextContent("Cannot read");
  });

  it("limpa o erro anterior ao tentar de novo", async () => {
    ativarMock.mockRejectedValueOnce(new PushError("Falhou uma vez.")).mockResolvedValueOnce({ tipo: "ativo" });
    await abrir({ tipo: "desativado" });

    fireEvent.click(screen.getByRole("button", { name: "Ativar" }));
    await screen.findByText("Falhou uma vez.");
    fireEvent.click(screen.getByRole("button", { name: "Ativar" }));

    await screen.findByText(/Ativo neste aparelho/);
    expect(screen.queryByText("Falhou uma vez.")).not.toBeInTheDocument();
  });
});

describe("desativar", () => {
  it("tocar em Desativar chama desativarPush e volta para Ativar", async () => {
    await abrir({ tipo: "ativo" });

    fireEvent.click(screen.getByRole("button", { name: "Desativar" }));

    await screen.findByRole("button", { name: "Ativar" });
    expect(desativarMock).toHaveBeenCalledTimes(1);
  });

  it("falha ao desativar mostra o erro e mantém Ativo", async () => {
    desativarMock.mockRejectedValue(new Error("falhou"));
    await abrir({ tipo: "ativo" });

    fireEvent.click(screen.getByRole("button", { name: "Desativar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Não foi possível desativar");
    expect(screen.getByText(/Ativo neste aparelho/)).toBeInTheDocument();
  });
});
