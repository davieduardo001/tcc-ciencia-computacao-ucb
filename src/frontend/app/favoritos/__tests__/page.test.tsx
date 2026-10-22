import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import FavoritosPage from "../page";
import {
  listarFavoritosRemoto,
  removerFavorito,
  cachearFavoritos,
  lerFavoritosCache,
  limparCacheFavoritos,
  SalvarFavoritoError,
} from "@/lib/api";

// Mock do AppShell para não precisar de toda a infraestrutura de navegação.
jest.mock("../../mapa/AppShell", () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="app-shell">{children}</div>
  ),
}));

jest.mock("@/lib/api", () => ({
  listarFavoritosRemoto: jest.fn(),
  removerFavorito: jest.fn(),
  cachearFavoritos: jest.fn(),
  lerFavoritosCache: jest.fn(),
  limparCacheFavoritos: jest.fn(),
  SalvarFavoritoError: class SalvarFavoritoError extends Error {
    status?: number;
    constructor(message: string, status?: number) {
      super(message);
      this.status = status;
    }
  },
}));

const pushMock = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

const listarFavoritosMock = listarFavoritosRemoto as jest.Mock;
const removerFavoritoMock = removerFavorito as jest.Mock;
const lerFavoritosCacheMock = lerFavoritosCache as jest.Mock;

const FAV_A = {
  id: "uuid-a",
  usuario_id: "uuid-user",
  numero_linha: "0.110",
  nome_linha: "0.110 — Taguatinga / Rodoviária",
  label: "Casa → Trabalho",
  origem_lat: -15.8305,
  origem_lng: -48.0425,
  destino_lat: -15.7939,
  destino_lng: -47.8828,
  criado_em: "2026-10-05T14:30:00",
};

const FAV_B = {
  ...FAV_A,
  id: "uuid-b",
  label: "Trabalho → Academia",
  numero_linha: "0.108",
};

describe("FavoritosPage", () => {
  beforeEach(() => {
    listarFavoritosMock.mockReset();
    removerFavoritoMock.mockReset();
    lerFavoritosCacheMock.mockReset();
    pushMock.mockReset();
    lerFavoritosCacheMock.mockReturnValue([]);
  });

  it("exibe mensagem de carregando enquanto a lista chega", () => {
    // Promise que nunca resolve — simula loading
    listarFavoritosMock.mockReturnValue(new Promise(() => {}));

    render(<FavoritosPage />);
    expect(screen.getByText(/Carregando/i)).toBeInTheDocument();
  });

  it("exibe estado vazio quando não há favoritos", async () => {
    listarFavoritosMock.mockResolvedValue([]);

    render(<FavoritosPage />);

    await waitFor(() => {
      expect(
        screen.getByText(/Você ainda não salvou nenhuma rota/i)
      ).toBeInTheDocument();
    });
  });

  it("exibe lista de favoritos após carregar", async () => {
    listarFavoritosMock.mockResolvedValue([FAV_A, FAV_B]);

    render(<FavoritosPage />);

    await waitFor(() => {
      expect(screen.getByText("Casa → Trabalho")).toBeInTheDocument();
      expect(screen.getByText("Trabalho → Academia")).toBeInTheDocument();
    });
  });

  it("exibe o cache imediatamente antes da resposta do servidor", async () => {
    lerFavoritosCacheMock.mockReturnValue([FAV_A]);
    // Servidor demora
    listarFavoritosMock.mockReturnValue(
      new Promise((resolve) => setTimeout(() => resolve([FAV_A]), 500))
    );

    render(<FavoritosPage />);

    // Cache exibido imediatamente
    expect(screen.getByText("Casa → Trabalho")).toBeInTheDocument();
  });

  it("botão remover chama removerFavorito com o ID correto", async () => {
    listarFavoritosMock.mockResolvedValue([FAV_A]);
    removerFavoritoMock.mockResolvedValue(undefined);

    render(<FavoritosPage />);

    await waitFor(() => {
      expect(screen.getByText("Casa → Trabalho")).toBeInTheDocument();
    });

    fireEvent.click(
      screen.getByLabelText(`Remover ${FAV_A.label} dos favoritos`)
    );

    await waitFor(() => {
      expect(removerFavoritoMock).toHaveBeenCalledWith("uuid-a");
    });
  });

  it("favorito é removido da lista após remoção bem-sucedida", async () => {
    listarFavoritosMock.mockResolvedValue([FAV_A, FAV_B]);
    removerFavoritoMock.mockResolvedValue(undefined);

    render(<FavoritosPage />);

    await waitFor(() => {
      expect(screen.getByText("Casa → Trabalho")).toBeInTheDocument();
    });

    fireEvent.click(
      screen.getByLabelText(`Remover ${FAV_A.label} dos favoritos`)
    );

    await waitFor(() => {
      expect(screen.queryByText("Casa → Trabalho")).not.toBeInTheDocument();
      expect(screen.getByText("Trabalho → Academia")).toBeInTheDocument();
    });
  });

  it("exibe mensagem de erro quando remoção falha", async () => {
    listarFavoritosMock.mockResolvedValue([FAV_A]);
    removerFavoritoMock.mockRejectedValue(
      new SalvarFavoritoError("Você não tem permissão.", 403)
    );

    render(<FavoritosPage />);

    await waitFor(() => {
      expect(screen.getByText("Casa → Trabalho")).toBeInTheDocument();
    });

    fireEvent.click(
      screen.getByLabelText(`Remover ${FAV_A.label} dos favoritos`)
    );

    await waitFor(() => {
      expect(
        screen.getByText("Você não tem permissão.")
      ).toBeInTheDocument();
    });
  });

  it("botão Ir navega para /mapa com query params corretos", async () => {
    listarFavoritosMock.mockResolvedValue([FAV_A]);

    render(<FavoritosPage />);

    await waitFor(() => {
      expect(screen.getByText("Casa → Trabalho")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByLabelText(`Abrir rota ${FAV_A.label} no mapa`));

    expect(pushMock).toHaveBeenCalledWith(
      expect.stringContaining("/mapa?")
    );
    expect(pushMock).toHaveBeenCalledWith(
      expect.stringContaining("painel=rotas")
    );
    expect(pushMock).toHaveBeenCalledWith(
      expect.stringContaining("origem_lat=-15.8305")
    );
    expect(pushMock).toHaveBeenCalledWith(
      expect.stringContaining("destino_lat=-15.7939")
    );
  });

  it("exibe banner offline e mantém o cache quando o servidor não responde", async () => {
    lerFavoritosCacheMock.mockReturnValue([FAV_A]);
    listarFavoritosMock.mockRejectedValue(new Error("rede fora"));

    render(<FavoritosPage />);

    await waitFor(() => {
      expect(screen.getByText(/Você está offline/i)).toBeInTheDocument();
    });
    expect(screen.getByText("Casa → Trabalho")).toBeInTheDocument();
  });

  it("não exibe banner offline quando o servidor responde", async () => {
    lerFavoritosCacheMock.mockReturnValue([FAV_A]);
    listarFavoritosMock.mockResolvedValue([FAV_A]);

    render(<FavoritosPage />);

    await waitFor(() => {
      expect(screen.getByText("Casa → Trabalho")).toBeInTheDocument();
    });
    expect(screen.queryByText(/Você está offline/i)).not.toBeInTheDocument();
  });

  it("botão Ir para o mapa no estado vazio navega para /mapa?painel=rotas", async () => {
    listarFavoritosMock.mockResolvedValue([]);

    render(<FavoritosPage />);

    await waitFor(() => {
      expect(
        screen.getByText(/Você ainda não salvou nenhuma rota/i)
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Ir para o mapa"));
    expect(pushMock).toHaveBeenCalledWith("/mapa?painel=rotas");
  });
});
