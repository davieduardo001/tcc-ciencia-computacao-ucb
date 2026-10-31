"use client";

import { useState } from "react";
import { ShieldQuestion, X } from "lucide-react";

/**
 * US #199, Cenário 1 — consentimento explícito, DESligado por padrão.
 *
 * O que a folha promete é literal, e é o que o backend guardará como prova
 * (a `versao` do texto): só com o meu "sim", a posição do ônibus em que
 * estou vai para outros passageiros por no máximo 2 minutos por leitura —
 * sem histórico, sem rastro no perfil do usuário (nenhuma coordenada é
 * gravada em banco) e revogável a qualquer momento.
 *
 * O texto aqui tem uma versão (`VERSAO_CONSENTIMENTO` em lib/api.ts): mudou
 * o texto, muda a versão — assim a prova guardada por embarque diz de fato
 * o que a pessoa leu.
 */
export const TEXTO_CONSENTIMENTO = [
  "Ao aceitar, a posição do ônibus em que você está (não a sua casa, não o seu percurso) pode ser usada por outros passageiros para ter estimativas de chegada quando o GPS oficial falha.",
  "Cada leitura vale no máximo 2 minutos; não guardamos histórico nem sua posição no seu perfil, e você pode parar a qualquer momento.",
].join(" ");

interface OperadorConsentimento {
  marcado: boolean;
  aoAlternar: (marcado: boolean) => void;
}

export default function ConsentimentoDePosicao({
  marcado,
  aoAlternar,
}: OperadorConsentimento) {
  const [aberto, setAberto] = useState(false);

  return (
    <div className="mapa-consentimento">
      <label className="mapa-consentimento-caixa">
        <input
          type="checkbox"
          checked={marcado}
          onChange={(e) => aoAlternar(e.target.checked)}
        />
        <span>Compartilhar a posição do ônibus com outros passageiros</span>
      </label>
      <button
        type="button"
        className="mapa-consentimento-mais"
        aria-expanded={aberto}
        onClick={() => setAberto((v) => !v)}
      >
        {aberto ? <X size={14} aria-hidden="true" /> : <ShieldQuestion size={14} aria-hidden="true" />}
        {aberto ? "Fechar" : "Saiba o que é compartilhado"}
      </button>
      {aberto && (
        <p className="mapa-consentimento-texto" role="note" aria-label="O que é compartilhado">
          {TEXTO_CONSENTIMENTO}
        </p>
      )}
    </div>
  );
}
