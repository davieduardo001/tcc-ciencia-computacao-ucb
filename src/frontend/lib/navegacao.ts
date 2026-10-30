/**
 * Isola o acesso a window.location para que os testes possam trocar
 * por um dublê (jsdom não permite redefinir/espiar window.location).
 */
export function caminhoAtual(): string {
  return typeof window === "undefined" ? "" : window.location.pathname;
}

export function irPara(url: string): void {
  if (typeof window === "undefined") return;
  window.location.assign(url);
}
