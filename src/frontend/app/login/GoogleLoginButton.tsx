"use client";

import { useEffect, useRef } from "react";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: { credential: string }) => void;
          }) => void;
          renderButton: (
            parent: HTMLElement,
            options: Record<string, unknown>
          ) => void;
        };
      };
    };
  }
}

const GOOGLE_SCRIPT_SRC = "https://accounts.google.com/gsi/client";

interface GoogleLoginButtonProps {
  clientId?: string;
  onCredential: (idToken: string) => void;
  disabled?: boolean;
}

export default function GoogleLoginButton({
  clientId,
  onCredential,
  disabled,
}: GoogleLoginButtonProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!clientId || disabled || !containerRef.current) {
      return;
    }

    function iniciarBotao() {
      if (!window.google || !containerRef.current) return;
      window.google.accounts.id.initialize({
        client_id: clientId as string,
        callback: (response) => onCredential(response.credential),
      });
      window.google.accounts.id.renderButton(containerRef.current, {
        theme: "outline",
        size: "large",
        width: 320,
        text: "continue_with",
        locale: "pt-BR",
      });
    }

    if (window.google) {
      iniciarBotao();
      return;
    }

    const script = document.createElement("script");
    script.src = GOOGLE_SCRIPT_SRC;
    script.async = true;
    script.defer = true;
    script.onload = iniciarBotao;
    document.head.appendChild(script);

    return () => {
      script.onload = null;
    };
  }, [clientId, disabled, onCredential]);

  if (!clientId) {
    return null;
  }

  return (
    <div
      ref={containerRef}
      className="google-login-button"
      data-testid="google-login-button"
    />
  );
}
