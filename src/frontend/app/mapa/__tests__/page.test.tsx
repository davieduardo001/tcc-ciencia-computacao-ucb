import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import MapaPage from "../page";
import {
  buscarLugares,
  calcularRotas,
  nomearLugar,
  sugerirLinhas,
} from "@/lib/api";

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
  // A página lê ?painel= pra abrir o planejador quando o usuário chega
  // pelo item "Rotas" da navegação.
  useSearchParams: () => new URLSearchParams(parametrosDaUrl),
}));

/** Query string simulada; os testes sobrescrevem quando precisam. */
let parametrosDaUrl = "";

// O mapa em si depende de Leaflet/DOM real. O dublê expõe um botão que
// simula "usuário permitiu a localização", pra testar o atalho de
// "minha localização" do planejador (US #20) sem mexer em Geolocation.
jest.mock("../MapaInterativo", () => ({
  __esModule: true,
  default: ({
    onLocalizacao,
    viagem,
  }: {
    onLocalizacao?: (c: { lat: number; lng: number } | null) => void;
    viagem?: { pernas: { numero: string }[] } | null;
  }) => (
    <div data-testid="mapa-interativo" data-viagem={viagem ? "sim" : "nao"}>
      <button
        type="button"
        onClick={() => onLocalizacao?.({ lat: -15.83, lng: -48.04 })}
      >
        simular-localizacao
      </button>
    </div>
  ),
}));

jest.mock("@/lib/api", () => ({
  sugerirLinhas: jest.fn(),
  buscarLinha: jest.fn(),
  buscarLugares: jest.fn().mockResolvedValue([]),
  nomearLugar: jest.fn().mockResolvedValue(null),
  calcularRotas: jest.fn().mockResolvedValue([]),
  buscarUsuarioAtual: jest.fn().mockResolvedValue(null),
  logoutUsuario: jest.fn().mockResolvedValue(undefined),
  BuscarLinhaError: class BuscarLinhaError extends Error {},
  CalcularRotaError: class CalcularRotaError extends Error {},
}));

const sugerirLinhasMock = sugerirLinhas as jest.Mock;
const buscarLugaresMock = buscarLugares as jest.Mock;
const calcularRotasMock = calcularRotas as jest.Mock;
const nomearLugarMock = nomearLugar as jest.Mock;
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

// ---------------------------------------------------------------------------
// US #20 — planejamento de viagem origem → destino
// ---------------------------------------------------------------------------

const LUGAR_ORIGEM = {
  nome: "Terminal Ceilândia",
  endereco: "Terminal Ceilândia, Ceilândia, DF",
  lat: -15.8195,
  lng: -48.1096,
};

const LUGAR_DESTINO = {
  nome: "Rodoviária do Plano Piloto",
  endereco: "Rodoviária do Plano Piloto, Brasília, DF",
  lat: -15.7939,
  lng: -47.8828,
};

const VIAGEM_DIRETA = {
  pernas: [
    {
      numero: "0.382",
      sentido: "IDA",
      nome: "0.382 — Ceilândia / Rodoviária",
      embarque: {
        lat: -15.819,
        lng: -48.109,
        parada_nome: "Avenida Hélio Prates, Ceilândia",
        caminhada_metros: 119,
      },
      desembarque: {
        lat: -15.794,
        lng: -47.883,
        parada_nome: "Eixo L Central, Setor Bancário Sul",
        caminhada_metros: 58,
      },
      distancia_km: 27,
      paradas_no_trecho: 33,
      trajeto: [
        [-15.819, -48.109],
        [-15.794, -47.883],
      ],
    },
  ],
  baldeacoes: 0,
  distancia_km: 27,
  caminhada_metros: 177,
  duracao_estimada_min: 76,
};

async function abrirPlanejador() {
  render(<MapaPage />);
  await act(async () => {
    fireEvent.click(screen.getByText("Para onde você vai?"));
  });
}

/** Preenche um dos campos escolhendo a primeira sugestão do autocomplete. */
async function escolherLugar(rotulo: string, lugar: typeof LUGAR_ORIGEM) {
  buscarLugaresMock.mockResolvedValueOnce([lugar]);

  const campo = screen.getByLabelText(rotulo);
  fireEvent.change(campo, { target: { value: lugar.nome.slice(0, 6) } });

  await act(async () => {
    jest.advanceTimersByTime(500);
  });

  await act(async () => {
    fireEvent.click(screen.getByText(lugar.endereco));
  });
}

describe("MapaPage — planejar viagem origem → destino (US #20)", () => {
  beforeEach(() => {
    buscarLugaresMock.mockReset().mockResolvedValue([]);
    calcularRotasMock.mockReset().mockResolvedValue([]);
    nomearLugarMock.mockReset().mockResolvedValue(null);
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("o botão de buscar só habilita com origem E destino definidos", async () => {
    await abrirPlanejador();

    const botao = screen.getByRole("button", { name: /ver opções de ônibus/i });
    expect(botao).toBeDisabled();

    await escolherLugar("De onde", LUGAR_ORIGEM);
    expect(botao).toBeDisabled();

    await escolherLugar("Para onde", LUGAR_DESTINO);
    expect(botao).toBeEnabled();
  });

  it("calcula a rota com as coordenadas dos dois pontos escolhidos", async () => {
    calcularRotasMock.mockResolvedValue([VIAGEM_DIRETA]);
    await abrirPlanejador();

    await escolherLugar("De onde", LUGAR_ORIGEM);
    await escolherLugar("Para onde", LUGAR_DESTINO);

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /ver opções de ônibus/i }));
    });

    expect(calcularRotasMock).toHaveBeenCalledWith(
      { nome: LUGAR_ORIGEM.nome, lat: LUGAR_ORIGEM.lat, lng: LUGAR_ORIGEM.lng },
      { nome: LUGAR_DESTINO.nome, lat: LUGAR_DESTINO.lat, lng: LUGAR_DESTINO.lng }
    );

    // A linha aparece duas vezes: no resumo da opção e no passo
    // expandido logo abaixo (a primeira opção abre já expandida).
    expect(screen.getAllByText("0.382")).toHaveLength(2);
    expect(screen.getByText("~76 min")).toBeInTheDocument();
    expect(screen.getByText(/Avenida Hélio Prates/)).toBeInTheDocument();
    expect(screen.getByText(/Eixo L Central/)).toBeInTheDocument();
    expect(screen.getByText(/33 paradas/)).toBeInTheDocument();
    // E o itinerário chega ao mapa.
    expect(screen.getByTestId("mapa-interativo")).toHaveAttribute(
      "data-viagem",
      "sim"
    );
  });

  it("mostra a mensagem do Cenário 3 quando não há rota possível", async () => {
    calcularRotasMock.mockResolvedValue([]);
    await abrirPlanejador();

    await escolherLugar("De onde", LUGAR_ORIGEM);
    await escolherLugar("Para onde", LUGAR_DESTINO);

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /ver opções de ônibus/i }));
    });

    expect(screen.getByText(/Nenhuma linha liga esses dois pontos/)).toBeInTheDocument();
  });

  it("inverter troca origem e destino de lugar", async () => {
    await abrirPlanejador();

    await escolherLugar("De onde", LUGAR_ORIGEM);
    await escolherLugar("Para onde", LUGAR_DESTINO);

    await act(async () => {
      fireEvent.click(screen.getByTitle("Inverter origem e destino"));
    });

    expect(screen.getByLabelText("De onde")).toHaveValue(LUGAR_DESTINO.nome);
    expect(screen.getByLabelText("Para onde")).toHaveValue(LUGAR_ORIGEM.nome);
  });

  it("'minha localização' só habilita quando o mapa reporta a posição", async () => {
    await abrirPlanejador();

    const atalhos = screen.getAllByText("Minha localização");
    expect(atalhos[0].closest("button")).toBeDisabled();

    await act(async () => {
      fireEvent.click(screen.getByText("simular-localizacao"));
    });

    expect(
      screen.getAllByText("Minha localização")[0].closest("button")
    ).toBeEnabled();
  });

  it("usar minha localização preenche a origem com a posição do mapa", async () => {
    nomearLugarMock.mockResolvedValue({
      nome: "QNM 18, Ceilândia",
      endereco: "QNM 18, Ceilândia, DF",
      lat: -15.83,
      lng: -48.04,
    });

    await abrirPlanejador();

    await act(async () => {
      fireEvent.click(screen.getByText("simular-localizacao"));
    });

    await act(async () => {
      fireEvent.click(screen.getAllByText("Minha localização")[0]);
    });

    await waitFor(() => {
      expect(screen.getByLabelText("De onde")).toHaveValue("QNM 18, Ceilândia");
    });
    expect(nomearLugarMock).toHaveBeenCalledWith(-15.83, -48.04);
  });

  it("não consulta o geocodificador com menos de 3 caracteres", async () => {
    await abrirPlanejador();

    fireEvent.change(screen.getByLabelText("De onde"), {
      target: { value: "ro" },
    });

    await act(async () => {
      jest.advanceTimersByTime(500);
    });

    expect(buscarLugaresMock).not.toHaveBeenCalled();
  });
});
