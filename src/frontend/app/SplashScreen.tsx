"use client";

import { useEffect, useState } from "react";
import "./splash.css";

// Timings do protótipo v3: grade entra em ~0.9s, o traçado desenha em 1.5s
// (começando em 0.25s), o "wipe" que revela o app começa em 2.1s e dura
// 0.5s. Depois disso o componente desmonta — nada fica retendo pointer
// events nem re-renderizando à toa.
const DURACAO_TOTAL_MS = 2600;

export default function SplashScreen() {
  const [visivel, setVisivel] = useState(true);
  const [saindo, setSaindo] = useState(false);

  useEffect(() => {
    // Quem pediu menos movimento não deveria ver 2.6s de grade animada e
    // traçado se desenhando — a splash já cumpriu a função (nome do app na
    // tela) no primeiro frame.
    const prefereMenosMovimento = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;
    if (prefereMenosMovimento) {
      setVisivel(false);
      return;
    }

    const timerSaida = setTimeout(() => setSaindo(true), DURACAO_TOTAL_MS - 500);
    const timerFim = setTimeout(() => setVisivel(false), DURACAO_TOTAL_MS);
    return () => {
      clearTimeout(timerSaida);
      clearTimeout(timerFim);
    };
  }, []);

  if (!visivel) return null;

  return (
    <div className={`splash${saindo ? " splash-saindo" : ""}`} aria-hidden="true">
      <div className="splash-grade">
        <span className="splash-linha-v" style={{ left: "16%", animationDelay: "0.05s" }} />
        <span className="splash-linha-v" style={{ left: "41%", animationDelay: "0.16s" }} />
        <span className="splash-linha-v" style={{ left: "69%", animationDelay: "0.27s" }} />
        <span className="splash-linha-v" style={{ left: "88%", animationDelay: "0.36s" }} />
        <span className="splash-linha-h" style={{ top: "22%", animationDelay: "0.1s" }} />
        <span className="splash-linha-h" style={{ top: "48%", animationDelay: "0.22s" }} />
        <span className="splash-linha-h" style={{ top: "72%", animationDelay: "0.32s" }} />
      </div>

      <svg
        className="splash-tracado"
        viewBox="0 0 392 824"
        preserveAspectRatio="xMidYMid meet"
      >
        <path
          className="splash-tracado-halo"
          d="M42 806 C 96 700, 60 610, 120 540 S 236 470, 196 386"
        />
        <path
          className="splash-tracado-linha"
          d="M42 806 C 96 700, 60 610, 120 540 S 236 470, 196 386"
        />
        <g className="splash-marcador">
          <animateMotion
            dur="1.5s"
            begin="0.25s"
            fill="freeze"
            keyPoints="0;1"
            keyTimes="0;1"
            calcMode="spline"
            keySplines=".4 0 .2 1"
            path="M42 806 C 96 700, 60 610, 120 540 S 236 470, 196 386"
          />
          <circle r="21" fill="#0e2a3f" stroke="#4fd6c7" strokeWidth="3" />
          <g
            transform="translate(-11,-11) scale(.92)"
            fill="none"
            stroke="#4fd6c7"
            strokeWidth="2.2"
            strokeLinecap="round"
          >
            <rect x="4" y="3" width="16" height="14" rx="3" />
            <path d="M4 11h16M7 21l2-3M17 21l-2-3" />
          </g>
        </g>
      </svg>

      <div className="splash-marca">
        <strong>Movecity</strong>
        <small>Mobilidade DF</small>
      </div>
    </div>
  );
}
