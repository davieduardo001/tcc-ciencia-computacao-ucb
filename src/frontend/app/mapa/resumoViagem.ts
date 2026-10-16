import { OpcaoViagem, PernaViagem } from "@/lib/api";

/**
 * Cálculos do resultado de rota que não dependem de React: duração exibida,
 * caminhada em minutos, destaques entre opções e os passos da linha do tempo.
 * Ficam aqui pra serem testados sem renderizar nada.
 */

/** Velocidade a pé do backend (`rota_service.py`: 5 km/h). Usar a mesma
 *  conta evita que a tela diga "4 min a pé" onde o cálculo da duração
 *  total contou outra coisa. */
const METROS_POR_MINUTO_A_PE = 5000 / 60;

export function minutosAPe(metros: number): number {
  if (metros <= 0) return 0;
  return Math.max(1, Math.round(metros / METROS_POR_MINUTO_A_PE));
}

/**
 * US #159 — "tempo_real"/"parcial" têm ao menos a 1ª perna medida a partir
 * de um ônibus real; "teorica" (ou backend antigo, sem o campo) continua
 * mostrando a duração por velocidade média de sempre.
 */
export function duracaoDaOpcao(opcao: OpcaoViagem): { minutos: number; aoVivo: boolean } {
  const aoVivo = Boolean(
    opcao.tipo_estimativa && opcao.tipo_estimativa !== "teorica" && opcao.duracao_real_min != null
  );
  const bruto = aoVivo ? opcao.duracao_real_min! : opcao.duracao_estimada_min;
  return { minutos: Math.round(bruto), aoVivo };
}

export type Destaque = "mais_rapida" | "menos_baldeacoes" | "menos_caminhada";

export const ROTULO_DESTAQUE: Record<Destaque, string> = {
  mais_rapida: "Mais rápida",
  menos_baldeacoes: "Menos baldeações",
  menos_caminhada: "Menos caminhada",
};

/**
 * Para cada opção, em quais critérios ela é a melhor. Só destaca quando há
 * mais de uma opção E um único vencedor no critério: com empate, ou com uma
 * opção só, o rótulo não ajudaria a escolher — e "a menos que as outras"
 * mentiria sobre um empate. A caminhada é comparada em minutos, então uma
 * diferença de poucos metros conta como empate.
 */
export function destaquesDasOpcoes(opcoes: OpcaoViagem[]): Destaque[][] {
  const resultado: Destaque[][] = opcoes.map(() => []);
  if (opcoes.length < 2) return resultado;

  const criterios: [Destaque, (o: OpcaoViagem) => number][] = [
    ["mais_rapida", (o) => duracaoDaOpcao(o).minutos],
    ["menos_baldeacoes", (o) => o.baldeacoes],
    ["menos_caminhada", (o) => minutosAPe(o.caminhada_metros)],
  ];

  for (const [destaque, valor] of criterios) {
    const valores = opcoes.map(valor);
    const melhor = Math.min(...valores);
    const vencedoras = valores.flatMap((v, i) => (v === melhor ? [i] : []));
    if (vencedoras.length === 1) resultado[vencedoras[0]].push(destaque);
  }
  return resultado;
}

/** Um passo da linha do tempo do detalhe da opção. */
export type Passo =
  | { tipo: "caminhar"; chave: string; metros: number }
  | { tipo: "embarcar"; chave: string; perna: PernaViagem; numeroDoPasso: number }
  | { tipo: "viajar"; chave: string; perna: PernaViagem }
  | { tipo: "descer"; chave: string; perna: PernaViagem }
  | { tipo: "baldear"; chave: string; metros: number; para: string };

/**
 * Monta, na ordem em que a pessoa vive a viagem: caminhar → embarcar →
 * viajar → descer → (baldear → embarcar → …) → caminhar.
 *
 * Caminhada na baldeação = desembarque da perna + embarque da seguinte: é a
 * mesma soma que o backend usa para a caminhada total da opção
 * (`rota_service.caminhada_metros`), então nada aqui é inventado.
 *
 * `numeroDoPasso` é o número do marcador no mapa (1 = embarque inicial,
 * 2 = 1ª baldeação…), pra tela e mapa dizerem o mesmo.
 */
export function passosDaOpcao(opcao: OpcaoViagem): Passo[] {
  const { pernas } = opcao;
  const passos: Passo[] = [];

  pernas.forEach((perna, i) => {
    const chave = `${perna.numero}-${perna.sentido}-${i}`;

    if (i === 0 && perna.embarque.caminhada_metros > 0) {
      passos.push({ tipo: "caminhar", chave: `${chave}-ini`, metros: perna.embarque.caminhada_metros });
    }

    passos.push({ tipo: "embarcar", chave: `${chave}-emb`, perna, numeroDoPasso: i + 1 });
    passos.push({ tipo: "viajar", chave: `${chave}-via`, perna });
    passos.push({ tipo: "descer", chave: `${chave}-des`, perna });

    const proxima = pernas[i + 1];
    if (proxima) {
      passos.push({
        tipo: "baldear",
        chave: `${chave}-bal`,
        metros: perna.desembarque.caminhada_metros + proxima.embarque.caminhada_metros,
        para: proxima.numero,
      });
    } else if (perna.desembarque.caminhada_metros > 0) {
      passos.push({ tipo: "caminhar", chave: `${chave}-fim`, metros: perna.desembarque.caminhada_metros });
    }
  });

  return passos;
}
