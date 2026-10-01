"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { buscarUsuarioAtual } from "@/lib/api";

/**
 * `/` nunca foi pensada como a home do produto — é só o ponto que o
 * navegador abre por padrão. Quem já tem sessão vai pro mapa (mesmo
 * destino do `start_url` do manifesto do PWA); quem não tem vai pro
 * login. O painel de status dos serviços que morava aqui mudou pra
 * `/status` — ver app/status/page.tsx.
 */
export default function Home() {
  const router = useRouter();

  useEffect(() => {
    let ativo = true;

    buscarUsuarioAtual().then((usuario) => {
      if (!ativo) return;
      router.replace(usuario ? "/mapa" : "/login");
    });

    return () => {
      ativo = false;
    };
  }, [router]);

  return null;
}
