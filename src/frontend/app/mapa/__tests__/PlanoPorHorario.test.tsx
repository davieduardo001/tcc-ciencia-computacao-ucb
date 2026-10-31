import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import PlanoPorHorario, { duracaoEmTexto, horaDe } from "../PlanoPorHorario";
import { planejarViagem, PlanoViagem } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  ...jest.requireActual("@/lib/api"),
  planejarViagem: jest.fn(),
}));

const ORIGEM = { lat: -15.83, lng: -48.05 };
const DESTINO = { lat: -15.79, lng: -47.88 };

const PONTO = (nome: string) => ({
  lat: 0,
  lng: 0,
  parada_nome: nome,
  caminhada_metros: 100,
});

const PLANO: PlanoViagem = {
  tipo: "saida",
  referencia: "2026-11-02T07:10:00-03:00",
  motivo: null,
  mensagem: null,
  estimado: true,
  opcoes: [
    {
      baldeacoes: 1,
      caminhada_metros: 300,
      saida_casa: "2026-11-02T07:10:00-03:00",
      chegada_destino: "2026-11-02T08:25:00-03:00",
      duracao_total_min: 75,
      pernas: [
        {
          numero: "0.110",
          sentido: "IDA",
          nome: "Linha A",
          embarque: PONTO("Parada Casa"),
          desembarque: PONTO("Rodoviária"),
          embarca_em: "2026-11-02T07:15:00-03:00",
          desembarca_em: "2026-11-02T07:45:00-03:00",
          espera_min: 5,
        },
        {
          numero: "0.220",
          sentido: "IDA",
          nome: "Linha B",
          embarque: PONTO("Rodoviária"),
          desembarque: PONTO("Parada Trabalho"),
          embarca_em: "2026-11-02T08:00:00-03:00",
          desembarca_em: "2026-11-02T08:20:00-03:00",
          espera_min: 15,
        },
      ],
    },
  ],
};

function abrir() {
  render(<PlanoPorHorario origem={ORIGEM} destino={DESTINO} />);
  fireEvent.click(screen.getByRole("button", { name: /planejar por horário/i }));
}

describe("PlanoPorHorario", () => {
  beforeEach(() => jest.resetAllMocks());

  it("fica recolhido até o usuário abrir", () => {
    render(<PlanoPorHorario origem={ORIGEM} destino={DESTINO} />);

    expect(screen.queryByLabelText("Horário")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /planejar por horário/i })).toHaveAttribute(
      "aria-expanded",
      "false"
    );
  });

  it("Cenário 1: 'sair às' envia o tipo saída e o horário digitado", async () => {
    (planejarViagem as jest.Mock).mockResolvedValue(PLANO);
    abrir();

    fireEvent.change(screen.getByLabelText("Horário"), { target: { value: "07:10" } });
    fireEvent.click(screen.getByRole("button", { name: "Planejar" }));

    await waitFor(() => expect(planejarViagem).toHaveBeenCalled());
    const [origem, destino, tipo, horario] = (planejarViagem as jest.Mock).mock.calls[0];
    expect(origem).toEqual(ORIGEM);
    expect(destino).toEqual(DESTINO);
    expect(tipo).toBe("saida");
    expect(horario).toBe("07:10");
  });

  it("Cenário 2: 'chegar até' envia o tipo chegada", async () => {
    (planejarViagem as jest.Mock).mockResolvedValue({ ...PLANO, tipo: "chegada" });
    abrir();

    fireEvent.click(screen.getByLabelText("Chegar até"));
    fireEvent.change(screen.getByLabelText("Horário"), { target: { value: "08:00" } });
    fireEvent.click(screen.getByRole("button", { name: "Planejar" }));

    await waitFor(() => expect(planejarViagem).toHaveBeenCalled());
    expect((planejarViagem as jest.Mock).mock.calls[0][2]).toBe("chegada");
  });

  it("Cenário 3: mostra os horários de cada perna e a espera na baldeação", async () => {
    (planejarViagem as jest.Mock).mockResolvedValue(PLANO);
    abrir();
    fireEvent.change(screen.getByLabelText("Horário"), { target: { value: "07:10" } });
    fireEvent.click(screen.getByRole("button", { name: "Planejar" }));

    expect(await screen.findByText(/1 baldeação/)).toBeInTheDocument();
    expect(screen.getByText(/Espera de 15 min no ponto de troca/)).toBeInTheDocument();
    expect(screen.getByText(/Espera de 5 min no ponto de embarque/)).toBeInTheDocument();
    expect(screen.getByText("Parada Casa", { exact: false })).toBeInTheDocument();
    expect(screen.getByText("Parada Trabalho", { exact: false })).toBeInTheDocument();
    expect(screen.getByText(/1 h 15 min/)).toBeInTheDocument();
  });

  it("declara que os horários são estimados", async () => {
    (planejarViagem as jest.Mock).mockResolvedValue(PLANO);
    abrir();
    fireEvent.change(screen.getByLabelText("Horário"), { target: { value: "07:10" } });
    fireEvent.click(screen.getByRole("button", { name: "Planejar" }));

    expect(await screen.findByText(/estimados/)).toBeInTheDocument();
  });

  it("Cenário 5: sem opção, mostra o motivo em vez de lista vazia", async () => {
    (planejarViagem as jest.Mock).mockResolvedValue({
      ...PLANO,
      opcoes: [],
      motivo: "fora_do_horario",
      mensagem: "Nenhum ônibus atende este trajeto neste horário.",
    });
    abrir();
    fireEvent.change(screen.getByLabelText("Horário"), { target: { value: "23:30" } });
    fireEvent.click(screen.getByRole("button", { name: "Planejar" }));

    expect(
      await screen.findByText("Nenhum ônibus atende este trajeto neste horário.")
    ).toBeInTheDocument();
  });

  it("erro do servidor aparece como alerta", async () => {
    (planejarViagem as jest.Mock).mockRejectedValue(new Error("Falha ao planejar."));
    abrir();
    fireEvent.change(screen.getByLabelText("Horário"), { target: { value: "07:10" } });
    fireEvent.click(screen.getByRole("button", { name: "Planejar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Falha ao planejar.");
  });

  it("trocar o destino descarta o plano anterior", async () => {
    (planejarViagem as jest.Mock).mockResolvedValue(PLANO);
    const { rerender } = render(<PlanoPorHorario origem={ORIGEM} destino={DESTINO} />);
    fireEvent.click(screen.getByRole("button", { name: /planejar por horário/i }));
    fireEvent.change(screen.getByLabelText("Horário"), { target: { value: "07:10" } });
    fireEvent.click(screen.getByRole("button", { name: "Planejar" }));
    await screen.findByText(/1 baldeação/);

    rerender(<PlanoPorHorario origem={ORIGEM} destino={{ lat: -15.5, lng: -47.5 }} />);

    expect(screen.queryByText(/1 baldeação/)).not.toBeInTheDocument();
  });
});

describe("formatação", () => {
  it("horaDe mostra HH:MM no fuso de Brasília", () => {
    expect(horaDe("2026-11-02T07:15:00-03:00")).toBe("07:15");
    expect(horaDe("2026-11-02T10:15:00Z")).toBe("07:15");
  });

  it("duracaoEmTexto usa minutos abaixo de 1 h e horas acima", () => {
    expect(duracaoEmTexto(45)).toBe("45 min");
    expect(duracaoEmTexto(60)).toBe("1 h");
    expect(duracaoEmTexto(75)).toBe("1 h 15 min");
  });
});
