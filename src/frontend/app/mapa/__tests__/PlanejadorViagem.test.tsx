import { fireEvent, render, screen } from "@testing-library/react";
import PlanejadorViagem from "../PlanejadorViagem";

jest.mock("@/lib/api", () => ({
  buscarLugares: jest.fn().mockResolvedValue([]),
  nomearLugar: jest.fn().mockResolvedValue(null),
}));

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
