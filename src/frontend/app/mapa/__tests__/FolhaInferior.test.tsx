import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import FolhaInferior, {
  alturasDaFolha,
  ALTURA_MINIMA,
  snapMaisProximo,
  SnapFolha,
} from "../FolhaInferior";

// jsdom: window.innerHeight = 768 e as áreas medem 0, então a folha usa a
// janela inteira como área útil: mínimo 96, médio ~476 (62vh), máximo 760.

/** MouseEvent de propósito: o jsdom não implementa PointerEvent. */
function arrastar(alvo: HTMLElement, dy: number, y0 = 400) {
  fireEvent(alvo, new MouseEvent("pointerdown", { clientY: y0, bubbles: true }));
  fireEvent(window, new MouseEvent("pointermove", { clientY: y0 + dy, bubbles: true }));
  fireEvent(window, new MouseEvent("pointerup", { clientY: y0 + dy, bubbles: true }));
}

function Folha({ inicial = "medio" as SnapFolha, aoMudar = jest.fn() }) {
  const [snap, setSnap] = useState<SnapFolha>(inicial);
  return (
    <FolhaInferior
      snap={snap}
      onSnapChange={(s) => {
        aoMudar(s);
        setSnap(s);
      }}
      titulo={<strong>Título</strong>}
      rotuloAlca="a folha"
      rotuloFechar="Fechar a folha"
      onFechar={jest.fn()}
    >
      <p>conteúdo</p>
    </FolhaInferior>
  );
}

beforeEach(() => {
  jest.spyOn(performance, "now").mockReturnValue(0);
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe("alturasDaFolha / snapMaisProximo", () => {
  it("calcula as três alturas", () => {
    const alturas = alturasDaFolha(800);

    expect(alturas.minimo).toBe(ALTURA_MINIMA);
    expect(alturas.maximo).toBe(792);
    expect(alturas.medio).toBeCloseTo(768 * 0.62);
  });

  it("escolhe o encaixe mais próximo", () => {
    const alturas = alturasDaFolha(800);

    expect(snapMaisProximo(100, alturas)).toBe("minimo");
    expect(snapMaisProximo(470, alturas)).toBe("medio");
    expect(snapMaisProximo(700, alturas)).toBe("maximo");
  });
});

describe("FolhaInferior", () => {
  it("encaixa no mínimo ao soltar perto dele e permanece lá", () => {
    const { container } = render(<Folha />);
    const folha = container.querySelector("aside")!;

    arrastar(container.querySelector(".plan-alca") as HTMLElement, 600);

    expect(folha).toHaveClass("snap-minimo");
    // Sem altura inline sobrando: o encaixe é o estado, não um valor solto.
    expect(folha.style.height).toBe("");
  });

  it("encaixa no máximo ao puxar bastante para cima", () => {
    const { container } = render(<Folha />);

    arrastar(container.querySelector(".plan-alca") as HTMLElement, -600);

    expect(container.querySelector("aside")).toHaveClass("snap-maximo");
  });

  it("solta perto do meio e fica no meio, sem voltar a outro estado", () => {
    const { container } = render(<Folha inicial="maximo" />);

    // De 760 para ~476: dy = +284.
    arrastar(container.querySelector(".plan-alca") as HTMLElement, 284);

    expect(container.querySelector("aside")).toHaveClass("snap-medio");
  });

  it("o cabeçalho também arrasta", () => {
    const { container } = render(<Folha />);

    arrastar(container.querySelector(".folha-cabecalho") as HTMLElement, 600);

    expect(container.querySelector("aside")).toHaveClass("snap-minimo");
  });

  it("o botão de fechar não inicia arrasto", () => {
    const { container } = render(<Folha />);

    arrastar(screen.getByRole("button", { name: "Fechar a folha" }), 600);

    expect(container.querySelector("aside")).toHaveClass("snap-medio");
  });

  it("clique na alça sem arrasto alterna uma vez, sem oscilar", () => {
    const aoMudar = jest.fn();
    const { container } = render(<Folha aoMudar={aoMudar} />);
    const alca = container.querySelector(".plan-alca") as HTMLElement;

    // Toque sem movimento: pointerdown + pointerup + click.
    fireEvent(alca, new MouseEvent("pointerdown", { clientY: 400, bubbles: true }));
    fireEvent(window, new MouseEvent("pointerup", { clientY: 400, bubbles: true }));
    fireEvent.click(alca);

    expect(aoMudar).toHaveBeenCalledTimes(1);
    expect(aoMudar).toHaveBeenCalledWith("minimo");
  });

  it("o clique que vem logo após um arrasto é ignorado", () => {
    const aoMudar = jest.fn();
    const { container } = render(<Folha aoMudar={aoMudar} />);
    const alca = container.querySelector(".plan-alca") as HTMLElement;

    arrastar(alca, 600);
    fireEvent.click(alca);

    expect(aoMudar).toHaveBeenCalledTimes(1);
    expect(container.querySelector("aside")).toHaveClass("snap-minimo");
  });

  it("teclado: setas sobem e descem um encaixe", () => {
    const { container } = render(<Folha inicial="minimo" />);
    const alca = container.querySelector(".plan-alca") as HTMLElement;
    const folha = container.querySelector("aside")!;

    fireEvent.keyDown(alca, { key: "ArrowUp" });
    expect(folha).toHaveClass("snap-medio");
    fireEvent.keyDown(alca, { key: "ArrowUp" });
    expect(folha).toHaveClass("snap-maximo");
    fireEvent.keyDown(alca, { key: "ArrowUp" });
    expect(folha).toHaveClass("snap-maximo");

    fireEvent.keyDown(alca, { key: "ArrowDown" });
    expect(folha).toHaveClass("snap-medio");
    fireEvent.keyDown(alca, { key: "ArrowDown" });
    expect(folha).toHaveClass("snap-minimo");
  });

  it("aria-expanded e o nome da alça acompanham o encaixe", () => {
    render(<Folha inicial="minimo" />);

    const alca = screen.getByRole("button", { name: "Abrir a folha" });
    expect(alca).toHaveAttribute("aria-expanded", "false");

    fireEvent.click(alca);

    expect(screen.getByRole("button", { name: "Recolher a folha" })).toHaveAttribute(
      "aria-expanded",
      "true"
    );
  });

  it("sem snap controlado guarda o próprio estado", () => {
    const { container } = render(
      <FolhaInferior
        snapInicial="minimo"
        titulo="T"
        rotuloAlca="x"
        rotuloFechar="Fechar x"
        onFechar={jest.fn()}
      >
        <p>a</p>
      </FolhaInferior>
    );

    fireEvent.click(container.querySelector(".plan-alca") as HTMLElement);

    expect(container.querySelector("aside")).toHaveClass("snap-medio");
  });

  it("mostra o rodapé fixo e marca a folha", () => {
    const { container } = render(
      <FolhaInferior
        titulo="T"
        rotuloAlca="x"
        rotuloFechar="Fechar x"
        onFechar={jest.fn()}
        rodape={<button type="button">Cheguei</button>}
      >
        <p>a</p>
      </FolhaInferior>
    );

    expect(container.querySelector("aside")).toHaveClass("com-rodape");
    expect(screen.getByRole("button", { name: "Cheguei" })).toBeInTheDocument();
  });

  it("oculta mantém o conteúdo montado", () => {
    const { container } = render(
      <FolhaInferior
        titulo="T"
        rotuloAlca="x"
        rotuloFechar="Fechar x"
        onFechar={jest.fn()}
        oculta
      >
        <p>guardado</p>
      </FolhaInferior>
    );

    expect(container.querySelector("aside")).toHaveAttribute("hidden");
    expect(container.textContent).toContain("guardado");
  });
});
