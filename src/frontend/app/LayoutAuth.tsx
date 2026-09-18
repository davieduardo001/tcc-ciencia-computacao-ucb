import Image from "next/image";
import AbasAuth from "./AbasAuth";

/**
 * Moldura das telas de autenticação, portada do protótipo v3.
 *
 * Duas partes: o herói escuro (gradiente radial, três faixas diagonais,
 * marca d'água do símbolo, malha de pontos) e a folha clara que sobe por
 * cima dele. A borda de cima da folha é uma curva desenhada em SVG, e não
 * um border-radius — o protótipo tem uma onda assimétrica, mais alta à
 * esquerda, que um raio de canto não reproduz.
 */
interface LayoutAuthProps {
  ativa: "login" | "cadastro";
  /** Título do herói. A quebra de linha é preservada (white-space: pre-line). */
  titulo: string;
  children: React.ReactNode;
}

export default function LayoutAuth({
  ativa,
  titulo,
  children,
}: LayoutAuthProps) {
  return (
    <div className="auth">
      <div className="auth-heroi">
        <div className="auth-fundo" aria-hidden="true">
          <span className="auth-faixa auth-faixa-teal" />
          <span className="auth-faixa auth-faixa-branca" />
          <span className="auth-faixa auth-faixa-coral" />
          <Image
            className="auth-marca-dagua"
            src="/movecity-marca.svg"
            alt=""
            width={290}
            height={330}
            unoptimized
            priority
          />
          <span className="auth-malha" />
        </div>

        <div className="auth-marca">
          <span className="auth-marca-simbolo">
            <Image
              src="/movecity-marca.svg"
              alt=""
              width={32}
              height={32}
              unoptimized
              priority
            />
          </span>
          <span className="auth-marca-texto">
            <strong>MoveCity</strong>
            <small>Mobilidade DF</small>
          </span>
        </div>

        <div className="auth-copy">
          <span className="auth-tracos" aria-hidden="true">
            <i />
            <i />
            <i />
          </span>
          <h1>{titulo}</h1>
        </div>
      </div>

      <div className="auth-folha">
        <svg
          className="auth-curva"
          viewBox="0 0 392 62"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <path d="M0 62 L0 30 C 70 6, 132 0, 196 12 C 268 26, 322 30, 392 6 L392 62 Z" />
        </svg>

        <div className="auth-conteudo">
          <AbasAuth ativa={ativa} />
          {children}
          <p className="auth-assinatura">MoveCity — TCC Grupo Segurança UCB</p>
        </div>
      </div>
    </div>
  );
}
