import { Bus } from "lucide-react";
import type { ChegadaNoPonto } from "@/lib/api";
import SeloFonte from "./SeloFonte";
import { formatarMinutos } from "./tempo";

/**
 * Quando o ônibus daquele trecho chega a uma parada de subir ou de descer
 * (issue #190). Mesma redação do painel da parada (#185): "Chega em N min"
 * (ao vivo), "Previsto às HH:MM (em N min)" ou "Sem previsão no momento" —
 * nunca um número sem dizer de onde veio (RN-10), nunca um número inventado
 * (RN-09).
 *
 * `ponto` = `null`/`undefined` quando ainda não há resposta (carregando, ou a
 * consulta falhou): não afirma nada, nem mesmo "sem previsão".
 */
export default function TempoNaParada({
  ponto,
  qual,
}: {
  ponto: ChegadaNoPonto | null | undefined;
  /** Só para a leitura de tela: de que parada é o tempo. */
  qual: "embarque" | "desembarque";
}) {
  if (!ponto) return null;

  const rotulo = qual === "embarque" ? "Tempo até o embarque" : "Tempo até o desembarque";

  if (ponto.fonte === "ao_vivo" && ponto.etaMinutos !== null) {
    return (
      <p className="plan-chegada ao-vivo" aria-label={rotulo}>
        <span className="mapa-pulso" />
        <Bus size={14} aria-hidden="true" />
        <span>
          Chega em <strong>{formatarMinutos(ponto.etaMinutos)}</strong>
          {ponto.prefixo ? ` (carro ${ponto.prefixo})` : ""}
        </span>
        <SeloFonte fonte="ao_vivo" />
      </p>
    );
  }

  if (ponto.fonte === "previsto" && ponto.etaMinutos !== null) {
    return (
      <p className="plan-chegada" aria-label={rotulo}>
        <span>
          Previsto às <strong>{ponto.horarioPrevisto}</strong> (em {formatarMinutos(ponto.etaMinutos)})
        </span>
        <SeloFonte fonte="previsto" />
      </p>
    );
  }

  return (
    <p className="plan-chegada sem-onibus" aria-label={rotulo}>
      Sem previsão no momento
    </p>
  );
}

/** Ponto sem nenhum dado: faz o componente dizer "Sem previsão no momento". */
export const SEM_DADO: ChegadaNoPonto = {
  paradaCodigo: null,
  etaMinutos: null,
  fonte: null,
  prefixo: null,
  horarioPrevisto: null,
};

/** `true` quando há um número para mostrar (ao vivo ou previsto). */
export function temTempo(ponto: ChegadaNoPonto | null | undefined): boolean {
  return Boolean(ponto && ponto.fonte !== null && ponto.etaMinutos !== null);
}
