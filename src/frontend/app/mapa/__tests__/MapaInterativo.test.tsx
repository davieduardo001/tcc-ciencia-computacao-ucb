import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import MapaInterativo, { escolherBaseDoMapa } from "../MapaInterativo";
import { LinhaDetalhada, OpcaoViagem, VeiculoAoVivo } from "@/lib/api";
import { buscarPosicoesDaLinha } from "@/lib/api";

// US #16: o componente busca a posição ao vivo sozinho e repete a cada
// 20s. Só `buscarPosicoesDaLinha` precisa de dublê — o resto do módulo
// que ele importa são tipos, apagados na compilação.
jest.mock("@/lib/api", () => ({
  buscarPosicoesDaLinha: jest.fn().mockResolvedValue([]),
}));

const buscarPosicoesMock = buscarPosicoesDaLinha as jest.Mock;

jest.mock("react-leaflet", () => ({
  MapContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="map-container">{children}</div>
  ),
  TileLayer: ({
    url,
    attribution,
    subdomains,
  }: {
    url?: string;
    attribution?: string;
    subdomains?: string;
  }) => (
    <div
      data-testid="tile-layer"
      data-url={url}
      data-attribution={attribution}
      data-subdomains={subdomains}
    />
  ),
  Marker: ({
    icon,
    children,
  }: {
    icon?: { className?: string; html?: string };
    children?: React.ReactNode;
  }) => (
    <div
      data-testid={`marcador-${icon?.className ?? "generico"}`}
      data-classe={icon?.className}
      data-html={icon?.html}
    >
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
  // Vários componentes chamam useMapEvents (clique pra escolher ponto,
  // aviso de zoom). Acumula em vez de sobrescrever — do contrário o
  // último a montar apagaria os handlers dos outros.
  useMapEvents: (handlers: Record<string, (e?: unknown) => void>) => {
    Object.assign(handlersDeMapa, handlers);
    return null;
  },
}));

/** Handlers registrados via useMapEvents, pra simular eventos do mapa. */
const handlersDeMapa: Record<string, ((evento?: unknown) => void) | undefined> = {};

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

  it("mostra rótulo neutro quando a parada não tem nome cadastrado", () => {
    // 582 dos 7.142 abrigos do SEMOB vêm só com o CEP no endereço; o
    // backend manda nome vazio em vez de exibir "CEP: 71596-265".
    const semNome: LinhaDetalhada = {
      ...LINHA_TESTE,
      paradas: [{ nome: "", lat: -15.833, lng: -48.05 }],
    };

    render(<MapaInterativo linha={semNome} />);

    expect(
      screen.getAllByText("Parada sem nome cadastrado").length
    ).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// US #20 — itinerário origem → destino desenhado no mapa
// ---------------------------------------------------------------------------

const VIAGEM_COM_BALDEACAO: OpcaoViagem = {
  pernas: [
    {
      numero: "0.186",
      sentido: "IDA",
      nome: "0.186 — Aeroporto / Rodoviária",
      embarque: {
        lat: -15.87,
        lng: -47.92,
        parada_nome: "Estrada Parque Aeroporto",
        caminhada_metros: 395,
      },
      desembarque: {
        lat: -15.794,
        lng: -47.883,
        parada_nome: "Eixo W Central, Setor Bancário Sul",
        caminhada_metros: 99,
      },
      distancia_km: 12.4,
      paradas_no_trecho: 26,
      trajeto: [
        [-15.87, -47.92],
        [-15.794, -47.883],
      ],
    },
    {
      numero: "0.110",
      sentido: "CIRCULAR",
      nome: "0.110 — Circular Rodoviária / UnB",
      embarque: {
        lat: -15.793,
        lng: -47.882,
        parada_nome: "Eixo Rodoviário, Setor Bancário Sul",
        caminhada_metros: 16,
      },
      desembarque: {
        lat: -15.763,
        lng: -47.87,
        parada_nome: "L3 Norte, SQN 408",
        caminhada_metros: 212,
      },
      distancia_km: 5.9,
      paradas_no_trecho: 10,
      trajeto: [
        [-15.793, -47.882],
        [-15.763, -47.87],
      ],
    },
  ],
  baldeacoes: 1,
  distancia_km: 18.3,
  caminhada_metros: 722,
  duracao_estimada_min: 65,
};

describe("MapaInterativo — itinerário da viagem (US #20)", () => {
  beforeEach(() => {
    mockGeolocation({
      getCurrentPosition: jest.fn() as unknown as Geolocation["getCurrentPosition"],
    });
  });

  it("desenha uma polilinha por perna, com cores diferentes", () => {
    render(<MapaInterativo viagem={VIAGEM_COM_BALDEACAO} />);

    const linhas = screen.getAllByTestId("polyline");
    expect(linhas).toHaveLength(2);
    expect(linhas[0].getAttribute("data-cor")).not.toBe(
      linhas[1].getAttribute("data-cor")
    );
  });

  it("marca embarque, baldeação e desembarque", () => {
    render(<MapaInterativo viagem={VIAGEM_COM_BALDEACAO} />);

    expect(
      screen.getByTestId("marcador-mapa-icone-viagem embarque")
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("marcador-mapa-icone-viagem baldeacao")
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("marcador-mapa-icone-viagem desembarque")
    ).toBeInTheDocument();
  });

  it("marca origem e destino informados pelo usuário", () => {
    render(
      <MapaInterativo
        viagem={VIAGEM_COM_BALDEACAO}
        origemViagem={{ nome: "Aeroporto JK", lat: -15.87, lng: -47.92 }}
        destinoViagem={{ nome: "UnB", lat: -15.763, lng: -47.87 }}
      />
    );

    expect(
      screen.getByTestId("marcador-mapa-icone-viagem origem")
    ).toBeInTheDocument();
    expect(screen.getByText("Aeroporto JK")).toBeInTheDocument();
    expect(screen.getByText("UnB")).toBeInTheDocument();
  });

  it("no modo escolher ponto, o clique no mapa devolve a coordenada", () => {
    const onCliqueNoMapa = jest.fn();
    render(
      <MapaInterativo escolhendoNoMapa onCliqueNoMapa={onCliqueNoMapa} />
    );

    expect(screen.getByRole("status")).toHaveTextContent(
      "Toque no mapa para escolher o ponto."
    );

    handlersDeMapa.click?.({ latlng: { lat: -15.8, lng: -48.1 } });

    expect(onCliqueNoMapa).toHaveBeenCalledWith(-15.8, -48.1);
  });

  it("fora do modo escolher ponto, o clique no mapa é ignorado", () => {
    const onCliqueNoMapa = jest.fn();
    render(<MapaInterativo onCliqueNoMapa={onCliqueNoMapa} />);

    handlersDeMapa.click?.({ latlng: { lat: -15.8, lng: -48.1 } });

    expect(onCliqueNoMapa).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// US #16 — posição do ônibus em tempo real
// ---------------------------------------------------------------------------

const VEICULO: VeiculoAoVivo = {
  linha: "0.110",
  prefixo: "446475",
  direcao: 218.72,
  lat: -15.80459,
  lng: -47.92445,
  sentido: "VOLTA",
  velocidade: 41,
  atualizadoEm: "2026-09-13T22:13:22",
  operadora: "VIAÇÃO PIRACICABANA - BACIA 01",
};

describe("MapaInterativo — rastreamento ao vivo (US #16)", () => {
  beforeEach(() => {
    mockGeolocation({
      getCurrentPosition: jest.fn() as unknown as Geolocation["getCurrentPosition"],
    });
    buscarPosicoesMock.mockReset().mockResolvedValue([]);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("cenário 1: desenha um marcador por ônibus em operação", async () => {
    buscarPosicoesMock.mockResolvedValue([
      VEICULO,
      { ...VEICULO, prefixo: "446149", lat: -15.81 },
    ]);

    render(<MapaInterativo linha={LINHA_TESTE} />);

    await waitFor(() => {
      expect(screen.getAllByTestId("marcador-mapa-icone-onibus")).toHaveLength(2);
    });
    expect(buscarPosicoesMock).toHaveBeenCalledWith(LINHA_TESTE.numero);
  });

  it("cenário 2: atualiza sozinho, sem recarregar a página", async () => {
    jest.useFakeTimers();
    buscarPosicoesMock.mockResolvedValue([VEICULO]);

    render(<MapaInterativo linha={LINHA_TESTE} />);

    await act(async () => {});
    expect(buscarPosicoesMock).toHaveBeenCalledTimes(1);

    await act(async () => {
      jest.advanceTimersByTime(20000);
    });
    expect(buscarPosicoesMock).toHaveBeenCalledTimes(2);

    await act(async () => {
      jest.advanceTimersByTime(20000);
    });
    expect(buscarPosicoesMock).toHaveBeenCalledTimes(3);
  });

  it("cenário 3: avisa quando nenhum ônibus está em operação", async () => {
    buscarPosicoesMock.mockResolvedValue([]);

    render(<MapaInterativo linha={LINHA_TESTE} />);

    await waitFor(() => {
      expect(
        screen.getByText(/Nenhum ônibus desta linha em operação no momento/)
      ).toBeInTheDocument();
    });
    expect(screen.queryByTestId("marcador-mapa-icone-onibus")).not.toBeInTheDocument();
  });

  it("para de consultar ao fechar a linha, sem vazar o intervalo", async () => {
    jest.useFakeTimers();
    buscarPosicoesMock.mockResolvedValue([VEICULO]);

    const { rerender, unmount } = render(<MapaInterativo linha={LINHA_TESTE} />);
    await act(async () => {});
    expect(buscarPosicoesMock).toHaveBeenCalledTimes(1);

    // Linha fechada: nada mais a rastrear.
    rerender(<MapaInterativo linha={null} />);
    await act(async () => {
      jest.advanceTimersByTime(60000);
    });
    expect(buscarPosicoesMock).toHaveBeenCalledTimes(1);

    unmount();
    await act(async () => {
      jest.advanceTimersByTime(60000);
    });
    expect(buscarPosicoesMock).toHaveBeenCalledTimes(1);
  });

  it("sem linha selecionada não busca posição nenhuma", async () => {
    render(<MapaInterativo />);
    await act(async () => {});

    expect(buscarPosicoesMock).not.toHaveBeenCalled();
  });
});

describe("MapaInterativo — rastreio das linhas do itinerário (US #16 + #20)", () => {
  beforeEach(() => {
    mockGeolocation({
      getCurrentPosition: jest.fn() as unknown as Geolocation["getCurrentPosition"],
    });
    buscarPosicoesMock.mockReset().mockResolvedValue([]);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("rastreia todas as linhas do itinerário, não só uma", async () => {
    // Sem isso, quem planejava "Taguatinga → UCB" via a linha no
    // resultado e não tinha como ver onde o ônibus estava — precisava
    // buscar a linha pelo número numa segunda busca.
    buscarPosicoesMock.mockResolvedValue([]);

    render(<MapaInterativo viagem={VIAGEM_COM_BALDEACAO} />);

    await waitFor(() => {
      expect(buscarPosicoesMock).toHaveBeenCalledTimes(2);
    });
    expect(buscarPosicoesMock).toHaveBeenCalledWith("0.186");
    expect(buscarPosicoesMock).toHaveBeenCalledWith("0.110");
  });

  it("desenha os ônibus das duas pernas no mapa", async () => {
    buscarPosicoesMock
      .mockResolvedValueOnce([{ ...VEICULO, linha: "0.186", prefixo: "A1" }])
      .mockResolvedValueOnce([{ ...VEICULO, linha: "0.110", prefixo: "B1" }]);

    render(<MapaInterativo viagem={VIAGEM_COM_BALDEACAO} />);

    await waitFor(() => {
      expect(screen.getAllByTestId("marcador-mapa-icone-onibus")).toHaveLength(2);
    });
  });

  it("repassa os ônibus rastreados para quem desenha o painel", async () => {
    const onVeiculos = jest.fn();
    buscarPosicoesMock.mockResolvedValue([
      { ...VEICULO, linha: "0.186", prefixo: "A1" },
    ]);

    render(
      <MapaInterativo viagem={VIAGEM_COM_BALDEACAO} onVeiculos={onVeiculos} />
    );

    await waitFor(() => {
      const ultimo = onVeiculos.mock.calls.at(-1)?.[0];
      expect(ultimo).toHaveLength(2);
    });
  });

  it("não rastreia nada quando não há linha nem itinerário", async () => {
    render(<MapaInterativo />);
    await act(async () => {});

    expect(buscarPosicoesMock).not.toHaveBeenCalled();
  });
});

describe("MapaInterativo — base do mapa", () => {
  beforeEach(() => {
    mockGeolocation({
      getCurrentPosition: jest.fn() as unknown as Geolocation["getCurrentPosition"],
    });
  });

  /**
   * Regressão que só apareceu na tela: a CARTO passou a exigir chave e,
   * sem ela, responde 200 com um PNG válido — com "API KEY REQUIRED"
   * estampado na imagem. Conferir status HTTP e tamanho em bytes não
   * detecta isso.
   */
  it("sem chave da CARTO, usa o tile do OpenStreetMap", () => {
    const base = escolherBaseDoMapa(undefined);

    expect(base.url).toContain("tile.openstreetmap.org");
    expect(base.url).not.toContain("cartocdn");
    expect(base.atribuicao).toContain("OpenStreetMap");
  });

  it("chave vazia ou só espaços conta como ausente", () => {
    expect(escolherBaseDoMapa("").url).toContain("tile.openstreetmap.org");
    expect(escolherBaseDoMapa("   ").url).toContain("tile.openstreetmap.org");
  });

  it("com chave, usa o CARTO Voyager e manda a chave na URL", () => {
    const base = escolherBaseDoMapa("abc123");

    expect(base.url).toContain("basemaps.cartocdn.com/rastertiles/voyager");
    expect(base.url).toContain("key=abc123");
    // {r} vira "@2x" em tela retina; {s} varre os quatro subdomínios.
    expect(base.url).toContain("{r}");
    expect(base.subdominios).toBe("abcd");
  });

  it("a base da CARTO credita OpenStreetMap e CARTO — é obrigação de licença", () => {
    // Os dados são do OpenStreetMap; a CARTO faz só o estilo. Omitir
    // qualquer um dos dois viola os termos de uso das duas.
    const base = escolherBaseDoMapa("abc123");

    expect(base.atribuicao).toContain("OpenStreetMap");
    expect(base.atribuicao).toContain("CARTO");
    expect(base.atribuicao).toContain("carto.com/attributions");
  });

  it("o mapa renderiza a base escolhida, com atribuição", () => {
    render(<MapaInterativo />);

    const tiles = screen.getByTestId("tile-layer");
    expect(tiles.getAttribute("data-url")).toBeTruthy();
    expect(tiles.getAttribute("data-attribution")).toContain("OpenStreetMap");
  });
});

describe("MapaInterativo — o ônibus parece que anda (US #16)", () => {
  beforeEach(() => {
    mockGeolocation({
      getCurrentPosition: jest.fn() as unknown as Geolocation["getCurrentPosition"],
    });
    buscarPosicoesMock.mockReset().mockResolvedValue([]);
  });

  it("aponta a seta na direção que o ônibus está indo", async () => {
    // O feed traz `direcao` em graus e a gente ignorava. Sem ela o
    // ônibus é um ponto sem orientação no mapa.
    buscarPosicoesMock.mockResolvedValue([
      { ...VEICULO, velocidade: 41, direcao: 218.72 },
    ]);

    render(<MapaInterativo linha={LINHA_TESTE} />);

    await waitFor(() => {
      const marcador = screen.getByTestId("marcador-mapa-icone-onibus");
      expect(marcador.getAttribute("data-html")).toContain("rotate(218.72deg)");
    });
  });

  it("ônibus parado não ganha seta nem pulso", async () => {
    // Apontar rumo em quem está a 0 km/h mostraria a direção da última
    // vez que andou — informação errada apresentada como atual.
    buscarPosicoesMock.mockResolvedValue([
      { ...VEICULO, velocidade: 0, direcao: 218.72 },
    ]);

    render(<MapaInterativo linha={LINHA_TESTE} />);

    await waitFor(() => {
      const marcador = screen.getByTestId("marcador-mapa-icone-onibus parado");
      expect(marcador.getAttribute("data-html")).not.toContain("seta");
    });
  });

  it("velocidade abaixo do limiar conta como parado", async () => {
    buscarPosicoesMock.mockResolvedValue([
      { ...VEICULO, velocidade: 1.2, direcao: 90 },
    ]);

    render(<MapaInterativo linha={LINHA_TESTE} />);

    await waitFor(() => {
      expect(
        screen.getByTestId("marcador-mapa-icone-onibus parado")
      ).toBeInTheDocument();
    });
  });

  it("mostra há quanto tempo a posição foi reportada", async () => {
    // O SEMOB renova cada veículo a cada ~28s e consultamos a cada 20s,
    // então a mesma posição às vezes aparece duas vezes. Sem essa linha
    // o usuário lê isso como "o mapa travou".
    const haQuarentaSegundos = new Date(Date.now() - 40_000).toISOString();
    buscarPosicoesMock.mockResolvedValue([
      { ...VEICULO, velocidade: 30, atualizadoEm: haQuarentaSegundos },
    ]);

    render(<MapaInterativo linha={LINHA_TESTE} />);

    await waitFor(() => {
      expect(screen.getByText(/Posição de 4\ds atrás/)).toBeInTheDocument();
    });
  });

  it("desliga a transição durante o zoom, pra frota não sair escorregando", async () => {
    buscarPosicoesMock.mockResolvedValue([VEICULO]);
    const { container } = render(<MapaInterativo linha={LINHA_TESTE} />);

    const canvas = container.querySelector(".mapa-canvas") as HTMLElement;
    expect(canvas.className).not.toContain("em-zoom");

    await act(async () => {
      handlersDeMapa.zoomstart?.();
    });
    expect(canvas.className).toContain("em-zoom");

    await act(async () => {
      handlersDeMapa.zoomend?.();
    });
    expect(canvas.className).not.toContain("em-zoom");
  });
});
