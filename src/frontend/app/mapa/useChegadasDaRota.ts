import { useEffect, useState } from "react";
import {
  buscarChegadasDaRota,
  ChegadasDaPerna,
  PernaParaChegadas,
  PernaViagem,
} from "@/lib/api";
import { INTERVALO_CHEGADAS_MS } from "./useChegadasDaParada";

/**
 * O pedido ao backend a partir dos trechos da opção de rota, ou `null` quando
 * nenhum ponto tem código de parada (nada a perguntar: sem código não há
 * tempo, RN-09).
 */
export function pedidoDasPernas(
  pernas: PernaViagem[] | null | undefined
): PernaParaChegadas[] | null {
  if (!pernas || pernas.length === 0) return null;
  const pedido = pernas.map((p) => ({
    numero: p.numero,
    sentido: p.sentido,
    embarqueCodigo: p.embarque.parada_codigo ?? null,
    desembarqueCodigo: p.desembarque.parada_codigo ?? null,
  }));
  return pedido.some((p) => p.embarqueCodigo || p.desembarqueCodigo) ? pedido : null;
}

/**
 * Quando o ônibus de cada trecho da rota escolhida chega à parada de subir e
 * à de descer, atualizado enquanto a opção está selecionada. `pernas = null`
 * (nenhuma opção escolhida, ou sem códigos de parada) desliga tudo.
 *
 * O resultado vem alinhado, por índice, com `pernas`.
 *
 * Proteções que importam aqui (as mesmas de `useChegadasDaParada`):
 *  - resposta antiga não sobrescreve a nova: trocar de opção de rota, ou uma
 *    consulta lenta que termina depois da seguinte, não pode deixar tempos
 *    de outra rota na tela;
 *  - falha de rede não apaga o que já estava na tela — o dado de há 20 s
 *    ainda serve (quem está num ponto de ônibus costuma estar com sinal
 *    ruim). Trocar de opção, sim, limpa: o tempo antigo seria de outra rota.
 */
export function useChegadasDaRota(pernas: PernaViagem[] | null | undefined): {
  chegadas: ChegadasDaPerna[] | null;
} {
  const pedido = pedidoDasPernas(pernas);
  // A chave serializada evita reiniciar o polling a cada render: o array de
  // pernas é recriado sempre, o conteúdo do pedido quase nunca muda.
  const chave = pedido ? JSON.stringify(pedido) : null;
  const [chegadas, setChegadas] = useState<ChegadasDaPerna[] | null>(null);

  useEffect(() => {
    setChegadas(null);
    if (!chave) return;

    const pedidoAtual: PernaParaChegadas[] = JSON.parse(chave);
    let ativo = true;
    let pedidas = 0;
    let aplicada = 0;

    async function buscar() {
      const numero = ++pedidas;
      const resultado = await buscarChegadasDaRota(pedidoAtual);
      if (!ativo || numero < aplicada) return;
      // Resposta com outro tamanho não casa com as pernas: ignora em vez de
      // mostrar o tempo de um trecho no outro.
      if (resultado && resultado.pernas.length === pedidoAtual.length) {
        aplicada = numero;
        setChegadas(resultado.pernas);
      }
    }

    buscar();
    const intervalo = setInterval(buscar, INTERVALO_CHEGADAS_MS);

    return () => {
      ativo = false;
      clearInterval(intervalo);
    };
  }, [chave]);

  return { chegadas };
}
