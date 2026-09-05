import { render, screen, waitFor } from "@testing-library/react";
import MapaInterativo from "../MapaInterativo";

jest.mock("react-leaflet", () => ({
  MapContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="map-container">{children}</div>
  ),
  TileLayer: () => null,
  Marker: () => <div data-testid="marcador-posicao-atual" />,
}));

jest.mock("leaflet", () => ({
  __esModule: true,
  default: {
    divIcon: jest.fn(() => ({})),
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

describe("MapaInterativo", () => {
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
      expect(screen.getByTestId("marcador-posicao-atual")).toBeInTheDocument();
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
    expect(screen.queryByTestId("marcador-posicao-atual")).not.toBeInTheDocument();
  });

  it("desabilita o botão de centralizar enquanto não há coordenadas", () => {
    mockGeolocation({
      getCurrentPosition: jest.fn() as unknown as Geolocation["getCurrentPosition"],
    });

    render(<MapaInterativo />);

    expect(
      screen.getByTitle("Centralizar na minha localização")
    ).toBeDisabled();
  });
});
