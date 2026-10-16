import { CSSProperties } from "react";
import { corDaLinha } from "./corDaLinha";

/** Número da linha na cor dela no mapa (RN-14). O fundo continua escuro
 *  pra o número ser legível (14,8:1); a cor da linha vai na barra lateral. */
export default function BadgeLinha({ numero }: { numero: string }) {
  return (
    <em
      className="plan-badge-linha"
      style={{ "--cor-linha": corDaLinha(numero) } as CSSProperties}
    >
      {numero}
    </em>
  );
}
