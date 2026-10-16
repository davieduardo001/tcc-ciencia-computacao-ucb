import { LinhaNaParada } from "@/lib/api";

interface SaidasDoTerminalProps {
  linhas: LinhaNaParada[];
  /** Lista combinada da parada: só é usada quando o backend não manda os
   * horários de cada linha (versão antiga). */
  horariosCombinados: string[];
}

/**
 * Próximas saídas do terminal, uma linha por ônibus (issue #174): o PRD da
 * US #18 pede os próximos horários DE CADA linha, e não três no total
 * misturando as que passam pela parada.
 */
export default function SaidasDoTerminal({ linhas, horariosCombinados }: SaidasDoTerminalProps) {
  const backendPorLinha = linhas.some((l) => l.proximosHorarios !== undefined);

  if (!backendPorLinha) {
    // Cenário 2 da US #18: parada sem horário disponível.
    return horariosCombinados.length > 0 ? (
      <p>{horariosCombinados.join(" · ")}</p>
    ) : (
      <p className="mapa-painel-sem-veiculo">
        Nenhuma saída prevista disponível para esta parada no momento.
      </p>
    );
  }

  if (linhas.every((l) => (l.proximosHorarios ?? []).length === 0)) {
    return (
      <p className="mapa-painel-sem-veiculo">
        Nenhuma saída prevista disponível para esta parada no momento.
      </p>
    );
  }

  return (
    <ul className="mapa-saidas">
      {linhas.map((linha) => {
        const horarios = linha.proximosHorarios ?? [];
        return (
          <li key={linha.numero} className="mapa-saida">
            <strong>{linha.numero}</strong>{" "}
            {horarios.length > 0 ? (
              <span>{horarios.join(" · ")}</span>
            ) : (
              <span className="mapa-painel-sem-veiculo">sem saída prevista hoje</span>
            )}
          </li>
        );
      })}
    </ul>
  );
}
