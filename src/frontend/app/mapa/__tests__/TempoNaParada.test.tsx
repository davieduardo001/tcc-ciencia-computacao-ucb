import { render, screen } from "@testing-library/react";
import type { ChegadaNoPonto } from "@/lib/api";
import TempoNaParada, { SEM_DADO, temTempo } from "../TempoNaParada";

function ponto(sobre: Partial<ChegadaNoPonto> = {}): ChegadaNoPonto {
  return { paradaCodigo: "PR-1", etaMinutos: null, fonte: null, prefixo: null, horarioPrevisto: null, ...sobre };
}

describe("TempoNaParada", () => {
  it("ao vivo: minutos inteiros, carro e o selo de origem", () => {
    render(
      <TempoNaParada ponto={ponto({ etaMinutos: 4.3, fonte: "ao_vivo", prefixo: "440001" })} qual="embarque" />
    );

    expect(screen.getByLabelText("Tempo até o embarque")).toHaveTextContent("Chega em 4 min (carro 440001)");
    expect(screen.getByText("ao vivo")).toBeInTheDocument();
  });

  it("ao vivo sem prefixo não deixa um parêntese vazio", () => {
    render(<TempoNaParada ponto={ponto({ etaMinutos: 4, fonte: "ao_vivo" })} qual="embarque" />);

    expect(screen.getByLabelText("Tempo até o embarque")).toHaveTextContent(/^Chega em 4 min\s*ao vivo$/);
  });

  it("menos de 1 minuto vira 'menos de 1 min', e não '0 min'", () => {
    render(<TempoNaParada ponto={ponto({ etaMinutos: 0.2, fonte: "ao_vivo" })} qual="desembarque" />);

    const texto = screen.getByLabelText("Tempo até o desembarque");
    expect(texto).toHaveTextContent("menos de 1 min");
    expect(texto).not.toHaveTextContent("0 min");
  });

  it("previsto: horário e minutos, com o selo 'previsto' (e nunca 'ao vivo')", () => {
    render(
      <TempoNaParada
        ponto={ponto({ etaMinutos: 18.4, fonte: "previsto", horarioPrevisto: "15:18" })}
        qual="desembarque"
      />
    );

    expect(screen.getByLabelText("Tempo até o desembarque")).toHaveTextContent("Previsto às 15:18 (em 18 min)");
    expect(screen.getByText("previsto")).toBeInTheDocument();
    expect(screen.queryByText("ao vivo")).not.toBeInTheDocument();
  });

  it("sem dado: 'Sem previsão no momento', sem selo de origem", () => {
    render(<TempoNaParada ponto={ponto()} qual="embarque" />);

    expect(screen.getByLabelText("Tempo até o embarque")).toHaveTextContent("Sem previsão no momento");
    expect(screen.queryByText("ao vivo")).not.toBeInTheDocument();
    expect(screen.queryByText("previsto")).not.toBeInTheDocument();
  });

  it("fonte sem minutos (dado incompleto) cai em 'Sem previsão' em vez de mostrar 'null min'", () => {
    render(<TempoNaParada ponto={ponto({ fonte: "ao_vivo", etaMinutos: null })} qual="embarque" />);

    expect(screen.getByLabelText("Tempo até o embarque")).toHaveTextContent("Sem previsão no momento");
    expect(screen.queryByText(/null/)).not.toBeInTheDocument();
  });

  it("SEM_DADO sempre diz 'Sem previsão no momento'", () => {
    render(<TempoNaParada ponto={SEM_DADO} qual="desembarque" />);
    expect(screen.getByText("Sem previsão no momento")).toBeInTheDocument();
  });

  it.each([[null], [undefined]])("sem resposta ainda (%s), não afirma nada", (vazio) => {
    const { container } = render(<TempoNaParada ponto={vazio} qual="embarque" />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe("temTempo", () => {
  it("ao vivo e previsto com minutos têm tempo", () => {
    expect(temTempo(ponto({ etaMinutos: 3, fonte: "ao_vivo" }))).toBe(true);
    expect(temTempo(ponto({ etaMinutos: 0, fonte: "previsto" }))).toBe(true);
  });

  it("zero minutos ainda é um tempo (o ônibus está chegando)", () => {
    expect(temTempo(ponto({ etaMinutos: 0, fonte: "ao_vivo" }))).toBe(true);
  });

  it.each([
    ["sem dado", ponto()],
    ["fonte sem minutos", ponto({ fonte: "ao_vivo" })],
    ["minutos sem fonte", ponto({ etaMinutos: 3 })],
    ["null", null],
    ["undefined", undefined],
  ])("%s não tem tempo", (_nome, valor) => {
    expect(temTempo(valor)).toBe(false);
  });
});
