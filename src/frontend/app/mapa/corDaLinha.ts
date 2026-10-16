/**
 * Cor de cada linha, derivada do próprio número — a mesma no traçado do
 * mapa e no badge do resultado de rota (card #179, RN-14). Antes só o mapa
 * conhecia a cor: o painel pintava todo badge de mint, e a pessoa não
 * conseguia ligar "875A" ao traçado desenhado.
 *
 * Paleta pra diferenciar o trajeto por cor quando houver mais de uma linha
 * no mapa (PRD da US #17): a cor sai de um hash do número em vez de ser
 * fixa, então linhas simultâneas não colidem visualmente.
 */
export const CORES_TRAJETO = ["#1aa0ad", "#c9760a", "#2f72e8", "#1aa05a", "#d6453d"];

export function corDaLinha(numero: string): string {
  let hash = 0;
  for (let i = 0; i < numero.length; i++) {
    hash = (hash * 31 + numero.charCodeAt(i)) >>> 0;
  }
  return CORES_TRAJETO[hash % CORES_TRAJETO.length];
}
