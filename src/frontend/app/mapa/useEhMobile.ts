"use client";

import { useEffect, useState } from "react";

const QUERY_MOBILE = "(max-width: 920px)";

/**
 * `true` quando a tela é de celular (até 920 px), a mesma regra dos media
 * queries do mapa.css — assim o JS decide entre folha e coluna lateral sem
 * duplicar o corte. No servidor e antes de montar devolve `false`.
 */
export function useEhMobile(): boolean {
  const [mobile, setMobile] = useState(false);

  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const consulta = window.matchMedia(QUERY_MOBILE);
    setMobile(consulta.matches);
    const aoMudar = (evento: MediaQueryListEvent) => setMobile(evento.matches);
    consulta.addEventListener("change", aoMudar);
    return () => consulta.removeEventListener("change", aoMudar);
  }, []);

  return mobile;
}
