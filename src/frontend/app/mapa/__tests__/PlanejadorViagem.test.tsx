import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import PlanejadorViagem from "../PlanejadorViagem";
import { corDaLinha } from "../corDaLinha";

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

// ---------------------------------------------------------------------------
// Card #179 (④a) — rótulos legíveis e estados do resultado
// ---------------------------------------------------------------------------

function opcaoComParadas(embarqueNome: string, desembarqueNome: string) {
  const perna = pernaMockCompleta("0.110");
  perna.embarque.parada_nome = embarqueNome;
  perna.desembarque.parada_nome = desembarqueNome;
  return { ...opcaoMock, pernas: [perna] };
}

describe("PlanejadorViagem — rótulo de parada sem nome (card #179)", () => {
  it("parada sem nome na fonte vira 'Parada sem nome', e não coordenada crua", () => {
    render(
      <PlanejadorViagem
        {...props}
        origem={origemMock}
        destino={destinoMock}
        opcoes={[opcaoComParadas("", "")]}
        opcaoSelecionada={0}
      />
    );

    expect(screen.getAllByText("Parada sem nome")).toHaveLength(2);
    expect(screen.queryByText(/Ponto em/)).not.toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/-15.8300|-48.0400/);
  });

  it("a coordenada continua disponível no title, pra quem precisar conferir", () => {
    render(
      <PlanejadorViagem
        {...props}
        origem={origemMock}
        destino={destinoMock}
        opcoes={[opcaoComParadas("", "Parada B")]}
        opcaoSelecionada={0}
      />
    );

    expect(screen.getByText("Parada sem nome")).toHaveAttribute("title", "-15.83000, -48.04000");
  });

  it("parada com nome mostra o nome, sem title", () => {
    render(
      <PlanejadorViagem
        {...props}
        origem={origemMock}
        destino={destinoMock}
        opcoes={[opcaoComParadas("W3 Sul 502", "Rodoviária")]}
        opcaoSelecionada={0}
      />
    );

    expect(screen.getByText("W3 Sul 502")).not.toHaveAttribute("title");
    expect(screen.queryByText("Parada sem nome")).not.toBeInTheDocument();
  });
});

describe("PlanejadorViagem — ônibus rodando agora (card #179)", () => {
  it("'ônibus' é invariável: 1 e N usam o mesmo texto", () => {
    const { rerender } = render(
      <PlanejadorViagem
        {...props}
        origem={origemMock}
        destino={destinoMock}
        opcoes={[opcaoMock]}
        opcaoSelecionada={0}
        veiculosPorLinha={{ "0.110": 1 }}
        rastreando
      />
    );
    expect(screen.getByText(/ônibus rodando agora/)).toHaveTextContent("1 ônibus rodando agora");

    rerender(
      <PlanejadorViagem
        {...props}
        origem={origemMock}
        destino={destinoMock}
        opcoes={[opcaoMock]}
        opcaoSelecionada={0}
        veiculosPorLinha={{ "0.110": 4 }}
        rastreando
      />
    );
    expect(screen.getByText(/ônibus rodando agora/)).toHaveTextContent("4 ônibus rodando agora");
  });
});

describe("PlanejadorViagem — favorito dentro do cartão selecionado (card #179)", () => {
  it("o botão de favorito vive numa área própria colada ao cartão, com o estado 'salvo' legível", () => {
    const { container } = render(
      <PlanejadorViagem
        {...props}
        origem={origemMock}
        destino={destinoMock}
        opcoes={[opcaoMock]}
        opcaoSelecionada={0}
        favoritosIds={new Set(["0.110:-15.8305,-48.0425:-15.7939,-47.8828"])}
      />
    );

    const area = container.querySelector(".plan-favorito-area");
    expect(area).not.toBeNull();
    // o rodapé do favorito fica DENTRO do cartão selecionado (o <li>)
    expect(area!.closest("li")).toHaveClass("plan-opcao-card", "selecionada");
    expect(screen.getByRole("button", { name: /Rota já salva nos favoritos/ })).toHaveClass("salvo");
  });
});

// ---------------------------------------------------------------------------
// Card #179 (④b) — resultado de rota: cartão, linha do tempo, estados e teclado
// ---------------------------------------------------------------------------

function pernaViva(numero: string, extra: Record<string, unknown> = {}) {
  return {
    ...pernaMockCompleta(numero),
    espera_min: 6,
    fonte_espera: "tempo_real" as const,
    prefixo_veiculo: "B27431",
    ...extra,
  };
}

const opcaoViva = {
  pernas: [pernaViva("875A")],
  baldeacoes: 0,
  distancia_km: 12.4,
  caminhada_metros: 400,
  duracao_estimada_min: 46,
  duracao_real_min: 41,
  tipo_estimativa: "tempo_real" as const,
};

const opcaoComBaldeacao = {
  pernas: [
    {
      ...pernaMockCompleta("0.110"),
      embarque: { lat: 0, lng: 0, parada_nome: "Terminal", caminhada_metros: 60 },
      desembarque: { lat: 0, lng: 0, parada_nome: "X", caminhada_metros: 90 },
    },
    {
      ...pernaMockCompleta("106.2"),
      embarque: { lat: 0, lng: 0, parada_nome: "EQS 410", caminhada_metros: 150 },
      desembarque: { lat: 0, lng: 0, parada_nome: "Rodoviária", caminhada_metros: 40 },
    },
  ],
  baldeacoes: 1,
  distancia_km: 13,
  caminhada_metros: 340,
  duracao_estimada_min: 52,
};

function renderizar(parcial: Record<string, unknown> = {}) {
  return render(
    <PlanejadorViagem
      {...props}
      origem={origemMock}
      destino={destinoMock}
      opcoes={[opcaoViva]}
      opcaoSelecionada={0}
      rastreando
      {...parcial}
    />
  );
}

describe("PlanejadorViagem — cartão da opção (card #179)", () => {
  it("o badge da linha leva a mesma cor do traçado dela no mapa", () => {
    const { container } = renderizar();

    const badge = container.querySelector(".plan-opcao .plan-badge-linha") as HTMLElement;
    expect(badge).toHaveTextContent("875A");
    expect(badge.style.getPropertyValue("--cor-linha")).toBe(corDaLinha("875A"));
  });

  it("duração em destaque, sem o til, com o selo de origem do dado ao lado", () => {
    const { container } = renderizar();

    expect(screen.getByText("41 min")).toBeInTheDocument();
    expect(screen.queryByText(/~/)).not.toBeInTheDocument();
    expect(container.querySelector(".plan-opcao-selo-ao-vivo")).toHaveTextContent("ao vivo");
  });

  it("mostra a caminhada em minutos (e os metros como detalhe)", () => {
    renderizar();

    expect(screen.getByText("5 min a pé")).toBeInTheDocument();
    expect(screen.getByText("400 m")).toBeInTheDocument();
  });

  it("destaca a opção mais rápida, a de menos baldeações e a de menos caminhada", () => {
    renderizar({ opcoes: [opcaoViva, opcaoComBaldeacao], opcaoSelecionada: null });

    // viva: 41 min (mais rápida), 0 baldeações; a outra caminha 340 m (4 min) contra 400 m (5 min)
    expect(screen.getByText("Mais rápida")).toBeInTheDocument();
    expect(screen.getByText("Menos baldeações")).toBeInTheDocument();
    expect(screen.getByText("Menos caminhada")).toBeInTheDocument();
  });

  it("opção única não ganha destaque (não há com o que comparar)", () => {
    renderizar({ opcaoSelecionada: null });

    expect(screen.queryByText("Mais rápida")).not.toBeInTheDocument();
  });

  it("o <button> da opção só contém texto/inline; os passos ficam num irmão ligado por aria-controls", () => {
    const { container } = renderizar();

    const botao = container.querySelector("button.plan-opcao") as HTMLElement;
    expect(botao.querySelector("div, ol, ul, p, li")).toBeNull();

    const idDetalhe = botao.getAttribute("aria-controls")!;
    const detalhe = container.querySelector(`[id="${idDetalhe}"]`) as HTMLElement;
    expect(detalhe).toHaveAttribute("role", "group");
    expect(detalhe).toHaveAttribute("aria-label", "Passos da opção 1");
    expect(botao).toHaveAttribute("aria-expanded", "true");
  });

  it("opção fechada não referencia um detalhe que não existe", () => {
    const { container } = renderizar({ opcaoSelecionada: null });

    const botao = container.querySelector("button.plan-opcao") as HTMLElement;
    expect(botao).toHaveAttribute("aria-expanded", "false");
    expect(botao).not.toHaveAttribute("aria-controls");
  });
});

describe("PlanejadorViagem — linha do tempo (card #179)", () => {
  const TIPOS_DE_PASSO = ["caminhar", "embarcar", "viajar", "descer", "baldear"];

  it("renderiza os passos na ordem da viagem, cada um com seu marcador", () => {
    const { container } = renderizar();

    const tipos = [...container.querySelectorAll(".plan-tempo-passo")].map((li) =>
      [...li.classList].find((c) => TIPOS_DE_PASSO.includes(c))
    );
    expect(tipos).toEqual(["caminhar", "embarcar", "viajar", "descer", "caminhar"]);
  });

  it("destaca 'Chega em X min' num bloco próprio, com o carro", () => {
    const { container } = renderizar();

    const chegada = container.querySelector(".plan-chegada.ao-vivo") as HTMLElement;
    expect(chegada).toHaveTextContent("Chega em 6 min (carro B27431)");
  });

  it("numera o embarque como o marcador do mapa", () => {
    const { container } = renderizar({ opcoes: [opcaoComBaldeacao] });

    const numeros = [
      ...container.querySelectorAll(".plan-tempo-passo.embarcar .plan-tempo-marcador"),
    ].map((e) => e.textContent);
    expect(numeros).toEqual(["1", "2"]);
  });

  it("baldeação é um passo explícito, somando a caminhada das duas pontas", () => {
    const { container } = renderizar({ opcoes: [opcaoComBaldeacao] });

    const baldeacao = container.querySelector(".plan-tempo-passo.baldear") as HTMLElement;
    // 90 m (desembarque) + 150 m (embarque) = 240 m, a 5 km/h = 3 min
    expect(baldeacao).toHaveTextContent("Baldeação: caminhe 3 min (240 m) e pegue a linha 106.2");
  });

  it("caminhada inicial e final aparecem como passos próprios", () => {
    renderizar({ opcoes: [opcaoComBaldeacao] });

    expect(screen.getByText(/até o embarque/)).toBeInTheDocument();
    expect(screen.getByText(/até o destino/)).toBeInTheDocument();
  });

  it("sem espera calculada nem ônibus rastreado, diz isso sem inventar número", () => {
    renderizar({
      opcoes: [{ ...opcaoViva, pernas: [pernaMockCompleta("875A")] }],
      rastreando: true,
      veiculosPorLinha: {},
    });

    expect(
      screen.getByText(/Nenhum ônibus desta linha reportando posição agora/)
    ).toBeInTheDocument();
  });

  it("intervalo médio é rotulado como média, não como chegada", () => {
    renderizar({
      opcoes: [
        {
          ...opcaoViva,
          pernas: [
            pernaViva("875A", {
              fonte_espera: "intervalo_medio",
              intervalo_medio_min: 16,
              espera_min: 8,
              prefixo_veiculo: null,
            }),
          ],
        },
      ],
    });

    expect(screen.getByText(/Passa a cada ~/)).toBeInTheDocument();
    expect(screen.queryByText(/Chega em/)).not.toBeInTheDocument();
  });
});

describe("PlanejadorViagem — estados do resultado (card #179)", () => {
  it("carregando: mostra o esqueleto e anuncia para leitor de tela", () => {
    const { container } = renderizar({ opcoes: null, calculando: true });

    expect(container.querySelector(".plan-esqueletos")).not.toBeNull();
    expect(screen.getByRole("status")).toHaveTextContent("Calculando rotas...");
  });

  it("anuncia quantas opções encontrou", () => {
    renderizar({ opcoes: [opcaoViva, opcaoComBaldeacao], opcaoSelecionada: null });

    expect(screen.getByRole("status")).toHaveTextContent("2 opções encontradas.");
  });

  it("vazio: explica e oferece escolher outro destino", () => {
    const onDefinir = jest.fn();
    renderizar({ opcoes: [], opcaoSelecionada: null, onDefinir });

    expect(screen.getByText(/Nenhuma linha liga esses dois pontos/)).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Nenhuma opção encontrada.");

    fireEvent.click(screen.getByRole("button", { name: "Escolher outro destino" }));
    expect(onDefinir).toHaveBeenCalledWith("destino", null);
  });

  it("erro: mostra a mensagem e deixa tentar de novo", () => {
    const onBuscar = jest.fn();
    renderizar({
      opcoes: null,
      erro: "Não foi possível calcular a rota. Tente novamente.",
      onBuscar,
    });

    expect(screen.getByRole("alert")).toHaveTextContent("Não foi possível calcular a rota");
    fireEvent.click(screen.getByRole("button", { name: /Tentar de novo/ }));
    expect(onBuscar).toHaveBeenCalledTimes(1);
  });

  it("erro sem origem/destino preenchidos não oferece 'tentar de novo' (não há o que repetir)", () => {
    renderizar({ opcoes: null, erro: "Falhou", origem: null, destino: null });

    expect(screen.queryByRole("button", { name: /Tentar de novo/ })).not.toBeInTheDocument();
  });
});

describe("PlanejadorViagem — formulário recolhido no mobile (card #179)", () => {
  it("com resultado, aparece o resumo 'Origem → Destino' e o botão Editar", () => {
    const { container } = renderizar();

    const resumo = container.querySelector(".plan-resumo-rota") as HTMLElement;
    expect(resumo).toHaveTextContent("Terminal Ceilândia");
    expect(resumo).toHaveTextContent("Rodoviária");
    expect(screen.getByRole("button", { name: /Editar/ })).toHaveAttribute(
      "aria-expanded",
      "false"
    );
  });

  it("Editar alterna o modo de edição do painel", () => {
    const { container } = renderizar();
    const painel = container.querySelector(".plan-painel")!;

    expect(painel).toHaveClass("com-resultado");
    expect(painel).not.toHaveClass("editando");

    fireEvent.click(screen.getByRole("button", { name: /Editar/ }));
    expect(painel).toHaveClass("editando");
    expect(screen.getByRole("button", { name: /Fechar edição/ })).toHaveAttribute(
      "aria-expanded",
      "true"
    );
  });

  it("um resultado novo volta ao modo resumido", () => {
    const { container, rerender } = renderizar();
    const painel = container.querySelector(".plan-painel")!;

    fireEvent.click(screen.getByRole("button", { name: /Editar/ }));
    expect(painel).toHaveClass("editando");

    rerender(
      <PlanejadorViagem
        {...props}
        origem={origemMock}
        destino={destinoMock}
        opcoes={[opcaoViva, opcaoComBaldeacao]}
        opcaoSelecionada={0}
        rastreando
      />
    );
    expect(painel).not.toHaveClass("editando");
  });

  it("sem resultado não há resumo nem painel em modo de resultado", () => {
    const { container } = renderizar({ opcoes: null });

    expect(container.querySelector(".plan-resumo-rota")).toBeNull();
    expect(container.querySelector(".plan-painel")).not.toHaveClass("com-resultado");
  });
});

describe("PlanejadorViagem — campo de lugar acessível por teclado (card #179)", () => {
  const LUGARES = [
    { nome: "Terminal Ceilândia", endereco: "Ceilândia Sul", lat: -15.83, lng: -48.04 },
    { nome: "Terminal Taguatinga", endereco: "Taguatinga Centro", lat: -15.84, lng: -48.05 },
  ];

  async function digitarEAbrir(onDefinir = jest.fn()) {
    apiMock.buscarLugares.mockResolvedValueOnce(LUGARES);
    render(<PlanejadorViagem {...props} onDefinir={onDefinir} />);

    const campo = screen.getByLabelText("De onde");
    fireEvent.focus(campo);
    fireEvent.change(campo, { target: { value: "Terminal" } });
    await screen.findByRole("listbox", {}, { timeout: 2000 });
    return { campo, onDefinir };
  }

  it("expõe o padrão combobox: papel, expanded, controls e opções", async () => {
    const { campo } = await digitarEAbrir();

    expect(campo).toHaveAttribute("role", "combobox");
    expect(campo).toHaveAttribute("aria-expanded", "true");
    expect(campo).toHaveAttribute("aria-autocomplete", "list");
    expect(campo.getAttribute("aria-controls")).toBe(screen.getByRole("listbox").id);
    expect(screen.getAllByRole("option")).toHaveLength(2);
  });

  it("setas percorrem as opções e anunciam a ativa via aria-activedescendant", async () => {
    const { campo } = await digitarEAbrir();

    fireEvent.keyDown(campo, { key: "ArrowDown" });
    const [primeira, segunda] = screen.getAllByRole("option");
    expect(primeira).toHaveAttribute("aria-selected", "true");
    expect(campo.getAttribute("aria-activedescendant")).toBe(primeira.id);

    fireEvent.keyDown(campo, { key: "ArrowDown" });
    expect(segunda).toHaveAttribute("aria-selected", "true");

    // dá a volta
    fireEvent.keyDown(campo, { key: "ArrowDown" });
    expect(primeira).toHaveAttribute("aria-selected", "true");

    fireEvent.keyDown(campo, { key: "ArrowUp" });
    expect(segunda).toHaveAttribute("aria-selected", "true");
  });

  it("Enter na opção ativa escolhe o lugar (e não envia o formulário)", async () => {
    const { campo, onDefinir } = await digitarEAbrir();

    fireEvent.keyDown(campo, { key: "ArrowDown" });
    fireEvent.keyDown(campo, { key: "ArrowDown" });
    fireEvent.keyDown(campo, { key: "Enter" });

    expect(onDefinir).toHaveBeenCalledWith("origem", {
      nome: "Terminal Taguatinga",
      lat: -15.84,
      lng: -48.05,
    });
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("Escape fecha a lista sem escolher nada", async () => {
    const { campo, onDefinir } = await digitarEAbrir();

    fireEvent.keyDown(campo, { key: "ArrowDown" });
    fireEvent.keyDown(campo, { key: "Escape" });

    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    expect(onDefinir).not.toHaveBeenCalled();
  });

  it("clicar numa opção continua funcionando", async () => {
    const { onDefinir } = await digitarEAbrir();

    fireEvent.click(screen.getByText("Terminal Ceilândia"));

    expect(onDefinir).toHaveBeenCalledWith(
      "origem",
      expect.objectContaining({ nome: "Terminal Ceilândia" })
    );
  });

  it("os botões só-ícone têm nome acessível", () => {
    render(<PlanejadorViagem {...props} origem={origemMock} destino={destinoMock} />);

    expect(
      screen.getByRole("button", { name: "Fechar planejador de viagem" })
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Inverter origem e destino" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Limpar de onde" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Limpar para onde" })).toBeInTheDocument();
  });
});
