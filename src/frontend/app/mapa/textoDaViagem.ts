import type { ViagemAtiva } from "@/lib/api";

export interface TextoDaViagem {
  /** A frase principal da faixa. */
  principal: string;
  /** `alerta` quando o usuário precisa saber de algo que não é o normal. */
  tom: "normal" | "alerta";
}

function plural(n: number, singular: string, plural: string): string {
  return n === 1 ? singular : plural;
}

/**
 * O que a faixa de viagem diz agora.
 *
 * A ordem das regras é a da confiança no dado (RN-09): sem sinal do ônibus
 * não se estima nada; destino ultrapassado vale mais que "próxima parada";
 * sem trajeto conhecido, a tela diz que só acompanha o ônibus em vez de
 * inventar uma parada.
 */
export function textoDaViagem(viagem: ViagemAtiva): TextoDaViagem {
  if (viagem.sinal === "sem_sinal") {
    return { principal: "Sem sinal do ônibus no momento", tom: "alerta" };
  }

  if (viagem.destino?.ultrapassado) {
    return {
      principal: `O ônibus já passou de ${viagem.destino.nome}`,
      tom: "alerta",
    };
  }

  const proxima = viagem.proximaParada;
  if (!proxima) {
    return { principal: "Acompanhando o ônibus", tom: "normal" };
  }

  const faltam = viagem.paradasRestantes.length;
  if (viagem.destino && faltam === 1) {
    return {
      principal: `Sua parada, ${viagem.destino.nome}, é a próxima`,
      tom: "normal",
    };
  }
  if (viagem.destino && faltam > 1) {
    return {
      principal: `Próxima: ${proxima.nome} · ${plural(faltam, "falta", "faltam")} ${faltam} ${plural(
        faltam,
        "parada",
        "paradas"
      )} até ${viagem.destino.nome}`,
      tom: "normal",
    };
  }

  return { principal: `Próxima parada: ${proxima.nome}`, tom: "normal" };
}
