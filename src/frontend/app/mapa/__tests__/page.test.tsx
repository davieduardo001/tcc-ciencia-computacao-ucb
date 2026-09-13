import { act, fireEvent, render, screen } from "@testing-library/react";
import MapaPage from "../page";
import { sugerirLinhas } from "@/lib/api";

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
}));

// O mapa em si depende de Leaflet/DOM real — aqui só interessa a busca.
jest.mock("../MapaInterativo", () => ({
  __esModule: true,
  default: () => <div data-testid="mapa-interativo" />,
}));

jest.mock("@/lib/api", () => ({
  sugerirLinhas: jest.fn(),
  buscarLinha: jest.fn(),
  buscarUsuarioAtual: jest.fn().mockResolvedValue(null),
  logoutUsuario: jest.fn().mockResolvedValue(undefined),
  BuscarLinhaError: class BuscarLinhaError extends Error {},
}));

const sugerirLinhasMock = sugerirLinhas as jest.Mock;
const PLACEHOLDER = "Buscar linha ou destino (ex: 0.110 ou Ceilândia)";

const LINHA = {
  numero: "0.110",
  nome: "0.110 — Circular Rodoviária / UnB",
  sentido: "Circular",
};

describe("MapaPage — sugestões de busca", () => {
  beforeEach(() => {
    sugerirLinhasMock.mockReset();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  /**
   * Regressão: digitar "asa norte" mostrava todas as linhas na lista.
   * A busca disparada por um prefixo anterior (ex: "a", que casa com
   * quase toda linha) respondia DEPOIS da busca final e sobrescrevia o
   * resultado correto. O resultado aplicado tem que ser sempre o da
   * busca mais recente, não o da última resposta a chegar.
   */
  it("ignora a resposta de uma busca antiga que chega depois da mais recente", async () => {
    let resolverAntiga: (v: unknown) => void = () => {};
    let resolverRecente: (v: unknown) => void = () => {};

    sugerirLinhasMock
      .mockImplementationOnce(
        () => new Promise((resolve) => {
          resolverAntiga = resolve;
        })
      )
      .mockImplementationOnce(
        () => new Promise((resolve) => {
          resolverRecente = resolve;
        })
      );

    jest.useFakeTimers();
    render(<MapaPage />);

    const input = screen.getByPlaceholderText(PLACEHOLDER);

    // 1ª digitação ("a") — dispara a busca ampla
    fireEvent.change(input, { target: { value: "a" } });
    act(() => {
      jest.advanceTimersByTime(400);
    });

    // 2ª digitação ("asa norte") — dispara a busca específica
    fireEvent.change(input, { target: { value: "asa norte" } });
    act(() => {
      jest.advanceTimersByTime(400);
    });

    expect(sugerirLinhasMock).toHaveBeenCalledTimes(2);

    // Respostas fora de ordem: a recente (vazia) chega primeiro...
    await act(async () => {
      resolverRecente([]);
    });
    // ...e a antiga (com tudo) chega depois e NÃO pode sobrescrever.
    await act(async () => {
      resolverAntiga([LINHA]);
    });

    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    expect(screen.queryByText(LINHA.nome)).not.toBeInTheDocument();
  });

  it("mostra as sugestões da busca mais recente", async () => {
    sugerirLinhasMock.mockResolvedValue([LINHA]);

    jest.useFakeTimers();
    render(<MapaPage />);

    fireEvent.change(screen.getByPlaceholderText(PLACEHOLDER), {
      target: { value: "0.110" },
    });

    await act(async () => {
      jest.advanceTimersByTime(400);
    });

    fireEvent.focus(screen.getByPlaceholderText(PLACEHOLDER));

    expect(screen.getByText(LINHA.nome)).toBeInTheDocument();
  });

  it("limpa as sugestões quando o campo fica vazio", async () => {
    sugerirLinhasMock.mockResolvedValue([LINHA]);

    jest.useFakeTimers();
    render(<MapaPage />);
    const input = screen.getByPlaceholderText(PLACEHOLDER);

    fireEvent.change(input, { target: { value: "0.110" } });
    await act(async () => {
      jest.advanceTimersByTime(400);
    });
    expect(screen.getByText(LINHA.nome)).toBeInTheDocument();

    fireEvent.change(input, { target: { value: "" } });
    await act(async () => {
      jest.advanceTimersByTime(400);
    });

    expect(screen.queryByText(LINHA.nome)).not.toBeInTheDocument();
  });
});
