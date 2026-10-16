"use client";

import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  buscarViagemAtiva,
  definirDestinoDaViagem,
  EmbarquePayload,
  embarcarNoOnibus,
  encerrarViagem,
  ViagemAtiva,
  ViagemError,
} from "@/lib/api";

/**
 * A posição do ônibus vem do feed da SEMOB, cacheado por 20 s no backend
 * (ADR-04): perguntar mais seguido só devolveria o mesmo dado.
 */
export const INTERVALO_VIAGEM_MS = 20_000;

export interface ResultadoAcao {
  ok: boolean;
  /** Frase pronta para mostrar ao usuário quando `ok` é falso. */
  mensagem?: string;
}

interface EstadoViagem {
  /** `null` = Aguardando (RN-04). Preenchido = Em viagem. */
  viagem: ViagemAtiva | null;
  /** Só a primeira consulta, ao abrir a tela. */
  carregando: boolean;
  /** Uma ação (embarcar, destino, encerrar) está em andamento. */
  ocupado: boolean;
  embarcar: (dados: EmbarquePayload) => Promise<ResultadoAcao>;
  definirDestino: (codigo: string | null) => Promise<ResultadoAcao>;
  encerrar: () => Promise<ResultadoAcao>;
  /** `true` quando o servidor respondeu (com ou sem viagem). */
  atualizar: () => Promise<boolean>;
}

const SEM_PROVEDOR: EstadoViagem = {
  viagem: null,
  carregando: false,
  ocupado: false,
  embarcar: async () => ({ ok: false, mensagem: "Viagem indisponível nesta tela." }),
  definirDestino: async () => ({ ok: false, mensagem: "Viagem indisponível nesta tela." }),
  encerrar: async () => ({ ok: false, mensagem: "Viagem indisponível nesta tela." }),
  atualizar: async () => false,
};

// Sem Provider, a tela se comporta como "Aguardando" — assim componentes que
// leem o estado (o mapa) continuam funcionando fora do AppShell, como nos
// testes, sem precisar de um mock a mais.
const ViagemContext = createContext<EstadoViagem>(SEM_PROVEDOR);

export function useViagem(): EstadoViagem {
  return useContext(ViagemContext);
}

function mensagemDe(erro: unknown, padrao: string): string {
  return erro instanceof ViagemError ? erro.message : padrao;
}

/**
 * Estado de viagem do usuário (Aguardando × Em viagem), compartilhado entre
 * o indicador do AppShell e o mapa.
 *
 * Proteções que importam:
 *  - resposta antiga não sobrescreve a nova: uma consulta periódica que
 *    demora não pode "desencerrar" a viagem que o usuário acabou de
 *    encerrar (cada consulta tem um número de ordem);
 *  - falha de rede não derruba o estado: o dado de há 20 s ainda serve, e
 *    sumir com "Em viagem" por causa de um sinal ruim num ônibus em
 *    movimento seria pior que mostrar a posição anterior.
 */
export function ViagemProvider({ children }: { children: ReactNode }) {
  const [viagem, setViagem] = useState<ViagemAtiva | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [ocupado, setOcupado] = useState(false);
  const ordemRef = useRef(0);
  const montadoRef = useRef(true);

  useEffect(() => {
    montadoRef.current = true;
    return () => {
      montadoRef.current = false;
    };
  }, []);

  const atualizar = useCallback(async (): Promise<boolean> => {
    const minhaOrdem = ++ordemRef.current;
    const resultado = await buscarViagemAtiva();
    if (!montadoRef.current || minhaOrdem !== ordemRef.current) return false;
    if (!resultado.falhou) setViagem(resultado.viagem);
    setCarregando(false);
    return !resultado.falhou;
  }, []);

  useEffect(() => {
    atualizar();
  }, [atualizar]);

  // Só faz polling enquanto há viagem: quem está aguardando não precisa de
  // uma consulta a cada 20 s (ela muda por uma ação do próprio usuário).
  const idDaViagem = viagem?.id ?? null;
  useEffect(() => {
    if (!idDaViagem) return;
    const intervalo = setInterval(atualizar, INTERVALO_VIAGEM_MS);
    return () => clearInterval(intervalo);
  }, [idDaViagem, atualizar]);

  const executar = useCallback(
    async (
      acao: () => Promise<void>,
      padrao: string,
      sincronizarNoErro: number[] = []
    ): Promise<ResultadoAcao> => {
      setOcupado(true);
      try {
        await acao();
        // A ação já deu certo no servidor. Se a releitura falhar por um
        // soluço de rede, tenta mais uma vez antes de deixar a tela
        // contradizendo o que acabou de acontecer.
        if (!(await atualizar())) await atualizar();
        return { ok: true };
      } catch (erro) {
        // Ex.: 409 "já está em viagem" — a tela estava desatualizada.
        if (erro instanceof ViagemError && erro.status && sincronizarNoErro.includes(erro.status)) {
          await atualizar();
        }
        return { ok: false, mensagem: mensagemDe(erro, padrao) };
      } finally {
        if (montadoRef.current) setOcupado(false);
      }
    },
    [atualizar]
  );

  const embarcar = useCallback(
    (dados: EmbarquePayload) =>
      executar(
        () => embarcarNoOnibus(dados),
        "Não foi possível registrar o embarque. Tente novamente.",
        [409]
      ),
    [executar]
  );

  const definirDestino = useCallback(
    (codigo: string | null) => {
      if (!idDaViagem) {
        return Promise.resolve<ResultadoAcao>({ ok: false, mensagem: "Você não está em uma viagem." });
      }
      return executar(
        () => definirDestinoDaViagem(idDaViagem, codigo),
        "Não foi possível salvar o destino. Tente novamente.",
        [404, 409]
      );
    },
    [executar, idDaViagem]
  );

  const encerrar = useCallback(() => {
    if (!idDaViagem) return Promise.resolve<ResultadoAcao>({ ok: true });
    return executar(
      () => encerrarViagem(idDaViagem),
      "Não foi possível encerrar a viagem. Tente novamente."
    );
  }, [executar, idDaViagem]);

  const valor = useMemo<EstadoViagem>(
    () => ({ viagem, carregando, ocupado, embarcar, definirDestino, encerrar, atualizar }),
    [viagem, carregando, ocupado, embarcar, definirDestino, encerrar, atualizar]
  );

  return <ViagemContext.Provider value={valor}>{children}</ViagemContext.Provider>;
}
