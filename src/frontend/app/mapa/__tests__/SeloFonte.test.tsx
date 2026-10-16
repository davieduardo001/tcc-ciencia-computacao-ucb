import { render, screen } from "@testing-library/react";
import SeloFonte, { FonteDoTempo, legendaDaFonte } from "../SeloFonte";

describe("SeloFonte", () => {
  const CASOS: [FonteDoTempo, string, string][] = [
    ["ao_vivo", "ao vivo", "ao-vivo"],
    ["media", "média", "media"],
    ["estimado", "estimado", "estimado"],
    ["saida_terminal", "saída do terminal", "saida-terminal"],
  ];

  it.each(CASOS)("%s mostra '%s' e a classe '%s'", (fonte, texto, classe) => {
    render(<SeloFonte fonte={fonte} />);

    expect(screen.getByText(texto)).toHaveClass("selo-fonte", classe);
  });

  it("cada selo traz a legenda no title, pra quem passa o mouse/toca e quer entender", () => {
    render(<SeloFonte fonte="saida_terminal" />);

    expect(screen.getByText("saída do terminal")).toHaveAttribute(
      "title",
      expect.stringContaining("não é a hora em que passa nesta parada")
    );
  });

  it("toda fonte tem legenda não vazia", () => {
    CASOS.forEach(([fonte]) => {
      expect(legendaDaFonte(fonte).length).toBeGreaterThan(10);
    });
  });

  it("a legenda do 'ao vivo' fala de posição real; a do 'estimado', de velocidade média", () => {
    expect(legendaDaFonte("ao_vivo")).toMatch(/posição real/);
    expect(legendaDaFonte("estimado")).toMatch(/velocidade média/);
    expect(legendaDaFonte("media")).toMatch(/não um horário marcado/);
  });
});
