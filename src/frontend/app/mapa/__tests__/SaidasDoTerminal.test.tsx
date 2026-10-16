import { render, screen } from "@testing-library/react";
import SaidasDoTerminal from "../SaidasDoTerminal";

const SEM_SAIDA = "Nenhuma saída prevista disponível para esta parada no momento.";

describe("SaidasDoTerminal (issue #174)", () => {
  it("uma linha por ônibus, cada uma com as próprias saídas", () => {
    render(
      <SaidasDoTerminal
        linhas={[
          { numero: "0.110", nome: "A", sentido: "ida", proximosHorarios: ["06:20", "06:40", "07:00"] },
          { numero: "0.220", nome: "B", sentido: "ida", proximosHorarios: ["06:30"] },
        ]}
        horariosCombinados={["06:20", "06:30", "06:40"]}
      />
    );

    const itens = screen.getAllByRole("listitem");
    expect(itens).toHaveLength(2);
    expect(itens[0]).toHaveTextContent("0.110 06:20 · 06:40 · 07:00");
    expect(itens[1]).toHaveTextContent("0.220 06:30");
  });

  it("linha sem saída hoje aparece dizendo isso, sem inventar horário", () => {
    render(
      <SaidasDoTerminal
        linhas={[
          { numero: "0.110", nome: "A", sentido: "ida", proximosHorarios: ["06:20"] },
          { numero: "0.330", nome: "C", sentido: "ida", proximosHorarios: [] },
        ]}
        horariosCombinados={["06:20"]}
      />
    );

    expect(screen.getAllByRole("listitem")[1]).toHaveTextContent("0.330 sem saída prevista hoje");
  });

  it("todas as linhas sem saída: mostra o aviso, e não uma lista vazia", () => {
    render(
      <SaidasDoTerminal
        linhas={[{ numero: "0.110", nome: "A", sentido: "ida", proximosHorarios: [] }]}
        horariosCombinados={[]}
      />
    );

    expect(screen.getByText(SEM_SAIDA)).toBeInTheDocument();
    expect(screen.queryByRole("list")).not.toBeInTheDocument();
  });

  it("backend antigo, sem horários por linha: usa a lista combinada de sempre", () => {
    render(
      <SaidasDoTerminal
        linhas={[{ numero: "0.110", nome: "A", sentido: "ida" }]}
        horariosCombinados={["06:20", "06:40", "07:00"]}
      />
    );

    expect(screen.getByText("06:20 · 06:40 · 07:00")).toBeInTheDocument();
    expect(screen.queryByRole("list")).not.toBeInTheDocument();
  });

  it("backend antigo e sem horário nenhum: mostra o aviso", () => {
    render(
      <SaidasDoTerminal
        linhas={[{ numero: "0.110", nome: "A", sentido: "ida" }]}
        horariosCombinados={[]}
      />
    );

    expect(screen.getByText(SEM_SAIDA)).toBeInTheDocument();
  });
});
