"use client";

import { useEffect } from "react";

/**
 * Registra o service worker que torna o app instalável.
 *
 * Só em produção: em desenvolvimento, um worker cacheando a casca briga
 * com o hot reload do Next e faz o navegador servir código velho, o que
 * rende meia hora de depuração de um bug que não existe.
 *
 * Falha em silêncio de propósito. Se o registro não der certo — modo
 * anônimo, storage bloqueado, navegador sem suporte —, o site continua
 * funcionando normalmente; só não fica instalável. Não há nada que o
 * usuário possa fazer a respeito, então não há o que avisar.
 */
export default function RegistrarServiceWorker() {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production") return;
    if (!("serviceWorker" in navigator)) return;

    navigator.serviceWorker.register("/sw.js").catch(() => {});
  }, []);

  return null;
}
