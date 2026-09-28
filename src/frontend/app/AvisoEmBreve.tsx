"use client";

import { useEffect, useRef } from "react";

/**
 * Pop-up de "em breve" — usado em controles que existem no desenho da
 * interface mas cuja funcionalidade ainda não foi entregue.
 *
 * É a mesma convenção do selo "Em breve" da navegação do AppShell: o
 * controle aparece, porque faz parte da identidade da tela, mas diz com
 * clareza que ainda não funciona em vez de fingir que funciona.
 */
interface AvisoEmBreveProps {
  aberto: boolean;
  onFechar: () => void;
  titulo?: string;
  children: React.ReactNode;
}

export default function AvisoEmBreve({
  aberto,
  onFechar,
  titulo = "Em breve",
  children,
}: AvisoEmBreveProps) {
  const fecharRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!aberto) return;

    // Foco no botão de fechar: quem navega por teclado precisa cair
    // dentro do diálogo, e não continuar no fundo da página.
    fecharRef.current?.focus();

    function aoTeclar(e: KeyboardEvent) {
      if (e.key === "Escape") onFechar();
    }
    document.addEventListener("keydown", aoTeclar);
    return () => document.removeEventListener("keydown", aoTeclar);
  }, [aberto, onFechar]);

  if (!aberto) return null;

  return (
    <div className="modal-fundo" onClick={onFechar}>
      <div
        className="modal-caixa"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-titulo"
        onClick={(e) => e.stopPropagation()}
      >
        <span className="modal-selo">Em breve</span>
        <h2 id="modal-titulo">{titulo}</h2>
        <p>{children}</p>
        <button
          ref={fecharRef}
          type="button"
          className="botao-primario"
          onClick={onFechar}
        >
          Entendi
        </button>
      </div>
    </div>
  );
}
