"use client";

import { useState } from "react";
import IconeCampo from "./IconeCampo";

/**
 * Campo de senha do protótipo v3: cadeado à esquerda, botão de
 * mostrar/ocultar à direita e, na tela de cadastro, o medidor de força
 * (quatro barras com o rótulo à direita) e a lista de critérios.
 *
 * O medidor é orientação, não validação: quem decide se a senha é aceita
 * continua sendo a regra da tela de cadastro (8 caracteres, com letra e
 * número). Por isso um "Fraca" aqui não bloqueia o envio.
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
  placeholder?: string;
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
  placeholder,
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
    <div className="campo-bloco">
      <label className="apenas-leitor" htmlFor={id}>
        {label}
      </label>

      <div className={`campo-v3${value ? " preenchido" : ""}`}>
        <IconeCampo tipo="cadeado" />
        <input
          id={id}
          type={visivel ? "text" : "password"}
          value={value}
          placeholder={placeholder ?? label}
          autoComplete={autoComplete}
          onChange={(e) => onChange(e.target.value)}
        />
        <button
          type="button"
          className={`botao-olho${medidorForca ? " destacado" : ""}`}
          onClick={() => setVisivel((v) => !v)}
          aria-label={visivel ? "Ocultar senha" : "Mostrar senha"}
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.9"
            strokeLinecap="round"
            aria-hidden="true"
          >
            <path d="M2 12s3.8-6.5 10-6.5S22 12 22 12s-3.8 6.5-10 6.5S2 12 2 12z" />
            <circle cx="12" cy="12" r="2.8" />
            {!visivel && <path d="M4 20 20 4" />}
          </svg>
        </button>
      </div>

      {medidorForca && (
        <>
          <div className="forca-senha" data-nivel={nivel}>
            <span className="forca-barras" aria-hidden="true">
              {[1, 2, 3, 4].map((i) => (
                <i key={i} className={nivel >= i ? "ativa" : undefined} />
              ))}
            </span>
            <span className="forca-rotulo">{ROTULOS_FORCA[nivel]}</span>
          </div>

          <ul className="forca-criterios">
            {criterios.map((c) => (
              <li key={c.rotulo} className={c.ok ? "ok" : undefined}>
                <span className="forca-marca" aria-hidden="true">
                  <svg
                    width="10"
                    height="10"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="3.6"
                  >
                    <path d="M5 13l4.5 4.5L19 7" />
                  </svg>
                </span>
                {c.rotulo}
              </li>
            ))}
          </ul>
        </>
      )}

      {erro && <span className="erro-campo">{erro}</span>}
    </div>
  );
}
