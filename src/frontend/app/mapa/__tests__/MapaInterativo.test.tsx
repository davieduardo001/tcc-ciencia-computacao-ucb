import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import MapaInterativo, { escolherBaseDoMapa } from "../MapaInterativo";
import { ChegadasDaParada, DetalhesParada, LinhaDetalhada, OpcaoViagem, VeiculoAoVivo } from "@/lib/api";
import { buscarChegadasParada, buscarDetalhesParada, buscarPosicoesDaLinha, BuscarParadaError } from "@/lib/api";
import { buscarViagemAtiva, embarcarNoOnibus, ViagemAtiva } from "@/lib/api";
import { ViagemProvider } from "../ViagemContext";

// US #16 e #18: o componente busca posição ao vivo e detalhes de parada
// sozinho — precisam de dublê. `BuscarParadaError` é uma classe usada em
// `instanceof` no catch, então precisa existir de verdade no mock (não
// só um jest.fn()). O resto do módulo que o componente importa são
// tipos, apagados na compilação.
jest.mock("@/lib/api", () => ({
  buscarPosicoesDaLinha: jest
    .fn()
    .mockResolvedValue({ veiculos: [], proximoHorarioPrevisto: null }),
  buscarDetalhesParada: jest.fn().mockResolvedValue(null),
  buscarChegadasParada: jest.fn().mockResolvedValue(null),
  BuscarParadaError: class BuscarParadaError extends Error {},
  // US #171 — usadas só pelos testes que montam o ViagemProvider.
  buscarViagemAtiva: jest.fn().mockResolvedValue({ falhou: false, viagem: null }),
  embarcarNoOnibus: jest.fn(),
  definirDestinoDaViagem: jest.fn(),
  encerrarViagem: jest.fn(),
  ViagemError: class ViagemError extends Error {
    status?: number;
    constructor(message: string, status?: number) {
      super(message);
      this.status = status;
    }
  },
}));

/** US #19: embrulha uma lista de veículos no formato que a API devolve. */
function resultadoPosicoes(
  veiculos: VeiculoAoVivo[],
  proximoHorarioPrevisto: string | null = null
) {
  return { veiculos, proximoHorarioPrevisto };
}

const buscarPosicoesMock = buscarPosicoesDaLinha as jest.Mock;
const buscarDetalhesParadaMock = buscarDetalhesParada as jest.Mock;
const buscarChegadasParadaMock = buscarChegadasParada as jest.Mock;

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
    eventHandlers,
  }: {
    icon?: { className?: string; html?: string };
    children?: React.ReactNode;
    eventHandlers?: { click?: () => void };
  }) => (
    <div
      data-testid={`marcador-${icon?.className ?? "generico"}`}
      data-classe={icon?.className}
      data-html={icon?.html}
      onClick={eventHandlers?.click}
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
    buscarDetalhesParadaMock.mockClear().mockResolvedValue(null);
    buscarChegadasParadaMock.mockClear().mockResolvedValue(null);
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

  it("tem um atalho pra reportar ocorrência já com a linha preenchida", () => {
    render(<MapaInterativo linha={LINHA_TESTE} />);

    const atalho = screen.getByText("Reportar ocorrência nesta linha");
    expect(atalho.closest("a")).toHaveAttribute(
      "href",
      "/ocorrencias/reportar?linha=0.110"
    );
  });

  it("tem um atalho pra ver as ocorrências já filtradas pela linha (US #24)", () => {
    render(<MapaInterativo linha={LINHA_TESTE} />);

    const atalho = screen.getByText("Ver ocorrências desta linha");
    expect(atalho.closest("a")).toHaveAttribute("href", "/ocorrencias?linha=0.110");
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

  // ---------------------------------------------------------------------
  // US #18 — Detalhes de uma parada
  // ---------------------------------------------------------------------

  const DETALHE_PARADA_TESTE: DetalhesParada = {
    nome: "W3 Sul — 502",
    codigo: "PR-12345",
    lat: -15.8,
    lng: -47.9,
    linhas: [
      {
        numero: "0.110",
        nome: "0.110 — Taguatinga / Rodoviária",
        sentido: "Taguatinga → Rodoviária do Plano Piloto",
      },
    ],
    proximosHorarios: ["06:20", "06:40", "07:00"],
  };

  it("abre o painel de detalhes ao tocar na parada, com linhas e horários (cenário 1)", async () => {
    buscarDetalhesParadaMock.mockResolvedValue(DETALHE_PARADA_TESTE);

    render(<MapaInterativo linha={LINHA_TESTE} />);
    fireEvent.click(screen.getAllByTestId("marcador-mapa-icone-parada")[0]);

    await waitFor(() => {
      expect(screen.getByText("06:20 · 06:40 · 07:00")).toBeInTheDocument();
    });

    expect(screen.getByText("Parada PR-12345")).toBeInTheDocument();
    expect(
      screen.getByText(/0\.110 — Taguatinga \/ Rodoviária/)
    ).toBeInTheDocument();

    // Card #179 (RN-10): são saídas do TERMINAL, e o painel diz isso — com o
    // título "Próximos horários" parecia que o ônibus passava ali na hora.
    expect(screen.getByText("Próximas saídas do terminal")).toBeInTheDocument();
    expect(screen.queryByText("Próximos horários")).not.toBeInTheDocument();
    expect(screen.getByText(/não é a hora em que passa nesta parada/)).toBeInTheDocument();

    expect(buscarDetalhesParadaMock).toHaveBeenCalledWith(
      LINHA_TESTE.paradas[0].lat,
      LINHA_TESTE.paradas[0].lng
    );
  });

  it("avisa quando a parada não tem horário previsto disponível (cenário 2)", async () => {
    buscarDetalhesParadaMock.mockResolvedValue({
      ...DETALHE_PARADA_TESTE,
      proximosHorarios: [],
    });

    render(<MapaInterativo linha={LINHA_TESTE} />);
    fireEvent.click(screen.getAllByTestId("marcador-mapa-icone-parada")[0]);

    await waitFor(() => {
      expect(
        screen.getByText(
          "Nenhuma saída prevista disponível para esta parada no momento."
        )
      ).toBeInTheDocument();
    });
  });


  // ---------------------------------------------------------------------
  // Card #179 (⑤b) — Chegando nesta parada
  // ---------------------------------------------------------------------

  const CHEGADAS_TESTE: ChegadasDaParada = {
    paradaCodigo: "PR-12345",
    paradaNome: "W3 Sul — 502",
    calculadoEm: "2026-10-14T15:00:00+00:00",
    chegadas: [
      {
        numero: "0.110",
        nome: "0.110 — Taguatinga / Rodoviária",
        rotaSentido: "IDA",
        etaMinutos: 4.3,
        fonte: "ao_vivo",
        prefixo: "440001",
        veiculosACaminho: 1,
        horarioPrevisto: null,
      },
      {
        numero: "875A",
        nome: "875A — Perdizes",
        rotaSentido: "IDA",
        etaMinutos: 17.6,
        fonte: "previsto",
        prefixo: null,
        veiculosACaminho: 0,
        horarioPrevisto: "15:18",
      },
      {
        numero: "106.2",
        nome: "106.2 — Aeroporto",
        rotaSentido: "IDA",
        etaMinutos: null,
        fonte: null,
        prefixo: null,
        veiculosACaminho: 0,
        horarioPrevisto: null,
      },
    ],
  };

  async function abrirPainelDaParada() {
    buscarDetalhesParadaMock.mockResolvedValue(DETALHE_PARADA_TESTE);
    render(<MapaInterativo linha={LINHA_TESTE} />);
    fireEvent.click(screen.getAllByTestId("marcador-mapa-icone-parada")[0]);
    await screen.findByText("Parada PR-12345");
  }

  it("mostra quando cada linha chega na parada, dizendo de onde vem o número", async () => {
    buscarChegadasParadaMock.mockResolvedValue(CHEGADAS_TESTE);

    await abrirPainelDaParada();

    expect(await screen.findByText("Chegando nesta parada")).toBeInTheDocument();
    expect(buscarChegadasParadaMock).toHaveBeenCalledWith("PR-12345");

    const linhas = screen.getAllByRole("listitem").filter((li) => li.classList.contains("mapa-chegada"));
    expect(linhas).toHaveLength(3);

    // ao vivo: minutos inteiros (4,3 → 4) e o selo
    expect(linhas[0]).toHaveTextContent("0.110");
    expect(linhas[0]).toHaveTextContent("Chega em 4 min");
    expect(linhas[0].querySelector(".selo-fonte")).toHaveTextContent("ao vivo");

    // previsto: o horário em que passa AQUI, e o selo "previsto"
    expect(linhas[1]).toHaveTextContent("Previsto às 15:18 (em 18 min)");
    expect(linhas[1].querySelector(".selo-fonte")).toHaveTextContent("previsto");

    // sem dado: diz isso, sem inventar número
    expect(linhas[2]).toHaveTextContent("Sem previsão no momento");
    expect(linhas[2].querySelector(".selo-fonte")).toBeNull();
  });

  it("menos de 1 minuto não vira '0 min'", async () => {
    buscarChegadasParadaMock.mockResolvedValue({
      ...CHEGADAS_TESTE,
      chegadas: [{ ...CHEGADAS_TESTE.chegadas[0], etaMinutos: 0.3 }],
    });

    await abrirPainelDaParada();

    expect(await screen.findByText(/menos de 1 min/)).toBeInTheDocument();
    expect(screen.queryByText(/\b0 min\b/)).not.toBeInTheDocument();
  });

  it("sem chegadas da API (404/falha), o painel segue igual e sem a seção", async () => {
    buscarChegadasParadaMock.mockResolvedValue(null);

    await abrirPainelDaParada();

    await waitFor(() => expect(buscarChegadasParadaMock).toHaveBeenCalled());
    expect(screen.queryByText("Chegando nesta parada")).not.toBeInTheDocument();
    // o resto do painel continua lá
    expect(screen.getByText("06:20 · 06:40 · 07:00")).toBeInTheDocument();
  });

  it("parada com lista de chegadas vazia não mostra a seção", async () => {
    buscarChegadasParadaMock.mockResolvedValue({ ...CHEGADAS_TESTE, chegadas: [] });

    await abrirPainelDaParada();

    await waitFor(() => expect(buscarChegadasParadaMock).toHaveBeenCalled());
    expect(screen.queryByText("Chegando nesta parada")).not.toBeInTheDocument();
  });

  it("as saídas do terminal continuam rotuladas como saídas, ao lado das chegadas", async () => {
    buscarChegadasParadaMock.mockResolvedValue(CHEGADAS_TESTE);

    await abrirPainelDaParada();

    expect(await screen.findByText("Chegando nesta parada")).toBeInTheDocument();
    expect(screen.getByText("Próximas saídas do terminal")).toBeInTheDocument();
  });

  it("fechar o painel da parada para de buscar chegadas", async () => {
    buscarChegadasParadaMock.mockResolvedValue(CHEGADAS_TESTE);
    await abrirPainelDaParada();
    await screen.findByText("Chegando nesta parada");

    fireEvent.click(screen.getAllByTitle("Fechar")[0]);

    await waitFor(() => expect(screen.queryByText("Chegando nesta parada")).not.toBeInTheDocument());
  });


  it("fecha o painel de detalhes e volta ao painel da linha (cenário 3)", async () => {
    buscarDetalhesParadaMock.mockResolvedValue(DETALHE_PARADA_TESTE);

    render(<MapaInterativo linha={LINHA_TESTE} />);
    fireEvent.click(screen.getAllByTestId("marcador-mapa-icone-parada")[0]);

    await waitFor(() => {
      expect(screen.getByText("Parada PR-12345")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTitle("Fechar"));

    expect(screen.queryByText("Parada PR-12345")).not.toBeInTheDocument();
    expect(screen.getByText(LINHA_TESTE.nome)).toBeInTheDocument();
  });

  it("exibe aviso quando a busca de detalhes da parada falha", async () => {
    buscarDetalhesParadaMock.mockRejectedValue(
      new BuscarParadaError(
        "Não foi possível carregar os detalhes da parada. Tente novamente."
      )
    );

    render(<MapaInterativo linha={LINHA_TESTE} />);
    fireEvent.click(screen.getAllByTestId("marcador-mapa-icone-parada")[0]);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Não foi possível carregar os detalhes da parada. Tente novamente."
      );
    });
  });

  // -------------------------------------------------------------------
  // Issue #174 — resposta atrasada não sobrescreve o painel
  // -------------------------------------------------------------------

  const DETALHE_A: DetalhesParada = { ...DETALHE_PARADA_TESTE, codigo: "PR-AAAAA", nome: "Parada A" };
  const DETALHE_B: DetalhesParada = { ...DETALHE_PARADA_TESTE, codigo: "PR-BBBBB", nome: "Parada B" };

  function adiada<T>() {
    let resolver!: (valor: T) => void;
    let rejeitar!: (erro: unknown) => void;
    const promessa = new Promise<T>((resolve, reject) => {
      resolver = resolve;
      rejeitar = reject;
    });
    return { promessa, resolver, rejeitar };
  }

  it("clicar na parada A e logo na B: a resposta atrasada de A não sobrescreve a B", async () => {
    const a = adiada<DetalhesParada | null>();
    buscarDetalhesParadaMock
      .mockReturnValueOnce(a.promessa)
      .mockResolvedValueOnce(DETALHE_B);

    render(<MapaInterativo linha={LINHA_TESTE} />);
    const marcadores = screen.getAllByTestId("marcador-mapa-icone-parada");
    fireEvent.click(marcadores[0]);
    fireEvent.click(marcadores[1]);

    await screen.findByText("Parada PR-BBBBB");

    await act(async () => {
      a.resolver(DETALHE_A);
      await a.promessa;
    });

    expect(screen.getByText("Parada PR-BBBBB")).toBeInTheDocument();
    expect(screen.queryByText("Parada PR-AAAAA")).not.toBeInTheDocument();
  });

  it("o erro atrasado de A também não derruba o painel da B", async () => {
    const a = adiada<DetalhesParada | null>();
    buscarDetalhesParadaMock
      .mockReturnValueOnce(a.promessa)
      .mockResolvedValueOnce(DETALHE_B);

    render(<MapaInterativo linha={LINHA_TESTE} />);
    const marcadores = screen.getAllByTestId("marcador-mapa-icone-parada");
    fireEvent.click(marcadores[0]);
    fireEvent.click(marcadores[1]);
    await screen.findByText("Parada PR-BBBBB");

    await act(async () => {
      a.rejeitar(new BuscarParadaError("Falha antiga de A"));
      await a.promessa.catch(() => undefined);
    });

    expect(screen.getByText("Parada PR-BBBBB")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("fechar o painel antes da resposta chegar: ela não reabre o painel", async () => {
    const a = adiada<DetalhesParada | null>();
    buscarDetalhesParadaMock.mockReturnValueOnce(a.promessa);

    render(<MapaInterativo linha={LINHA_TESTE} />);
    fireEvent.click(screen.getAllByTestId("marcador-mapa-icone-parada")[0]);
    fireEvent.click(screen.getByTitle("Fechar"));

    await act(async () => {
      a.resolver(DETALHE_A);
      await a.promessa;
    });

    expect(screen.queryByText("Parada PR-AAAAA")).not.toBeInTheDocument();
    expect(screen.getByText(LINHA_TESTE.nome)).toBeInTheDocument();
  });

  it("clicar de novo depois de fechar continua funcionando", async () => {
    buscarDetalhesParadaMock.mockResolvedValue(DETALHE_B);

    render(<MapaInterativo linha={LINHA_TESTE} />);
    const marcadores = screen.getAllByTestId("marcador-mapa-icone-parada");
    fireEvent.click(marcadores[0]);
    await screen.findByText("Parada PR-BBBBB");
    fireEvent.click(screen.getByTitle("Fechar"));
    fireEvent.click(marcadores[1]);

    expect(await screen.findByText("Parada PR-BBBBB")).toBeInTheDocument();
  });

  // -------------------------------------------------------------------
  // Issue #174 — horários por linha
  // -------------------------------------------------------------------

  it("mostra as próximas saídas de cada linha, e não três no total", async () => {
    buscarDetalhesParadaMock.mockResolvedValue({
      ...DETALHE_PARADA_TESTE,
      linhas: [
        { numero: "0.110", nome: "Taguatinga", sentido: "ida", proximosHorarios: ["06:20", "06:40", "07:00"] },
        { numero: "0.220", nome: "Ceilândia", sentido: "ida", proximosHorarios: ["06:30"] },
        { numero: "0.330", nome: "Samambaia", sentido: "ida", proximosHorarios: [] },
      ],
    });

    render(<MapaInterativo linha={LINHA_TESTE} />);
    fireEvent.click(screen.getAllByTestId("marcador-mapa-icone-parada")[0]);

    expect(await screen.findByText("06:20 · 06:40 · 07:00")).toBeInTheDocument();
    expect(screen.getByText("06:30")).toBeInTheDocument();
    expect(screen.getByText("sem saída prevista hoje")).toBeInTheDocument();
  });

  it("nenhuma linha com saída hoje: mostra o aviso de sem saída prevista", async () => {
    buscarDetalhesParadaMock.mockResolvedValue({
      ...DETALHE_PARADA_TESTE,
      linhas: [{ numero: "0.110", nome: "Taguatinga", sentido: "ida", proximosHorarios: [] }],
      proximosHorarios: [],
    });

    render(<MapaInterativo linha={LINHA_TESTE} />);
    fireEvent.click(screen.getAllByTestId("marcador-mapa-icone-parada")[0]);

    expect(
      await screen.findByText("Nenhuma saída prevista disponível para esta parada no momento.")
    ).toBeInTheDocument();
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
  etaMinutos: null,
};

describe("MapaInterativo — rastreamento ao vivo (US #16)", () => {
  beforeEach(() => {
    mockGeolocation({
      getCurrentPosition: jest.fn() as unknown as Geolocation["getCurrentPosition"],
    });
    buscarPosicoesMock.mockReset().mockResolvedValue(resultadoPosicoes([]));
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("cenário 1: desenha um marcador por ônibus em operação", async () => {
    buscarPosicoesMock.mockResolvedValue(
      resultadoPosicoes([
        VEICULO,
        { ...VEICULO, prefixo: "446149", lat: -15.81 },
      ])
    );

    render(<MapaInterativo linha={LINHA_TESTE} />);

    await waitFor(() => {
      expect(screen.getAllByTestId("marcador-mapa-icone-onibus")).toHaveLength(2);
    });
    expect(buscarPosicoesMock).toHaveBeenCalledWith(LINHA_TESTE.numero, null);
  });

  it("issue #132: o marcador é uma pílula com o número da linha", async () => {
    buscarPosicoesMock.mockResolvedValue(resultadoPosicoes([VEICULO]));

    render(<MapaInterativo linha={LINHA_TESTE} />);

    const marcador = await screen.findByTestId("marcador-mapa-icone-onibus");
    const html = marcador.getAttribute("data-html") ?? "";

    expect(html).toContain("mapa-onibus-pilula");
    expect(html).toContain("mapa-onibus-glifo");
    expect(html).toContain(">0.110<");
  });

  it("issue #132: sem tempo estimado, a pílula não mostra separador nem minutos", async () => {
    buscarPosicoesMock.mockResolvedValue(resultadoPosicoes([VEICULO]));

    render(<MapaInterativo linha={LINHA_TESTE} />);

    const marcador = await screen.findByTestId("marcador-mapa-icone-onibus");
    const html = marcador.getAttribute("data-html") ?? "";

    // Sem localização do usuário (geolocalização não resolvida no
    // beforeEach), o backend não calcula eta_minutos — a pílula não
    // pode inventar um tempo aproximado.
    expect(html).not.toContain("·");
    expect(html).not.toContain("min<");
  });

  it("cenário 4, US #19: com etaMinutos, a pílula mostra o tempo estimado", async () => {
    buscarPosicoesMock.mockResolvedValue(
      resultadoPosicoes([{ ...VEICULO, etaMinutos: 4 }])
    );

    render(<MapaInterativo linha={LINHA_TESTE} />);

    const marcador = await screen.findByTestId("marcador-mapa-icone-onibus");
    const html = marcador.getAttribute("data-html") ?? "";

    expect(html).toContain(">0.110 · 4 min<");
  });

  it("cenário 2: atualiza sozinho, sem recarregar a página", async () => {
    jest.useFakeTimers();
    buscarPosicoesMock.mockResolvedValue(resultadoPosicoes([VEICULO]));

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
    buscarPosicoesMock.mockResolvedValue(resultadoPosicoes([]));

    render(<MapaInterativo linha={LINHA_TESTE} />);

    await waitFor(() => {
      expect(
        screen.getByText(/Nenhum ônibus desta linha em operação no momento/)
      ).toBeInTheDocument();
    });
    expect(screen.queryByTestId("marcador-mapa-icone-onibus")).not.toBeInTheDocument();
  });

  it("cenário 3, US #19: com localização do usuário, mostra o horário previsto", async () => {
    mockGeolocation({
      getCurrentPosition: jest.fn((sucesso) =>
        sucesso({
          coords: { latitude: -15.83, longitude: -48.04 },
        } as GeolocationPosition)
      ) as unknown as Geolocation["getCurrentPosition"],
    });
    buscarPosicoesMock.mockResolvedValue(resultadoPosicoes([], "06:20"));

    render(<MapaInterativo linha={LINHA_TESTE} />);

    await waitFor(() => {
      expect(
        screen.getByText(/Próxima saída prevista do terminal: 06:20/)
      ).toBeInTheDocument();
    });
  });

  it("para de consultar ao fechar a linha, sem vazar o intervalo", async () => {
    jest.useFakeTimers();
    buscarPosicoesMock.mockResolvedValue(resultadoPosicoes([VEICULO]));

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
    buscarPosicoesMock.mockReset().mockResolvedValue(resultadoPosicoes([]));
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("rastreia todas as linhas do itinerário, não só uma", async () => {
    // Sem isso, quem planejava "Taguatinga → UCB" via a linha no
    // resultado e não tinha como ver onde o ônibus estava — precisava
    // buscar a linha pelo número numa segunda busca.
    buscarPosicoesMock.mockResolvedValue(resultadoPosicoes([]));

    render(<MapaInterativo viagem={VIAGEM_COM_BALDEACAO} />);

    await waitFor(() => {
      expect(buscarPosicoesMock).toHaveBeenCalledTimes(2);
    });
    expect(buscarPosicoesMock).toHaveBeenCalledWith("0.186", null);
    expect(buscarPosicoesMock).toHaveBeenCalledWith("0.110", null);
  });

  it("desenha os ônibus das duas pernas no mapa", async () => {
    buscarPosicoesMock
      .mockResolvedValueOnce(
        resultadoPosicoes([{ ...VEICULO, linha: "0.186", prefixo: "A1" }])
      )
      .mockResolvedValueOnce(
        resultadoPosicoes([{ ...VEICULO, linha: "0.110", prefixo: "B1" }])
      );

    render(<MapaInterativo viagem={VIAGEM_COM_BALDEACAO} />);

    await waitFor(() => {
      expect(screen.getAllByTestId("marcador-mapa-icone-onibus")).toHaveLength(2);
    });
  });

  it("repassa os ônibus rastreados para quem desenha o painel", async () => {
    const onVeiculos = jest.fn();
    buscarPosicoesMock.mockResolvedValue(
      resultadoPosicoes([{ ...VEICULO, linha: "0.186", prefixo: "A1" }])
    );

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
    buscarPosicoesMock.mockReset().mockResolvedValue(resultadoPosicoes([]));
  });

  it("aponta a seta na direção que o ônibus está indo", async () => {
    // O feed traz `direcao` em graus e a gente ignorava. Sem ela o
    // ônibus é um ponto sem orientação no mapa.
    buscarPosicoesMock.mockResolvedValue(
      resultadoPosicoes([{ ...VEICULO, velocidade: 41, direcao: 218.72 }])
    );

    render(<MapaInterativo linha={LINHA_TESTE} />);

    await waitFor(() => {
      const marcador = screen.getByTestId("marcador-mapa-icone-onibus");
      expect(marcador.getAttribute("data-html")).toContain("rotate(218.72deg)");
    });
  });

  it("sem 'sentido' da API, popup mostra a direção cardeal calculada do rumo", async () => {
    // Achado de uso real: o feed da SEMOB nem sempre preenche `sentido`,
    // e o popup caía num "Em operação" genérico, sem dizer pra onde o
    // ônibus ia — mesmo a seta do ícone já sabendo a direção (`direcao`).
    buscarPosicoesMock.mockResolvedValue(
      resultadoPosicoes([{ ...VEICULO, sentido: null, velocidade: 41, direcao: 218.72 }])
    );

    render(<MapaInterativo linha={LINHA_TESTE} />);

    await waitFor(() => {
      expect(screen.getByText(/Indo pra sudoeste/)).toBeInTheDocument();
    });
  });

  it("ônibus parado sem 'sentido' não inventa direção (não está mais indo a lugar nenhum)", async () => {
    buscarPosicoesMock.mockResolvedValue(
      resultadoPosicoes([{ ...VEICULO, sentido: null, velocidade: 0, direcao: 218.72 }])
    );

    render(<MapaInterativo linha={LINHA_TESTE} />);

    await waitFor(() => {
      expect(screen.getByText(/Em operação/)).toBeInTheDocument();
    });
    expect(screen.queryByText(/Indo pra/)).not.toBeInTheDocument();
  });

  it("ônibus parado não ganha seta nem pulso", async () => {
    // Apontar rumo em quem está a 0 km/h mostraria a direção da última
    // vez que andou — informação errada apresentada como atual.
    buscarPosicoesMock.mockResolvedValue(
      resultadoPosicoes([{ ...VEICULO, velocidade: 0, direcao: 218.72 }])
    );

    render(<MapaInterativo linha={LINHA_TESTE} />);

    await waitFor(() => {
      const marcador = screen.getByTestId("marcador-mapa-icone-onibus parado");
      expect(marcador.getAttribute("data-html")).not.toContain("seta");
    });
  });

  it("velocidade abaixo do limiar conta como parado", async () => {
    buscarPosicoesMock.mockResolvedValue(
      resultadoPosicoes([{ ...VEICULO, velocidade: 1.2, direcao: 90 }])
    );

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
    buscarPosicoesMock.mockResolvedValue(
      resultadoPosicoes([
        { ...VEICULO, velocidade: 30, atualizadoEm: haQuarentaSegundos },
      ])
    );

    render(<MapaInterativo linha={LINHA_TESTE} />);

    await waitFor(() => {
      expect(screen.getByText(/Posição de 4\ds atrás/)).toBeInTheDocument();
    });
  });

  it("desliga a transição durante o zoom, pra frota não sair escorregando", async () => {
    buscarPosicoesMock.mockResolvedValue(resultadoPosicoes([VEICULO]));
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
  // ---------------------------------------------------------------------
  // Card #179 (⑤b) — pílula e popup do ônibus
  // ---------------------------------------------------------------------

  it("a pílula mostra minutos inteiros, e não '4.3 min'", async () => {
    buscarPosicoesMock.mockResolvedValue(resultadoPosicoes([{ ...VEICULO, etaMinutos: 4.3 }]));

    render(<MapaInterativo linha={LINHA_TESTE} />);

    const marcador = await screen.findByTestId("marcador-mapa-icone-onibus");
    expect(marcador.getAttribute("data-html")).toContain(">0.110 · 4 min<");
  });

  it("menos de 1 minuto na pílula vira '<1 min'", async () => {
    buscarPosicoesMock.mockResolvedValue(resultadoPosicoes([{ ...VEICULO, etaMinutos: 0.4 }]));

    render(<MapaInterativo linha={LINHA_TESTE} />);

    const marcador = await screen.findByTestId("marcador-mapa-icone-onibus");
    expect(marcador.getAttribute("data-html")).toContain(">0.110 · <1 min<");
  });

  it("o popup do ônibus diz até QUAL parada o tempo foi medido", async () => {
    buscarPosicoesMock.mockResolvedValue(
      resultadoPosicoes([
        { ...VEICULO, etaMinutos: 4.3, paradaCodigo: "PR-12345", paradaNome: "W3 Sul — 502" },
      ])
    );

    render(<MapaInterativo linha={LINHA_TESTE} />);

    const popup = await screen.findByTestId("popup");
    expect(popup).toHaveTextContent("Chega na parada W3 Sul — 502 em 4 min");
  });

  it("sem parada de referência (projeção no traçado), o popup não afirma nenhuma", async () => {
    buscarPosicoesMock.mockResolvedValue(resultadoPosicoes([{ ...VEICULO, etaMinutos: 4 }]));

    render(<MapaInterativo linha={LINHA_TESTE} />);

    const popup = await screen.findByTestId("popup");
    expect(popup).not.toHaveTextContent(/Chega na parada/);
  });

  // ---------------------------------------------------------------------
  // Issue #190 — "quanto falta para ESTE ônibus chegar até mim"
  // ---------------------------------------------------------------------

  function comLocalizacao() {
    mockGeolocation({
      getCurrentPosition: jest.fn((sucesso) =>
        sucesso({
          coords: { latitude: -15.83, longitude: -48.04 },
        } as GeolocationPosition)
      ) as unknown as Geolocation["getCurrentPosition"],
    });
  }

  it("o tempo do popup declara a origem: 'ao vivo'", async () => {
    buscarPosicoesMock.mockResolvedValue(
      resultadoPosicoes([
        { ...VEICULO, etaMinutos: 4.3, paradaCodigo: "PR-12345", paradaNome: "W3 Sul — 502" },
      ])
    );

    render(<MapaInterativo linha={LINHA_TESTE} />);

    const popup = await screen.findByTestId("popup");
    expect(popup).toHaveTextContent("Chega na parada W3 Sul — 502 em 4 min");
    expect(popup).toHaveTextContent("ao vivo");
  });

  it("parada sem nome cadastrado: diz 'sua parada' em vez de calar", async () => {
    buscarPosicoesMock.mockResolvedValue(
      resultadoPosicoes([
        { ...VEICULO, etaMinutos: 4.3, paradaCodigo: "PR-12345", paradaNome: null },
      ])
    );

    render(<MapaInterativo linha={LINHA_TESTE} />);

    const popup = await screen.findByTestId("popup");
    expect(popup).toHaveTextContent("Chega na sua parada em 4 min");
    expect(popup).toHaveTextContent("ao vivo");
  });

  it("com localização e sem tempo, o popup diz 'Sem previsão no momento'", async () => {
    comLocalizacao();
    buscarPosicoesMock.mockResolvedValue(resultadoPosicoes([{ ...VEICULO, etaMinutos: null }]));

    render(<MapaInterativo linha={LINHA_TESTE} />);

    const popup = await screen.findByTestId("popup");
    await waitFor(() => expect(popup).toHaveTextContent("Sem previsão no momento"));
    expect(popup).not.toHaveTextContent(/Chega na/);
    expect(popup).not.toHaveTextContent("ao vivo");
  });

  it("sem localização, o popup não afirma 'Sem previsão' (não sabemos onde o usuário está)", async () => {
    buscarPosicoesMock.mockResolvedValue(resultadoPosicoes([{ ...VEICULO, etaMinutos: null }]));

    render(<MapaInterativo linha={LINHA_TESTE} />);

    const popup = await screen.findByTestId("popup");
    expect(popup).not.toHaveTextContent("Sem previsão no momento");
  });

  it("o tempo do popup atualiza sozinho a cada 20 s", async () => {
    jest.useFakeTimers();
    comLocalizacao();
    buscarPosicoesMock
      .mockResolvedValueOnce(
        resultadoPosicoes([
          { ...VEICULO, etaMinutos: 6, paradaCodigo: "PR-12345", paradaNome: "W3 Sul — 502" },
        ])
      )
      .mockResolvedValue(
        resultadoPosicoes([
          { ...VEICULO, etaMinutos: 4, paradaCodigo: "PR-12345", paradaNome: "W3 Sul — 502" },
        ])
      );

    render(<MapaInterativo linha={LINHA_TESTE} />);

    await act(async () => {});
    expect(screen.getByTestId("popup")).toHaveTextContent("em 6 min");

    await act(async () => {
      jest.advanceTimersByTime(20000);
    });
    expect(screen.getByTestId("popup")).toHaveTextContent("em 4 min");
    expect(screen.getByTestId("popup")).not.toHaveTextContent("em 6 min");
  });

});

// ---------------------------------------------------------------------------
// US #171 — Pegar o ônibus: o mapa em viagem × aguardando
// ---------------------------------------------------------------------------

describe("MapaInterativo — viagem em andamento (US #171)", () => {
  const buscarViagemMock = buscarViagemAtiva as jest.Mock;
  const embarcarMock = embarcarNoOnibus as jest.Mock;

  const POSICAO = { latitude: -15.83, longitude: -48.04 };

  function viagemEmCurso(sobre: Partial<ViagemAtiva> = {}): ViagemAtiva {
    return {
      id: "v-1",
      numeroLinha: "0.110",
      sentido: "IDA",
      veiculoPrefixo: VEICULO.prefixo,
      paradaDestinoCodigo: null,
      embarcouEm: "2026-10-14T15:00:00Z",
      sinal: "ao_vivo",
      veiculo: null,
      destino: null,
      proximaParada: { codigo: "PR-B", nome: "W3 Sul 502", lat: -15.8, lng: -47.9 },
      paradasRestantes: [],
      ...sobre,
    };
  }

  function comProvider(props: React.ComponentProps<typeof MapaInterativo> = {}) {
    return render(
      <ViagemProvider>
        <MapaInterativo {...props} />
      </ViagemProvider>
    );
  }

  beforeEach(() => {
    mockGeolocation({
      getCurrentPosition: jest.fn((sucesso) =>
        sucesso({ coords: POSICAO } as GeolocationPosition)
      ) as unknown as Geolocation["getCurrentPosition"],
    });
    buscarPosicoesMock
      .mockReset()
      .mockResolvedValue(resultadoPosicoes([{ ...VEICULO, etaMinutos: 4.3, paradaNome: "W3 Sul — 502" }]));
    buscarViagemMock.mockReset().mockResolvedValue({ falhou: false, viagem: null });
    embarcarMock.mockReset();
    buscarDetalhesParadaMock.mockReset().mockResolvedValue(null);
    buscarChegadasParadaMock.mockReset().mockResolvedValue(null);
  });

  describe("aguardando (comportamento de sempre)", () => {
    it("não mostra a faixa de viagem", async () => {
      comProvider({ linha: LINHA_TESTE });
      await screen.findByTestId("marcador-mapa-icone-onibus");

      expect(screen.queryByRole("region", { name: "Viagem em andamento" })).not.toBeInTheDocument();
    });

    it("a pílula e o popup seguem mostrando o tempo de espera", async () => {
      comProvider({ linha: LINHA_TESTE });

      const marcador = await screen.findByTestId("marcador-mapa-icone-onibus");
      expect(marcador.getAttribute("data-html")).toContain(">0.110 · 4 min<");
      expect(screen.getByTestId("popup")).toHaveTextContent("Chega na parada W3 Sul — 502 em 4 min");
    });

    it("o popup do ônibus oferece 'Peguei este ônibus' quando há localização", async () => {
      comProvider({ linha: LINHA_TESTE });

      expect(await screen.findByRole("button", { name: "Peguei este ônibus" })).toBeInTheDocument();
    });

    it("sem localização, o popup explica em vez de oferecer o botão", async () => {
      mockGeolocation({
        getCurrentPosition: jest.fn() as unknown as Geolocation["getCurrentPosition"],
      });

      comProvider({ linha: LINHA_TESTE });

      expect(await screen.findByText(/Ative a localização/)).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "Peguei este ônibus" })).not.toBeInTheDocument();
    });
  });

  describe("embarcar pelo popup (Cenário 1)", () => {
    it("manda a linha do ônibus tocado e a posição do usuário; depois a faixa aparece", async () => {
      buscarViagemMock
        .mockResolvedValueOnce({ falhou: false, viagem: null })
        .mockResolvedValue({ falhou: false, viagem: viagemEmCurso() });
      embarcarMock.mockResolvedValue(undefined);

      comProvider({ linha: LINHA_TESTE });
      fireEvent.click(await screen.findByRole("button", { name: "Peguei este ônibus" }));

      await waitFor(() =>
        expect(embarcarMock).toHaveBeenCalledWith({
          numeroLinha: "0.110",
          lat: POSICAO.latitude,
          lng: POSICAO.longitude,
        })
      );
      const faixa = await screen.findByRole("region", { name: "Viagem em andamento" });
      expect(faixa).toHaveTextContent("Em viagem · linha 0.110");
      expect(screen.getByText("Você está neste ônibus.")).toBeInTheDocument();
    });
  });

  describe("em viagem (RN-05)", () => {
    beforeEach(() => {
      buscarViagemMock.mockResolvedValue({ falhou: false, viagem: viagemEmCurso() });
    });

    it("mostra a faixa com a próxima parada", async () => {
      comProvider({ linha: LINHA_TESTE });

      const faixa = await screen.findByRole("region", { name: "Viagem em andamento" });
      expect(faixa).toHaveTextContent("Próxima parada: W3 Sul 502");
    });

    it("a pílula do ônibus deixa de mostrar o tempo de ESPERA", async () => {
      comProvider({ linha: LINHA_TESTE });
      await screen.findByRole("region", { name: "Viagem em andamento" });

      const marcador = await screen.findByTestId("marcador-mapa-icone-onibus");
      expect(marcador.getAttribute("data-html")).not.toContain("4 min");
      expect(marcador.getAttribute("data-html")).toContain("0.110");
    });

    it("o popup deixa de dizer quando o ônibus chega na parada", async () => {
      comProvider({ linha: LINHA_TESTE });
      await screen.findByRole("region", { name: "Viagem em andamento" });

      expect(screen.getByTestId("popup")).not.toHaveTextContent(/Chega na parada/);
    });

    it("o painel da parada esconde 'Chegando nesta parada' (já está a bordo)", async () => {
      buscarDetalhesParadaMock.mockResolvedValue({
        nome: "W3 Sul — 502",
        codigo: "PR-12345",
        lat: -15.8,
        lng: -47.9,
        linhas: [{ numero: "0.110", nome: "0.110", sentido: "IDA" }],
        proximosHorarios: [],
      });
      buscarChegadasParadaMock.mockResolvedValue({
        paradaCodigo: "PR-12345",
        paradaNome: "W3 Sul — 502",
        calculadoEm: "2026-10-14T15:00:00+00:00",
        chegadas: [
          {
            numero: "0.110",
            nome: "0.110",
            rotaSentido: "IDA",
            etaMinutos: 4,
            fonte: "ao_vivo",
            prefixo: "1",
            veiculosACaminho: 1,
            horarioPrevisto: null,
          },
        ],
      });

      comProvider({ linha: LINHA_TESTE });
      await screen.findByRole("region", { name: "Viagem em andamento" });
      fireEvent.click(screen.getAllByTestId("marcador-mapa-icone-parada")[0]);
      await screen.findByText("Parada PR-12345");

      expect(screen.queryByText("Chegando nesta parada")).not.toBeInTheDocument();
    });

    it("o painel de uma parada da linha oferece 'Descer nesta parada'", async () => {
      buscarDetalhesParadaMock.mockResolvedValue({
        nome: "W3 Sul — 502",
        codigo: "PR-12345",
        lat: -15.8,
        lng: -47.9,
        linhas: [{ numero: "0.110", nome: "0.110", sentido: "IDA" }],
        proximosHorarios: [],
      });

      comProvider({ linha: LINHA_TESTE });
      await screen.findByRole("region", { name: "Viagem em andamento" });
      fireEvent.click(screen.getAllByTestId("marcador-mapa-icone-parada")[0]);

      expect(await screen.findByRole("button", { name: "Descer nesta parada" })).toBeInTheDocument();
    });

    it("parada por onde a linha da viagem não passa: sem 'Descer nesta parada'", async () => {
      buscarDetalhesParadaMock.mockResolvedValue({
        nome: "Outra",
        codigo: "PR-99999",
        lat: -15.8,
        lng: -47.9,
        linhas: [{ numero: "875A", nome: "875A", sentido: "IDA" }],
        proximosHorarios: [],
      });

      comProvider({ linha: LINHA_TESTE });
      await screen.findByRole("region", { name: "Viagem em andamento" });
      fireEvent.click(screen.getAllByTestId("marcador-mapa-icone-parada")[0]);
      await screen.findByText("Parada PR-99999");

      expect(screen.queryByRole("button", { name: "Descer nesta parada" })).not.toBeInTheDocument();
    });
  });
});
