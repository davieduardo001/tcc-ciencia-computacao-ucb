import { render, screen } from "@testing-library/react";
import QuadroDeHorarios from "../QuadroDeHorarios";
import type { QuadroHorarios } from "@/lib/api";

const BASE: QuadroHorarios = {
  estado: "operando",
  tempoPercursoMin: 75,
  proximaPartida: { horario: "12:00", quando: "hoje", emMinutos: 30 },
  grupos: [
    { rotulo: "Segunda a sexta", horarios: ["05:00", "12:00"], hoje: true },
    { rotulo: "Sábado", horarios: ["07:00"], hoje: false },
    { rotulo: "Domingo", horarios: ["08:00"], hoje: false },
  ],
};

describe("QuadroDeHorarios (US #118)", () => {
  it("mostra o quadro por dia e destaca a próxima partida de hoje", () => {
    render(<QuadroDeHorarios quadro={BASE} />);

    expect(screen.getByText("Segunda a sexta (hoje)")).toBeInTheDocument();
    expect(screen.getByText("Sábado")).toBeInTheDocument();
    expect(screen.getByText("Domingo")).toBeInTheDocument();
    expect(screen.getByText("12:00", { selector: "li" })).toHaveAttribute("aria-current", "time");
    expect(screen.getByText("05:00")).not.toHaveAttribute("aria-current");
    expect(screen.getByText(/cerca de 75 min/)).toBeInTheDocument();
  });

  it("diz explicitamente quando a linha está fora de operação", () => {
    render(
      <QuadroDeHorarios
        quadro={{
          ...BASE,
          estado: "fora_do_horario",
          proximaPartida: { horario: "05:00", quando: "amanhã", emMinutos: 400 },
        }}
      />
    );

    expect(screen.getByText("Fora de operação agora.")).toBeInTheDocument();
    expect(screen.getByText(/amanhã/)).toBeInTheDocument();
    expect(screen.getByText("05:00", { selector: "li" })).not.toHaveAttribute("aria-current");
  });

  it("diz que a linha não opera hoje", () => {
    render(<QuadroDeHorarios quadro={{ ...BASE, estado: "nao_opera_hoje" }} />);

    expect(screen.getByText("Esta linha não opera hoje.")).toBeInTheDocument();
  });

  it("informa que não há horário publicado", () => {
    render(
      <QuadroDeHorarios
        quadro={{ estado: "sem_horario", tempoPercursoMin: null, proximaPartida: null, grupos: [] }}
      />
    );

    expect(screen.getByText("Não há horário publicado para esta linha.")).toBeInTheDocument();
  });

  it("não renderiza nada quando o backend não manda o quadro", () => {
    const { container } = render(<QuadroDeHorarios quadro={null} />);

    expect(container).toBeEmptyDOMElement();
  });
});
