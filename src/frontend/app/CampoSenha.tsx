"use client";

import { useState } from "react";

/**
 * Campo de senha da identidade v3: caixa branca de 56px com o botão de
 * mostrar/ocultar à direita e, opcionalmente, o medidor de força abaixo.
 *
 * O medidor é orientação, não validação: quem decide se a senha é aceita
 * continua sendo a regra da tela de cadastro (mínimo de 8 caracteres, com
 * letra e número). Por isso um "Fraca" aqui não bloqueia o envio.
 */
const CRITERIOS: { rotulo: string; atende: (senha: string) => boolean }[] = [
  { rotulo: "Pelo menos 8 caracteres", atende: (s) => s.length >= 8 },
  { rotulo: "Uma letra maiúscula", atende: (s) => /[A-ZÀ-Þ]/.test(s) },
  { rotulo: "Um número", atende: (s) => /[0-9]/.test(s) },
  { rotulo: "Um símbolo (!@#$)", atende: (s) => /[^A-Za-z0-9]/.test(s) },
];

const ROTULOS_FORCA = ["Digite uma senha", "Fraca", "Razoável", "Boa", "Forte"];

interface CampoSenhaProps {
  id: string;
  label: string;
  value: string;
  onChange: (valor: string) => void;
  erro?: string;
  autoComplete?: string;
  /** Exibe o medidor de força e a lista de critérios (tela de cadastro). */
  medidorForca?: boolean;
}

export default function CampoSenha({
  id,
  label,
  value,
  onChange,
  erro,
  autoComplete,
  medidorForca = false,
}: CampoSenhaProps) {
  const [visivel, setVisivel] = useState(false);

  const criterios = CRITERIOS.map((c) => ({
    rotulo: c.rotulo,
    ok: c.atende(value),
  }));
  const nivel = criterios.filter((c) => c.ok).length;

  return (
    <div className="campo">
      <label htmlFor={id}>{label}</label>

      <div className="campo-senha">
        <input
          id={id}
          type={visivel ? "text" : "password"}
          value={value}
          autoComplete={autoComplete}
          onChange={(e) => onChange(e.target.value)}
        />
        <button
          type="button"
          className="botao-olho"
          onClick={() => setVisivel((v) => !v)}
          aria-label={visivel ? "Ocultar senha" : "Mostrar senha"}
        >
          <svg
            width="19"
            height="19"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            aria-hidden="true"
          >
            <path d="M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12Z" />
            <circle cx="12" cy="12" r="2.8" />
            {!visivel && <path d="M4 20 20 4" />}
          </svg>
        </button>
      </div>

      {medidorForca && (
        <div className="forca-senha" data-nivel={nivel}>
          <div className="forca-barras" aria-hidden="true">
            {[1, 2, 3, 4].map((i) => (
              <span
                key={i}
                className={`forca-barra${nivel >= i ? " ativa" : ""}`}
              />
            ))}
          </div>
          <p className="forca-rotulo">{ROTULOS_FORCA[nivel]}</p>
          <ul className="forca-criterios">
            {criterios.map((c) => (
              <li key={c.rotulo} className={c.ok ? "ok" : undefined}>
                {c.rotulo}
              </li>
            ))}
          </ul>
        </div>
      )}

      {erro && <span className="erro-campo">{erro}</span>}
    </div>
  );
}
