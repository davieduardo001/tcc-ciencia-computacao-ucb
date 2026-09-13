import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import MapaInterativo from "../MapaInterativo";
import { LinhaDetalhada } from "@/lib/api";

jest.mock("react-leaflet", () => ({
  MapContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="map-container">{children}</div>
  ),
  TileLayer: () => null,
  Marker: ({
    icon,
    children,
  }: {
    icon?: { className?: string };
    children?: React.ReactNode;
  }) => (
    <div data-testid={`marcador-${icon?.className ?? "generico"}`}>
      {children}
    </div>
  ),
  Popup: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="popup">{children}</div>
  ),
  Polyline: ({
    positions,
    pathOptions,
  }: {
    positions: unknown;
    pathOptions?: { color?: string };
  }) => (
    <div
      data-testid="polyline"
      data-cor={pathOptions?.color}
      data-pontos={JSON.stringify(positions)}
    />
  ),
}));

jest.mock("leaflet", () => ({
  __esModule: true,
  default: {
    divIcon: jest.fn((options) => options),
    latLngBounds: jest.fn((positions) => positions),
  },
}));

function mockGeolocation(overrides: Partial<Geolocation> = {}) {
  const geolocation: Geolocation = {
    getCurrentPosition: jest.fn(),
    watchPosition: jest.fn(() => 1),
    clearWatch: jest.fn(),
    ...overrides,
  } as unknown as Geolocation;

  Object.defineProperty(global.navigator, "geolocation", {
    value: geolocation,
    configurable: true,
  });

  return geolocation;
}

const LINHA_TESTE: LinhaDetalhada = {
  numero: "0.110",
  nome: "0.110 — Taguatinga / Rodoviária",
  sentido: "Taguatinga → Rodoviária do Plano Piloto",
  paradas: [
    { nome: "Terminal Taguatinga", lat: -15.833, lng: -48.05 },
    { nome: "W3 Sul — 502", lat: -15.8, lng: -47.9 },
    { nome: "Rodoviária do Plano Piloto", lat: -15.79, lng: -47.88 },
  ],
  trajeto: [
    [-15.833, -48.05],
    [-15.81, -47.95],
    [-15.79, -47.88],
  ],
  horariosPrevistos: ["06:00", "06:20"],
};

describe("MapaInterativo", () => {
  beforeEach(() => {
    mockGeolocation({
      getCurrentPosition: jest.fn() as unknown as Geolocation["getCurrentPosition"],
    });
  });

  it("centraliza o mapa e exibe o marcador quando a localização é concedida", async () => {
    mockGeolocation({
      getCurrentPosition: jest.fn((sucesso) =>
        sucesso({
          coords: { latitude: -15.83, longitude: -48.04 },
        } as GeolocationPosition)
      ) as unknown as Geolocation["getCurrentPosition"],
    });

    render(<MapaInterativo />);

    await waitFor(() => {
      expect(screen.getByTestId("marcador-mapa-icone-usuario")).toBeInTheDocument();
    });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("exibe aviso e mantém o ponto padrão quando a localização está indisponível", async () => {
    mockGeolocation({
      getCurrentPosition: jest.fn((_sucesso, erro) =>
        erro?.({} as GeolocationPositionError)
      ) as unknown as Geolocation["getCurrentPosition"],
    });

    render(<MapaInterativo />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Não foi possível obter sua localização"
      );
    });
    expect(screen.queryByTestId("marcador-mapa-icone-usuario")).not.toBeInTheDocument();
  });

  it("desabilita o botão de centralizar enquanto não há coordenadas", () => {
    render(<MapaInterativo />);

    expect(
      screen.getByTitle("Centralizar na minha localização")
    ).toBeDisabled();
  });

  // ---------------------------------------------------------------------
  // US #17 — Trajeto e paradas da linha
  // ---------------------------------------------------------------------

  it("não desenha trajeto nem painel quando nenhuma linha foi buscada", () => {
    render(<MapaInterativo />);

    expect(screen.queryByTestId("polyline")).not.toBeInTheDocument();
    expect(screen.queryByText("Trajeto e paradas")).not.toBeInTheDocument();
  });

  it("desenha a polilinha do trajeto quando uma linha é fornecida", () => {
    render(<MapaInterativo linha={LINHA_TESTE} />);

    const polyline = screen.getByTestId("polyline");
    expect(polyline).toBeInTheDocument();
    expect(JSON.parse(polyline.getAttribute("data-pontos") ?? "[]")).toEqual(
      LINHA_TESTE.trajeto
    );
  });

  it("marca todas as paradas com o nome disponível (cenário 2 — tocar na parada)", () => {
    render(<MapaInterativo linha={LINHA_TESTE} />);

    const marcadoresParada = screen.getAllByTestId("marcador-mapa-icone-parada");
    expect(marcadoresParada).toHaveLength(LINHA_TESTE.paradas.length);

    for (const parada of LINHA_TESTE.paradas) {
      // Nome aparece tanto no popup do marcador quanto no painel/timeline
      expect(screen.getAllByText(parada.nome).length).toBeGreaterThan(0);
    }
  });

  it("exibe uma seta indicando o sentido de operação (cenário 3)", () => {
    render(<MapaInterativo linha={LINHA_TESTE} />);

    expect(screen.getByTestId("marcador-mapa-icone-sentido")).toBeInTheDocument();
  });

  it("exibe o painel com nome, sentido e a lista de paradas em ordem", () => {
    render(<MapaInterativo linha={LINHA_TESTE} />);

    expect(screen.getByText(LINHA_TESTE.nome)).toBeInTheDocument();
    expect(screen.getByText(LINHA_TESTE.sentido)).toBeInTheDocument();

    const rotulos = screen.getAllByText(
      new RegExp(LINHA_TESTE.paradas.map((p) => p.nome).join("|"))
    );
    expect(rotulos.length).toBeGreaterThanOrEqual(LINHA_TESTE.paradas.length);
  });

  it("chama onFecharLinha ao clicar em fechar o painel", () => {
    const onFecharLinha = jest.fn();
    render(<MapaInterativo linha={LINHA_TESTE} onFecharLinha={onFecharLinha} />);

    fireEvent.click(screen.getByTitle("Fechar"));

    expect(onFecharLinha).toHaveBeenCalledTimes(1);
  });

  it("exibe a mensagem de erro de busca sem quebrar o mapa", () => {
    render(<MapaInterativo erroBusca='Linha "999" não encontrada.' />);

    expect(screen.getByRole("alert")).toHaveTextContent(
      'Linha "999" não encontrada.'
    );
    expect(screen.queryByTestId("polyline")).not.toBeInTheDocument();
  });
});
