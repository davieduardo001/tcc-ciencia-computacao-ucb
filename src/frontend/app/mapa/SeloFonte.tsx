/**
 * Origem de um número de tempo (RN-10 do card #179): todo tempo exibido diz
 * de onde veio. Um horário de SAÍDA DO TERMINAL, por exemplo, não pode ser
 * lido como "quando o ônibus passa aqui" — são coisas diferentes, e a
 * diferença pode ser de dezenas de minutos.
 */
export type FonteDoTempo = "ao_vivo" | "media" | "estimado" | "saida_terminal" | "previsto";

const FONTES: Record<FonteDoTempo, { texto: string; legenda: string }> = {
  ao_vivo: {
    texto: "ao vivo",
    legenda: "Medido a partir da posição real do ônibus agora",
  },
  media: {
    texto: "média",
    legenda: "Intervalo médio entre os ônibus da linha, e não um horário marcado",
  },
  estimado: {
    texto: "estimado",
    legenda: "Estimativa por velocidade média, sem dado ao vivo",
  },
  saida_terminal: {
    texto: "saída do terminal",
    legenda: "Horário em que o ônibus sai da origem da linha — não é a hora em que passa nesta parada",
  },
  previsto: {
    texto: "previsto",
    legenda:
      "Sem ônibus a caminho: horário de saída do terminal somado ao tempo de percurso até esta parada",
  },
};

export function legendaDaFonte(fonte: FonteDoTempo): string {
  return FONTES[fonte].legenda;
}

export default function SeloFonte({ fonte }: { fonte: FonteDoTempo }) {
  const { texto, legenda } = FONTES[fonte];
  return (
    <span className={`selo-fonte ${fonte.replace("_", "-")}`} title={legenda}>
      {texto}
    </span>
  );
}
