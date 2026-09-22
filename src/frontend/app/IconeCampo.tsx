/**
 * Ícones que ficam dentro dos campos das telas de autenticação.
 *
 * Herdam a cor do campo via `currentColor`: cinza quando vazio, teal
 * quando o campo está em foco ou preenchido — o mesmo comportamento da
 * borda, definido em globals.css.
 */
export type TipoIcone = "email" | "pessoa" | "cadeado";

export default function IconeCampo({ tipo }: { tipo: TipoIcone }) {
  return (
    <svg
      className="campo-icone"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      aria-hidden="true"
    >
      {tipo === "email" && (
        <>
          <rect x="2.5" y="5" width="19" height="14" rx="3" />
          <path d="M3 7l9 6 9-6" />
        </>
      )}
      {tipo === "pessoa" && (
        <>
          <circle cx="12" cy="8" r="4" />
          <path d="M4.5 20a7.5 7.5 0 0115 0" />
        </>
      )}
      {tipo === "cadeado" && (
        <>
          <rect x="4" y="10" width="16" height="11" rx="3" />
          <path d="M8 10V7a4 4 0 118 0v3" />
        </>
      )}
    </svg>
  );
}
