/**
 * Minutos como a pessoa lê: inteiros. O backend devolve 4,3 ("4.3 min") e
 * isso passa uma precisão que o dado não tem — a posição do ônibus tem
 * defasagem de segundos, a velocidade é uma média. Menos de 1 minuto vira
 * "menos de 1 min", e não um "0 min" que parece erro.
 */
export function formatarMinutos(minutos: number): string {
  const arredondado = Math.round(minutos);
  if (arredondado < 1) return "menos de 1 min";
  return `${arredondado} min`;
}

/** Mesma regra, sem a unidade — para a pílula do ônibus, que já a leva no rótulo. */
export function minutosInteiros(minutos: number): string {
  const arredondado = Math.round(minutos);
  return arredondado < 1 ? "<1" : String(arredondado);
}
