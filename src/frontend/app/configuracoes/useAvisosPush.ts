"use client";

import { useCallback, useEffect, useState } from "react";
import { PushError } from "@/lib/api";
import { ativarPush, desativarPush, EstadoPush, lerEstadoPush } from "@/lib/push";

/**
 * Estado e ações do controle "Avisos com a tela bloqueada" (US #172).
 *
 * Ao montar, só LÊ o estado: nada de pedir permissão. A permissão do
 * navegador só aparece depois que a pessoa toca em "Ativar" (`ativar`).
 */
export function useAvisosPush() {
  const [estado, setEstado] = useState<EstadoPush>({ tipo: "carregando" });
  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    let ativo = true;
    lerEstadoPush()
      .then((lido) => {
        if (ativo) setEstado(lido);
      })
      .catch(() => {
        if (ativo) setEstado({ tipo: "nao-suportado" });
      });
    return () => {
      ativo = false;
    };
  }, []);

  const ativar = useCallback(async () => {
    setOcupado(true);
    setErro(null);
    try {
      // `ativarPush` pede a permissão como PRIMEIRA coisa assíncrona: este
      // handler precisa chegar nela ainda dentro do gesto do clique.
      setEstado(await ativarPush());
    } catch (falha) {
      setErro(
        falha instanceof PushError
          ? falha.message
          : "Não foi possível ativar os avisos. Tente novamente."
      );
    } finally {
      setOcupado(false);
    }
  }, []);

  const desativar = useCallback(async () => {
    setOcupado(true);
    setErro(null);
    try {
      setEstado(await desativarPush());
    } catch {
      setErro("Não foi possível desativar os avisos. Tente novamente.");
    } finally {
      setOcupado(false);
    }
  }, []);

  return { estado, ocupado, erro, ativar, desativar };
}

/** O que a tela diz em cada estado, e se mostra o botão. */
export const TEXTOS_AVISOS_PUSH: Record<
  EstadoPush["tipo"],
  { descricao: string; botao: "ativar" | "desativar" | null }
> = {
  carregando: { descricao: "Verificando este aparelho...", botao: null },
  "nao-suportado": {
    descricao: "Este navegador não permite avisos com a tela bloqueada.",
    botao: null,
  },
  "ios-instalar": {
    descricao:
      "No iPhone, para receber avisos com a tela bloqueada é preciso instalar o Movecity: toque em Compartilhar e depois em “Adicionar à Tela de Início”. Abra o app instalado e volte aqui.",
    botao: null,
  },
  indisponivel: {
    descricao: "Avisos com a tela bloqueada não estão disponíveis no momento.",
    botao: null,
  },
  negado: {
    descricao:
      "As notificações do Movecity estão bloqueadas neste navegador. Para ativar, libere-as nas configurações do site (ícone ao lado do endereço) e volte aqui.",
    botao: null,
  },
  desativado: {
    descricao: "Receba o aviso de que sua parada está chegando, mesmo com o app fechado.",
    botao: "ativar",
  },
  ativo: {
    descricao: "Ativo neste aparelho. Você será avisado quando sua parada estiver chegando.",
    botao: "desativar",
  },
};
