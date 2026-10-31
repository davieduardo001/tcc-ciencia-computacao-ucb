"use client";

import { FormEvent, useEffect, useId, useState } from "react";
import { Clock, LoaderCircle, SearchX } from "lucide-react";
import {
  OpcaoPlanejada,
  planejarViagem,
  PlanoViagem,
  TipoPlano,
} from "@/lib/api";
import BadgeLinha from "./BadgeLinha";

/**
 * US #115 — "Planejar por horário": sair às X ou chegar até X.
 *
 * Fica recolhido por padrão para não competir com a lista de opções da
 * US #20; só aparece com origem e destino escolhidos. O horário de
 * passagem em cada parada é estimado (saída da tabela + tempo de
 * percurso proporcional) e a tela diz isso.
 */

const FUSO = "America/Sao_Paulo";

interface Ponto {
  lat: number;
  lng: number;
}

interface PlanoPorHorarioProps {
  origem: Ponto;
  destino: Ponto;
}

export function horaDe(iso: string): string {
  return new Intl.DateTimeFormat("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: FUSO,
  }).format(new Date(iso));
}

export function duracaoEmTexto(minutos: number): string {
  if (minutos < 60) return `${minutos} min`;
  const horas = Math.floor(minutos / 60);
  const resto = minutos % 60;
  return resto === 0 ? `${horas} h` : `${horas} h ${resto} min`;
}

function agoraEmBrasilia(): { data: string; hora: string } {
  const partes = new Intl.DateTimeFormat("sv-SE", {
    timeZone: FUSO,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  })
    .format(new Date())
    .split(" ");
  return { data: partes[0], hora: partes[1] };
}

function OpcaoDoPlano({ opcao, tipo }: { opcao: OpcaoPlanejada; tipo: TipoPlano }) {
  return (
    <li className="plano-horario-opcao">
      <p className="plano-horario-resumo">
        <strong>
          {tipo === "chegada" ? "Saia às " : "Saindo às "}
          {horaDe(opcao.saida_casa)}
        </strong>{" "}
        · chega às <strong>{horaDe(opcao.chegada_destino)}</strong> ·{" "}
        {duracaoEmTexto(opcao.duracao_total_min)}
        {opcao.baldeacoes > 0 &&
          ` · ${opcao.baldeacoes} ${opcao.baldeacoes === 1 ? "baldeação" : "baldeações"}`}
      </p>
      <ol className="plano-horario-pernas">
        {opcao.pernas.map((perna, i) => (
          <li key={`${perna.numero}-${i}`}>
            {i > 0 && perna.espera_min > 0 && (
              <p className="plano-horario-espera">
                Espera de {perna.espera_min} min no ponto de troca
              </p>
            )}
            {i === 0 && perna.espera_min > 0 && (
              <p className="plano-horario-espera">
                Espera de {perna.espera_min} min no ponto de embarque
              </p>
            )}
            <p>
              <BadgeLinha numero={perna.numero} /> sobe às{" "}
              <strong>{horaDe(perna.embarca_em)}</strong> em {perna.embarque.parada_nome}
              <br />
              desce às <strong>{horaDe(perna.desembarca_em)}</strong> em{" "}
              {perna.desembarque.parada_nome}
            </p>
          </li>
        ))}
      </ol>
    </li>
  );
}

export default function PlanoPorHorario({ origem, destino }: PlanoPorHorarioProps) {
  const idBase = useId();
  const [aberto, setAberto] = useState(false);
  const [tipo, setTipo] = useState<TipoPlano>("saida");
  const [horario, setHorario] = useState("");
  const [data, setData] = useState("");
  const [carregando, setCarregando] = useState(false);
  const [plano, setPlano] = useState<PlanoViagem | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  // Preenche com "agora" ao abrir; depois o usuário mexe.
  useEffect(() => {
    if (aberto && !horario) {
      const agora = agoraEmBrasilia();
      setHorario(agora.hora);
      setData(agora.data);
    }
  }, [aberto, horario]);

  // Origem ou destino mudou: o plano antigo não vale mais.
  useEffect(() => {
    setPlano(null);
    setErro(null);
  }, [origem.lat, origem.lng, destino.lat, destino.lng]);

  async function aoPlanejar(evento: FormEvent) {
    evento.preventDefault();
    if (!horario) return;
    setCarregando(true);
    setErro(null);
    setPlano(null);
    try {
      setPlano(await planejarViagem(origem, destino, tipo, horario, data || undefined));
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Não foi possível planejar a viagem.");
    } finally {
      setCarregando(false);
    }
  }

  return (
    <section className="plano-horario" aria-label="Planejar por horário">
      <button
        type="button"
        className="plano-horario-abrir"
        aria-expanded={aberto}
        aria-controls={`${idBase}-corpo`}
        onClick={() => setAberto((v) => !v)}
      >
        <Clock size={15} aria-hidden="true" /> Planejar por horário
      </button>

      {aberto && (
        <div id={`${idBase}-corpo`} className="plano-horario-corpo">
          <form onSubmit={aoPlanejar} className="plano-horario-form">
            <fieldset className="plano-horario-tipo">
              <legend className="sr-only">Tipo de horário</legend>
              <label>
                <input
                  type="radio"
                  name={`${idBase}-tipo`}
                  checked={tipo === "saida"}
                  onChange={() => setTipo("saida")}
                />
                Sair às
              </label>
              <label>
                <input
                  type="radio"
                  name={`${idBase}-tipo`}
                  checked={tipo === "chegada"}
                  onChange={() => setTipo("chegada")}
                />
                Chegar até
              </label>
            </fieldset>

            <label className="plano-horario-campo">
              <span>Horário</span>
              <input
                type="time"
                value={horario}
                onChange={(e) => setHorario(e.target.value)}
                required
              />
            </label>
            <label className="plano-horario-campo">
              <span>Dia</span>
              <input type="date" value={data} onChange={(e) => setData(e.target.value)} />
            </label>

            <button type="submit" className="plan-acao-secundaria" disabled={carregando || !horario}>
              {carregando ? (
                <LoaderCircle size={14} className="plan-girando" aria-hidden="true" />
              ) : null}
              {carregando ? "Calculando..." : "Planejar"}
            </button>
          </form>

          {erro && (
            <p className="plan-erro" role="alert">
              {erro}
            </p>
          )}

          {plano && plano.opcoes.length === 0 && (
            <div className="plano-horario-vazio" role="status">
              <SearchX size={20} aria-hidden="true" />
              <p>{plano.mensagem ?? "Nenhuma opção neste horário."}</p>
            </div>
          )}

          {plano && plano.opcoes.length > 0 && (
            <>
              <ul className="plano-horario-lista">
                {plano.opcoes.map((opcao, i) => (
                  <OpcaoDoPlano key={i} opcao={opcao} tipo={plano.tipo} />
                ))}
              </ul>
              <p className="plan-ressalva">
                Horários <strong>estimados</strong>: saída do terminal pela tabela da SEMOB mais o
                tempo de percurso até a parada. O ônibus real pode adiantar ou atrasar. Feriados
                não são considerados.
              </p>
            </>
          )}
        </div>
      )}
    </section>
  );
}
