import { fireEvent, render, screen } from "@testing-library/react";
import AppShell from "../AppShell";
import { buscarUsuarioAtual, buscarViagemAtiva, confirmarAvisoDeProximidade } from "@/lib/api";

/**
 * US #172 — o aviso de proximidade aparece em QUALQUER tela do app, não só
 * no mapa: quem está em viagem pode ter ido olhar as Rotas Salvas.
 */

jest.mock("@/lib/api", () => ({
  buscarUsuarioAtual: jest.fn(),
  logoutUsuario: jest.fn(),
  atualizarFirstAccess: jest.fn(),
  buscarViagemAtiva: jest.fn(),
  confirmarAvisoDeProximidade: jest.fn(),
}));

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
}));

const VIAGEM = {
  id: "v-1",
  numeroLinha: "0.110",
  sentido: "IDA",
  veiculoPrefixo: "440001",
  paradaDestinoCodigo: "PR-C",
  embarcouEm: "2026-10-14T15:00:00Z",
  sinal: "ao_vivo" as const,
  veiculo: null,
  destino: null,
  proximaParada: null,
  paradasRestantes: [],
  avisoProximidade: {
    id: "a-1",
    paradaCodigo: "PR-C",
    paradaNome: "Terminal Central",
    etaMinutos: 2,
    disparadoEm: "2026-10-14T15:30:00Z",
  },
};

describe("AppShell — aviso de proximidade (US #172)", () => {
  beforeEach(() => {
    (buscarUsuarioAtual as jest.Mock).mockReset().mockResolvedValue(null);
    (confirmarAvisoDeProximidade as jest.Mock).mockReset().mockResolvedValue(undefined);
    (buscarViagemAtiva as jest.Mock)
      .mockReset()
      .mockResolvedValue({ falhou: false, viagem: VIAGEM });
  });

  it.each(["mapa", "favoritos", "ocorrencias"])(
    "na tela %s, o aviso aparece",
    async (tela) => {
      render(
        <AppShell active={tela}>
          <div>conteúdo</div>
        </AppShell>
      );

      const aviso = await screen.findByRole("alert");
      expect(aviso).toHaveTextContent("Seu ônibus está chegando");
      expect(aviso).toHaveTextContent("Terminal Central");
    }
  );

  it("'Entendi' dispensa o aviso e confirma a viagem certa", async () => {
    render(
      <AppShell active="favoritos">
        <div>conteúdo</div>
      </AppShell>
    );
    await screen.findByRole("alert");

    fireEvent.click(screen.getByRole("button", { name: "Entendi" }));

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(confirmarAvisoDeProximidade).toHaveBeenCalledWith("v-1");
  });

  it("sem aviso pendente, nenhum alerta na tela", async () => {
    (buscarViagemAtiva as jest.Mock).mockResolvedValue({
      falhou: false,
      viagem: { ...VIAGEM, avisoProximidade: null },
    });

    render(
      <AppShell active="favoritos">
        <div>conteúdo</div>
      </AppShell>
    );

    await screen.findByRole("link", { name: /Em viagem na linha 0.110/ });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
