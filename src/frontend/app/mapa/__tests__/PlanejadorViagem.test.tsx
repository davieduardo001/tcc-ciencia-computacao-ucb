import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import PlanejadorViagem from "../PlanejadorViagem";

jest.mock("@/lib/api", () => ({
  buscarLugares: jest.fn().mockResolvedValue([]),
  nomearLugar: jest.fn().mockResolvedValue(null),
  salvarFavorito: jest.fn(),
  // SalvarFavoritoError precisa ser uma classe real para `instanceof` funcionar.
  SalvarFavoritoError: class SalvarFavoritoError extends Error {
    status?: number;
    constructor(message: string, status?: number) {
      super(message);
      this.status = status;
    }
  },
}));

// No jest com ts-jest, o import estático é hoisted ANTES do jest.mock(),
// então `salvarFavorito` importado via ES import seria undefined.
// O padrão seguro é acessar via require() após o mock ser registrado.
// eslint-disable-next-line @typescript-eslint/no-var-requires
const apiMock = require("@/lib/api");
const salvarFavoritoMock: jest.Mock = apiMock.salvarFavorito;
const SalvarFavoritoError: new (msg: string, status?: number) => Error = apiMock.SalvarFavoritoError;

const props = {
  origem: null,
  destino: null,
  onDefinir: jest.fn(),
  onInverter: jest.fn(),
  onBuscar: jest.fn(),
  onEscolherNoMapa: jest.fn(),
  escolhendoNoMapa: null,
  onUsarMinhaLocalizacao: jest.fn(),
  temLocalizacao: false,
  opcoes: null,
  opcaoSelecionada: null,
  onSelecionarOpcao: jest.fn(),
  calculando: false,
  erro: null,
  onFechar: jest.fn(),
  veiculosPorLinha: {},
  rastreando: false,
  // US #25
  favoritosIds: new Set<string>(),
  onFavoritoSalvo: jest.fn(),
};

/** Simula um arrasto vertical na alça, em pixels (negativo = para cima).
 *
 * Os eventos são construídos como MouseEvent de propósito: o jsdom não
 * implementa PointerEvent, e o `fireEvent.pointerDown` acaba criando um
 * Event genérico, sem `clientY` — o arrasto chegaria ao componente sem
 * coordenada nenhuma. Em navegador de verdade o PointerEvent carrega o
 * campo normalmente.
 */
function arrastar(alca: HTMLElement, dy: number) {
  fireEvent(
    alca,
    new MouseEvent("pointerdown", { clientY: 400, bubbles: true })
  );
  fireEvent(
    window,
    new MouseEvent("pointermove", { clientY: 400 + dy, bubbles: true })
  );
  fireEvent(
    window,
    new MouseEvent("pointerup", { clientY: 400 + dy, bubbles: true })
  );
}

describe("PlanejadorViagem — folha arrastável (issue #132)", () => {
  it("começa aberta", () => {
    const { container } = render(<PlanejadorViagem {...props} />);

    expect(container.querySelector(".plan-painel")).not.toHaveClass("recolhida");
    expect(screen.getByRole("button", { name: /Recolher opções/ })).toHaveAttribute(
      "aria-expanded",
      "true"
    );
  });

  it("alterna pelo botão da alça — arrastar não é acessível por teclado", () => {
    const { container } = render(<PlanejadorViagem {...props} />);
    const painel = container.querySelector(".plan-painel")!;

    fireEvent.click(screen.getByRole("button", { name: /Recolher opções/ }));
    expect(painel).toHaveClass("recolhida");

    fireEvent.click(screen.getByRole("button", { name: /Abrir opções/ }));
    expect(painel).not.toHaveClass("recolhida");
  });

  it("arrastar para baixo além do limiar recolhe a folha", () => {
    const { container } = render(<PlanejadorViagem {...props} />);
    const painel = container.querySelector(".plan-painel")!;

    arrastar(container.querySelector(".plan-alca") as HTMLElement, 120);

    expect(painel).toHaveClass("recolhida");
  });

  it("arrasto curto não muda o estado", () => {
    const { container } = render(<PlanejadorViagem {...props} />);
    const painel = container.querySelector(".plan-painel")!;

    arrastar(container.querySelector(".plan-alca") as HTMLElement, 20);

    expect(painel).not.toHaveClass("recolhida");
  });

  it("arrastar para cima reabre a folha recolhida", () => {
    const { container } = render(<PlanejadorViagem {...props} />);
    const painel = container.querySelector(".plan-painel")!;
    const alca = container.querySelector(".plan-alca") as HTMLElement;

    fireEvent.click(screen.getByRole("button", { name: /Recolher opções/ }));
    expect(painel).toHaveClass("recolhida");

    arrastar(alca, -120);

    expect(painel).not.toHaveClass("recolhida");
  });
});

function pernaMock(numero: string) {
  return {
    numero,
    sentido: "Sentido Teste",
    nome: "Linha Teste",
    embarque: { lat: 0, lng: 0, parada_nome: "Parada A", caminhada_metros: 50 },
    desembarque: { lat: 0, lng: 0, parada_nome: "Parada B", caminhada_metros: 50 },
    distancia_km: 5,
    paradas_no_trecho: 3,
    trajeto: [] as [number, number][],
  };
}

describe("PlanejadorViagem — resumo da opção de rota", () => {
  it("pluraliza 'baldeações' quando há mais de uma troca de linha", () => {
    render(
      <PlanejadorViagem
        {...props}
        opcoes={[
          {
            pernas: [pernaMock("0.110"), pernaMock("0.120"), pernaMock("0.130")],
            baldeacoes: 2,
            distancia_km: 10,
            caminhada_metros: 300,
            duracao_estimada_min: 40,
          },
        ]}
      />
    );

    expect(screen.getByText("2 baldeações")).toBeInTheDocument();
  });

  it("mantém 'baldeação' no singular quando há só uma troca", () => {
    render(
      <PlanejadorViagem
        {...props}
        opcoes={[
          {
            pernas: [pernaMock("0.110"), pernaMock("0.120")],
            baldeacoes: 1,
            distancia_km: 8,
            caminhada_metros: 200,
            duracao_estimada_min: 30,
          },
        ]}
      />
    );

    expect(screen.getByText("1 baldeação")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// US #25 — Botão de favorito no PlanejadorViagem
// ---------------------------------------------------------------------------

function pernaMockCompleta(numero: string) {
  return {
    numero,
    sentido: "IDA",
    nome: `${numero} — Linha Teste`,
    embarque: { lat: -15.83, lng: -48.04, parada_nome: "Parada A", caminhada_metros: 50 },
    desembarque: { lat: -15.79, lng: -47.88, parada_nome: "Parada B", caminhada_metros: 50 },
    distancia_km: 10,
    paradas_no_trecho: 5,
    trajeto: [[-15.83, -48.04], [-15.79, -47.88]] as [number, number][],
  };
}

const origemMock = { nome: "Terminal Ceilândia", lat: -15.8305, lng: -48.0425 };
const destinoMock = { nome: "Rodoviária", lat: -15.7939, lng: -47.8828 };
const opcaoMock = {
  pernas: [pernaMockCompleta("0.110")],
  baldeacoes: 0,
  distancia_km: 10,
  caminhada_metros: 100,
  duracao_estimada_min: 30,
};

describe("PlanejadorViagem — botão de favorito (US #25)", () => {
  beforeEach(() => {
    salvarFavoritoMock.mockReset();
  });

  it("botão 'Salvar como favorita' aparece quando a opção está expandida", () => {
    render(
      <PlanejadorViagem
        {...props}
        origem={origemMock}
        destino={destinoMock}
        opcoes={[opcaoMock]}
        opcaoSelecionada={0}
      />
    );

    expect(
      screen.getByRole("button", { name: /Salvar como favorita/i })
    ).toBeInTheDocument();
  });

  it("botão NÃO aparece quando nenhuma opção está selecionada", () => {
    render(
      <PlanejadorViagem
        {...props}
        origem={origemMock}
        destino={destinoMock}
        opcoes={[opcaoMock]}
        opcaoSelecionada={null}
      />
    );

    expect(
      screen.queryByRole("button", { name: /Salvar como favorita/i })
    ).not.toBeInTheDocument();
  });

  it("clicar no botão chama salvarFavorito com os dados da opção", async () => {
    const favoritoRetornado = {
      id: "uuid-novo",
      usuario_id: "uuid-user",
      numero_linha: "0.110",
      nome_linha: "0.110 — Linha Teste",
      label: "Terminal Ceilândia → Rodoviária",
      origem_lat: -15.8305,
      origem_lng: -48.0425,
      destino_lat: -15.7939,
      destino_lng: -47.8828,
      criado_em: "2026-10-05T14:30:00",
    };
    salvarFavoritoMock.mockResolvedValue(favoritoRetornado);
    const onFavoritoSalvo = jest.fn();

    render(
      <PlanejadorViagem
        {...props}
        origem={origemMock}
        destino={destinoMock}
        opcoes={[opcaoMock]}
        opcaoSelecionada={0}
        onFavoritoSalvo={onFavoritoSalvo}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: /Salvar como favorita/i }));

    await waitFor(() => {
      expect(salvarFavoritoMock).toHaveBeenCalledWith(
        expect.objectContaining({
          numero_linha: "0.110",
          origem_lat: -15.8305,
          destino_lat: -15.7939,
          label: "Terminal Ceilândia → Rodoviária",
        })
      );
      expect(onFavoritoSalvo).toHaveBeenCalledWith(favoritoRetornado);
    });
  });

  it("mostra estrela preenchida quando a opção já está nos favoritos", () => {
    // A chave lógica é: numero_linha:orig_lat,orig_lng:dest_lat,dest_lng
    const chaveJaSalva = new Set([
      "0.110:-15.8305,-48.0425:-15.7939,-47.8828",
    ]);

    render(
      <PlanejadorViagem
        {...props}
        origem={origemMock}
        destino={destinoMock}
        opcoes={[opcaoMock]}
        opcaoSelecionada={0}
        favoritosIds={chaveJaSalva}
      />
    );

    expect(
      screen.getByRole("button", { name: /Rota já salva nos favoritos/i })
    ).toBeInTheDocument();
    expect(
      screen.getByText("Salva nos favoritos")
    ).toBeInTheDocument();
  });

  it("mostra mensagem de erro quando salvar falha", async () => {
    salvarFavoritoMock.mockRejectedValue(
      new SalvarFavoritoError("Você atingiu o limite de 20 rotas favoritas.", 422)
    );

    render(
      <PlanejadorViagem
        {...props}
        origem={origemMock}
        destino={destinoMock}
        opcoes={[opcaoMock]}
        opcaoSelecionada={0}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: /Salvar como favorita/i }));

    await waitFor(() => {
      expect(
        screen.getByText("Você atingiu o limite de 20 rotas favoritas.")
      ).toBeInTheDocument();
    });
  });
});
