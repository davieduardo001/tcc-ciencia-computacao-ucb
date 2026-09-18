"use client";

import IconeCampo, { TipoIcone } from "./IconeCampo";

/**
 * Campo de texto das telas de autenticação: ícone à esquerda, placeholder
 * no lugar do rótulo acima.
 *
 * O `<label>` continua existindo, só que visualmente oculto. Placeholder
 * não é rótulo acessível: some quando a pessoa digita e leitor de tela não
 * o anuncia de forma confiável.
 */
interface CampoTextoProps {
  id: string;
  label: string;
  icone: TipoIcone;
  value: string;
  onChange: (valor: string) => void;
  tipo?: "text" | "email";
  /** Texto do placeholder, quando difere do rótulo. */
  placeholder?: string;
  erro?: string;
  autoComplete?: string;
}

export default function CampoTexto({
  id,
  label,
  icone,
  value,
  onChange,
  tipo = "text",
  placeholder,
  erro,
  autoComplete,
}: CampoTextoProps) {
  return (
    <div className="campo-bloco">
      <label className="apenas-leitor" htmlFor={id}>
        {label}
      </label>

      <div className={`campo-v3${value ? " preenchido" : ""}`}>
        <IconeCampo tipo={icone} />
        <input
          id={id}
          type={tipo}
          value={value}
          placeholder={placeholder ?? label}
          autoComplete={autoComplete}
          onChange={(e) => onChange(e.target.value)}
        />
      </div>

      {erro && <span className="erro-campo">{erro}</span>}
    </div>
  );
}
