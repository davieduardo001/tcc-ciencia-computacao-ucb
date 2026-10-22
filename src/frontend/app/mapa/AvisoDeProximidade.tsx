"use client";

import { BellRing } from "lucide-react";
import { useViagem } from "./ViagemContext";

/**
 * Aviso "seu ônibus está chegando" (US #172), por cima de qualquer tela.
 *
 * Mora no AppShell, e não na faixa do mapa, porque quem está em viagem pode
 * estar em outra tela (Rotas Salvas, Configurações) e precisa ser avisado do
 * mesmo jeito. Fica fixo no topo, sem empurrar nada.
 *
 * Só aparece enquanto o app está aberto: é entrega por consulta, e com a tela
 * bloqueada só push de verdade chegaria.
 *
 * O ETA do momento do disparo não é exibido: ele envelhece, e "chega em 3 min"
 * lido dez minutos depois seria errado. O aviso diz só o que continua
 * verdadeiro — o ônibus se aproxima da parada.
 */
export default function AvisoDeProximidade() {
  const { avisoProximidade, dispensarAviso } = useViagem();

  if (!avisoProximidade) return null;

  const parada = avisoProximidade.paradaNome?.trim() || "a sua parada";

  return (
    <div className="ms-aviso-proximidade" role="alert">
      <BellRing size={22} aria-hidden="true" />
      <p className="ms-aviso-proximidade-texto">
        <strong>Seu ônibus está chegando</strong>
        <span>
          Ele se aproxima de {parada}. Prepare-se para descer.
        </span>
      </p>
      <button type="button" className="ms-aviso-proximidade-ok" onClick={dispensarAviso}>
        Entendi
      </button>
    </div>
  );
}
