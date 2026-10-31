"use client";

import { useEffect, useRef } from "react";
import {
  enviarPosicaoColaborativa,
  ViagemError,
} from "@/lib/api";

/**
 * US #199 — intervalo de envio da posição do ônibus. 15 s assenta entre o
 * limite do backend (10 s) e o intervalo do feed da SEMOB (20 s): o
 * servidor limita de qualquer forma, então errar para mais é seguro.
 */
export const INTERVALO_ENVIO_POSICAO_MS = 15_000;

interface OpcoesUsePosicaoColaborativa {
  /** Id da viagem ATIVA do usuário; `null` = não está em viagem. */
  viagemId: string | null;
  /** Consentimento ainda de pé (contexto da viagem). */
  compartilhando: boolean;
  /** Última leitura do GPS; o hook envia SEM guardar nada. */
  lerPosicao: () => { lat: number; lng: number; precisaoM?: number } | null;
  /** Marca a revogação local quando o servidor recusa com 409. */
  revogarLocalmente: () => void;
}

/**
 * Envia, no ritmo do consentimento, a posição do ônibus em que a pessoa
 * está (não o perfil dela: cada envio é a leitura atual, efêmera).
 *
 * Proteções:
 *  - 409 do servidor = consentimento acabou de cair: para o ciclo na hora
 *    e marca a revogação local (a próxima releitura da viagem fecha a
 *    tela por si só);
 *  - 429 = ainda dentro do limite de taxa do servidor — sem erro na UI,
 *    o próximo ciclo resolve;
 *  - sem GPS ainda: não envia nada, tenta de novo no próximo ciclo.
 *
 * O efeito ASSUME que `compartilhando` já inclui "viagem ativa + consentimento
 * + não revogado"; desligar qualquer um deles desmonta o ciclo.
 */
export function usePosicaoColaborativa({
  viagemId,
  compartilhando,
  lerPosicao,
  revogarLocalmente,
}: OpcoesUsePosicaoColaborativa): void {
  const lerPosicaoRef = useRef(lerPosicao);
  lerPosicaoRef.current = lerPosicao;
  const revogarRef = useRef(revogarLocalmente);
  revogarRef.current = revogarLocalmente;

  useEffect(() => {
    if (!compartilhando || !viagemId) return;

    let parou = false;
    const id = viagemId;

    function enviar() {
      const posicao = lerPosicaoRef.current();
      if (parou || !posicao) return;
      void enviarPosicaoColaborativa(id, posicao).catch((erro: unknown) => {
        // 409 revoga (ou a viagem encerrou): para de martelar. 429 é o
        // servidor dizendo "devagar" — tentamos de novo no próximo ciclo.
        if (erro instanceof ViagemError && (erro.status === 409 || erro.status === 404)) {
          parou = true;
          revogarRef.current();
        }
      });
    }

    void enviar();
    const intervalo = setInterval(enviar, INTERVALO_ENVIO_POSICAO_MS);
    return () => {
      parou = true;
      clearInterval(intervalo);
    };
  }, [compartilhando, viagemId]);
}

/**
 * Reexportado para os testes: algumas recusas (409 de revogação) decidem o
 * ciclo sem depender do contexto. Função utilitária, sem estado.
 */
export function revogarSeConsentimentoCai(erro: unknown, revogar: () => void): boolean {
  if (erro instanceof ViagemError && (erro.status === 409 || erro.status === 404)) {
    revogar();
    return true;
  }
  return false;
}
