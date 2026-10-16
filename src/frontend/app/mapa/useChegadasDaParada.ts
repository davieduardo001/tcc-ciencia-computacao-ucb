import { useEffect, useState } from "react";
import { buscarChegadasParada, ChegadasDaParada } from "@/lib/api";

/**
 * O feed de GPS é cacheado por 20 s no backend (ADR-04): consultar mais
 * seguido só devolveria o mesmo dado.
 */
export const INTERVALO_CHEGADAS_MS = 20_000;

/**
 * Chegadas das linhas numa parada, atualizadas enquanto o painel está
 * aberto. `codigo = null` (painel fechado, ou parada sem código) desliga
 * tudo.
 *
 * Duas proteções que importam aqui:
 *  - resposta antiga não sobrescreve a nova: clicar na parada A e logo na B
 *    não pode deixar as chegadas de A no painel da B (o mesmo problema que a
 *    #174 registra para o detalhe da parada);
 *  - falha de rede/404 não apaga o que já estava na tela — o dado de há 20 s
 *    ainda serve, e `calculadoEm` deixa o cliente saber a idade dele.
 */
export function useChegadasDaParada(codigo: string | null): {
  chegadas: ChegadasDaParada | null;
  carregando: boolean;
} {
  const [chegadas, setChegadas] = useState<ChegadasDaParada | null>(null);
  const [carregando, setCarregando] = useState(false);

  useEffect(() => {
    setChegadas(null);
    if (!codigo) {
      setCarregando(false);
      return;
    }

    let ativo = true;
    setCarregando(true);

    async function buscar() {
      const resultado = await buscarChegadasParada(codigo as string);
      if (!ativo) return;
      if (resultado) setChegadas(resultado);
      setCarregando(false);
    }

    buscar();
    const intervalo = setInterval(buscar, INTERVALO_CHEGADAS_MS);

    return () => {
      ativo = false;
      clearInterval(intervalo);
    };
  }, [codigo]);

  return { chegadas, carregando };
}
