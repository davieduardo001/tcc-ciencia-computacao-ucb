"use client";

import { useId, useState } from "react";
import { Bus, ChevronDown, Flag } from "lucide-react";
import { textoDaViagem } from "./textoDaViagem";
import { useViagem } from "./ViagemContext";

/**
 * Faixa de "Em viagem" no topo do mapa (US #171, RN-05).
 *
 * Tem altura fixa de propósito: o planejador (esquerda) e os painéis de
 * linha/parada (direita) descem exatamente essa altura quando ela aparece
 * (`--viagem-faixa` em mapa.css). Os detalhes — as paradas que faltam — abrem
 * num painel por cima, a pedido de quem toca, e não empurram nada.
 */
export default function FaixaDaViagem() {
  const { viagem, ocupado, encerrar } = useViagem();
  const [aberta, setAberta] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const idDetalhes = useId();

  if (!viagem) return null;

  const { principal, tom } = textoDaViagem(viagem);

  async function aoTocarCheguei() {
    setErro(null);
    const resultado = await encerrar();
    if (!resultado.ok) setErro(resultado.mensagem ?? "Não foi possível encerrar a viagem.");
  }

  return (
    <section className="mapa-viagem-faixa" aria-label="Viagem em andamento">
      <div className="mapa-viagem-linha">
        <span className="mapa-viagem-selo">
          <Bus size={16} aria-hidden="true" />
          <span>
            Em viagem · linha <strong>{viagem.numeroLinha}</strong>
          </span>
        </span>

        <span
          className={`mapa-viagem-texto${tom === "alerta" ? " alerta" : ""}`}
          role="status"
        >
          {principal}
        </span>

        <button
          type="button"
          className="mapa-viagem-detalhes-btn"
          // No celular o rótulo visível some (só sobra o ícone): sem o
          // aria-label o botão ficaria sem nome acessível. O nome contém o
          // rótulo visível ("Paradas"), como pede o WCAG 2.5.3.
          aria-label="Paradas que faltam"
          aria-expanded={aberta}
          aria-controls={idDetalhes}
          onClick={() => setAberta((v) => !v)}
        >
          <span className="mapa-viagem-detalhes-rotulo">Paradas</span>
          <ChevronDown size={16} aria-hidden="true" className={aberta ? "aberto" : ""} />
        </button>

        <button
          type="button"
          className="mapa-viagem-cheguei"
          onClick={aoTocarCheguei}
          disabled={ocupado}
        >
          <Flag size={15} aria-hidden="true" />
          Cheguei
        </button>
      </div>

      {erro && (
        <p className="mapa-viagem-erro" role="alert">
          {erro}
        </p>
      )}

      <div id={idDetalhes} className="mapa-viagem-detalhes" hidden={!aberta}>
        {viagem.paradasRestantes.length > 0 ? (
          <>
            <div className="mapa-painel-titulo">
              Até {viagem.destino?.nome ?? "o destino"}
            </div>
            <ol className="mapa-viagem-paradas">
              {viagem.paradasRestantes.map((parada) => (
                <li
                  key={parada.codigo}
                  className={parada.codigo === viagem.destino?.codigo ? "destino" : undefined}
                >
                  {parada.nome}
                  {parada.codigo === viagem.destino?.codigo && (
                    <span className="mapa-viagem-destino-rotulo"> · seu destino</span>
                  )}
                </li>
              ))}
            </ol>
          </>
        ) : (
          <p className="mapa-painel-dica">
            {viagem.destino?.ultrapassado
              ? "O ônibus já passou da sua parada de destino."
              : viagem.paradaDestinoCodigo
                ? "Não conseguimos listar as paradas até o seu destino agora."
                : "Para ver quantas paradas faltam, toque numa parada da linha no mapa e escolha “Descer nesta parada”."}
          </p>
        )}
      </div>
    </section>
  );
}
