"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  ArrowUpDown,
  Bus,
  Crosshair,
  Footprints,
  LoaderCircle,
  MapPin,
  Repeat,
  Search,
  X,
} from "lucide-react";
import { buscarLugares, Lugar, OpcaoViagem } from "@/lib/api";

const DEBOUNCE_MS = 350;
const MIN_CARACTERES = 3;

export type Extremo = "origem" | "destino";

/** Ponto escolhido pelo usuário, venha de onde vier (busca, GPS ou mapa). */
export interface PontoEscolhido {
  nome: string;
  lat: number;
  lng: number;
}

interface PlanejadorViagemProps {
  origem: PontoEscolhido | null;
  destino: PontoEscolhido | null;
  onDefinir: (extremo: Extremo, ponto: PontoEscolhido | null) => void;
  onInverter: () => void;
  onBuscar: () => void;
  /** Ativa o modo "clique no mapa pra escolher este ponto". */
  onEscolherNoMapa: (extremo: Extremo) => void;
  escolhendoNoMapa: Extremo | null;
  onUsarMinhaLocalizacao: (extremo: Extremo) => void;
  temLocalizacao: boolean;
  opcoes: OpcaoViagem[] | null;
  opcaoSelecionada: number | null;
  onSelecionarOpcao: (indice: number) => void;
  calculando: boolean;
  erro: string | null;
  onFechar: () => void;
  /** US #16 — quantos ônibus estão rodando cada linha do itinerário,
   * indexado por número da linha. */
  veiculosPorLinha: Record<string, number>;
  /** Falso enquanto a primeira consulta de posição não voltou — evita
   * dizer "nenhum ônibus" antes de ter perguntado. */
  rastreando: boolean;
}

function CampoLugar({
  extremo,
  rotulo,
  placeholder,
  valor,
  onDefinir,
  onEscolherNoMapa,
  escolhendo,
  onUsarMinhaLocalizacao,
  temLocalizacao,
}: {
  extremo: Extremo;
  rotulo: string;
  placeholder: string;
  valor: PontoEscolhido | null;
  onDefinir: (extremo: Extremo, ponto: PontoEscolhido | null) => void;
  onEscolherNoMapa: (extremo: Extremo) => void;
  escolhendo: boolean;
  onUsarMinhaLocalizacao: (extremo: Extremo) => void;
  temLocalizacao: boolean;
}) {
  const [texto, setTexto] = useState("");
  const [sugestoes, setSugestoes] = useState<Lugar[]>([]);
  const [abertas, setAbertas] = useState(false);
  const [buscando, setBuscando] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Mesmo problema do autocomplete de linhas: uma busca antiga que
  // demore mais pra responder sobrescreveria a atual.
  const sequenciaRef = useRef(0);

  // Quando o ponto é definido por fora (GPS, clique no mapa, inversão),
  // o campo precisa refletir isso.
  useEffect(() => {
    setTexto(valor?.nome ?? "");
  }, [valor]);

  const digitar = useCallback(
    (novo: string) => {
      setTexto(novo);
      if (debounceRef.current) clearTimeout(debounceRef.current);

      const sequencia = ++sequenciaRef.current;

      if (novo.trim().length < MIN_CARACTERES) {
        setSugestoes([]);
        setBuscando(false);
        return;
      }

      setBuscando(true);
      debounceRef.current = setTimeout(async () => {
        const resultado = await buscarLugares(novo);
        if (sequencia !== sequenciaRef.current) return;
        setSugestoes(resultado);
        setBuscando(false);
        setAbertas(true);
      }, DEBOUNCE_MS);
    },
    []
  );

  return (
    <div className={`plan-campo${escolhendo ? " escolhendo" : ""}`}>
      <label className="plan-campo-rotulo" htmlFor={`plan-${extremo}`}>
        <span className={`plan-bolinha ${extremo}`} aria-hidden="true" />
        {rotulo}
      </label>

      <div className="plan-campo-linha">
        <input
          id={`plan-${extremo}`}
          className="plan-input"
          value={texto}
          placeholder={escolhendo ? "Toque no mapa..." : placeholder}
          autoComplete="off"
          onChange={(e) => digitar(e.target.value)}
          onFocus={() => setAbertas(true)}
          onBlur={() => setTimeout(() => setAbertas(false), 150)}
        />

        {texto && (
          <button
            type="button"
            className="plan-botao-campo"
            title="Limpar"
            onClick={() => {
              setTexto("");
              setSugestoes([]);
              onDefinir(extremo, null);
            }}
          >
            <X size={14} />
          </button>
        )}

        {buscando && <LoaderCircle size={14} className="plan-girando" />}
      </div>

      <div className="plan-atalhos">
        <button
          type="button"
          className="plan-atalho"
          onClick={() => onUsarMinhaLocalizacao(extremo)}
          disabled={!temLocalizacao}
          title={
            temLocalizacao
              ? "Usar minha localização"
              : "Localização indisponível — permita o acesso no navegador"
          }
        >
          <Crosshair size={13} /> Minha localização
        </button>
        <button
          type="button"
          className={`plan-atalho${escolhendo ? " ativo" : ""}`}
          onClick={() => onEscolherNoMapa(extremo)}
        >
          <MapPin size={13} /> {escolhendo ? "Toque no mapa" : "Escolher no mapa"}
        </button>
      </div>

      {abertas && sugestoes.length > 0 && (
        <ul className="plan-sugestoes" role="listbox">
          {sugestoes.map((lugar, indice) => (
            <li key={`${lugar.lat}-${lugar.lng}-${indice}`}>
              <button
                type="button"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => {
                  onDefinir(extremo, {
                    nome: lugar.nome,
                    lat: lugar.lat,
                    lng: lugar.lng,
                  });
                  setSugestoes([]);
                  setAbertas(false);
                }}
              >
                <strong>{lugar.nome}</strong>
                <span>{lugar.endereco}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function rotuloDoPonto(nome: string, lat: number, lng: number): string {
  // 582 dos 7.142 abrigos do SEMOB vêm sem nome utilizável na fonte
  // (só o CEP). Nesses casos o backend manda string vazia de propósito.
  return nome || `Ponto em ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
}

function ResumoOpcao({ opcao }: { opcao: OpcaoViagem }) {
  return (
    <div className="plan-opcao-resumo">
      <div className="plan-opcao-linhas">
        {opcao.pernas.map((perna, indice) => (
          <span key={`${perna.numero}-${perna.sentido}-${indice}`}>
            {indice > 0 && <Repeat size={12} className="plan-opcao-troca" />}
            <em className="plan-badge-linha">{perna.numero}</em>
          </span>
        ))}
      </div>
      <div className="plan-opcao-metricas">
        <strong>~{opcao.duracao_estimada_min} min</strong>
        <span>
          <Footprints size={12} /> {opcao.caminhada_metros} m
        </span>
        <span>
          {opcao.baldeacoes === 0
            ? "direto"
            : `${opcao.baldeacoes} baldeação`}
        </span>
      </div>
    </div>
  );
}

/** Limites da folha, em pixels. O mínimo é a faixa que fica visível
 *  quando ela está recolhida: alça mais o cabeçalho. */
const ALTURA_MINIMA = 96;
const LIMIAR_ARRASTO = 46;

/**
 * Folha arrastável do mobile (issue #132).
 *
 * A folha é a camada do meio da tela: fica sobre o mapa e sob a barra de
 * navegação. Recolhida, deixa o trajeto visível e mantém a alça ao
 * alcance do polegar; arrastada para cima, volta a mostrar as opções.
 *
 * O estado só muda se houve movimento de verdade (mais de 3 px). Sem
 * isso, um toque na alça registraria como arrasto de zero pixel e a
 * folha oscilaria sozinha.
 */
function useFolhaArrastavel() {
  const ref = useRef<HTMLElement>(null);
  const [recolhida, setRecolhida] = useState(false);
  const [altura, setAltura] = useState<number | null>(null);
  const [arrastando, setArrastando] = useState(false);
  const arrasto = useRef<{ y0: number; altura0: number; moveu: boolean } | null>(
    null
  );
  const suprimirClique = useRef(false);

  const aoMover = useCallback((evento: PointerEvent) => {
    const atual = arrasto.current;
    if (!atual || !ref.current) return;

    const dy = evento.clientY - atual.y0;
    if (Math.abs(dy) > 3) atual.moveu = true;

    const teto = window.innerHeight * 0.82;
    setAltura(Math.max(ALTURA_MINIMA, Math.min(teto, atual.altura0 - dy)));
  }, []);

  const aoSoltar = useCallback(
    (evento: PointerEvent) => {
      const atual = arrasto.current;
      window.removeEventListener("pointermove", aoMover);
      window.removeEventListener("pointerup", aoSoltar);
      window.removeEventListener("pointercancel", aoSoltar);
      arrasto.current = null;
      setArrastando(false);
      setAltura(null);

      if (!atual || !atual.moveu) return;

      const dy = evento.clientY - atual.y0;
      if (dy < -LIMIAR_ARRASTO) setRecolhida(false);
      else if (dy > LIMIAR_ARRASTO) setRecolhida(true);

      // O pointerup dispara um clique logo em seguida; sem isso, arrastar
      // também alternaria o estado, desfazendo o que o arrasto acabou de
      // decidir.
      suprimirClique.current = true;
      window.setTimeout(() => {
        suprimirClique.current = false;
      }, 60);
    },
    [aoMover]
  );

  const aoPressionar = useCallback(
    (evento: React.PointerEvent) => {
      if (!ref.current) return;
      arrasto.current = {
        y0: evento.clientY,
        altura0: ref.current.offsetHeight,
        moveu: false,
      };
      setArrastando(true);
      window.addEventListener("pointermove", aoMover);
      window.addEventListener("pointerup", aoSoltar);
      window.addEventListener("pointercancel", aoSoltar);
    },
    [aoMover, aoSoltar]
  );

  const aoClicar = useCallback(() => {
    if (suprimirClique.current) return;
    setRecolhida((estava) => !estava);
  }, []);

  return { ref, recolhida, altura, arrastando, aoPressionar, aoClicar };
}

export default function PlanejadorViagem({
  origem,
  destino,
  onDefinir,
  onInverter,
  onBuscar,
  onEscolherNoMapa,
  escolhendoNoMapa,
  onUsarMinhaLocalizacao,
  temLocalizacao,
  opcoes,
  opcaoSelecionada,
  onSelecionarOpcao,
  calculando,
  erro,
  onFechar,
  veiculosPorLinha,
  rastreando,
}: PlanejadorViagemProps) {
  const podeBuscar = Boolean(origem && destino) && !calculando;
  const folha = useFolhaArrastavel();

  return (
    <aside
      ref={folha.ref}
      className={`plan-painel${folha.recolhida ? " recolhida" : ""}${
        folha.arrastando ? " arrastando" : ""
      }`}
      style={folha.altura !== null ? { height: `${folha.altura}px` } : undefined}
    >
      {/* Alça da folha (mobile). O botão existe porque arrastar não é
          acessível por teclado — quem navega assim alterna por aqui. */}
      <button
        type="button"
        className="plan-alca"
        aria-expanded={!folha.recolhida}
        aria-label={folha.recolhida ? "Abrir opções de viagem" : "Recolher opções de viagem"}
        onPointerDown={folha.aoPressionar}
        onClick={folha.aoClicar}
      >
        <span className="plan-alca-traco" aria-hidden="true" />
      </button>

      <div className="plan-cabecalho">
        <strong>Para onde você vai?</strong>
        <button
          type="button"
          className="mapa-botao-icone"
          title="Fechar"
          onClick={onFechar}
        >
          <X size={16} />
        </button>
      </div>

      <form
        className="plan-formulario"
        onSubmit={(e) => {
          e.preventDefault();
          if (podeBuscar) onBuscar();
        }}
      >
        <CampoLugar
          extremo="origem"
          rotulo="De onde"
          placeholder="Ex: Terminal Ceilândia"
          valor={origem}
          onDefinir={onDefinir}
          onEscolherNoMapa={onEscolherNoMapa}
          escolhendo={escolhendoNoMapa === "origem"}
          onUsarMinhaLocalizacao={onUsarMinhaLocalizacao}
          temLocalizacao={temLocalizacao}
        />

        <button
          type="button"
          className="plan-inverter"
          title="Inverter origem e destino"
          onClick={onInverter}
          disabled={!origem && !destino}
        >
          <ArrowUpDown size={14} />
        </button>

        <CampoLugar
          extremo="destino"
          rotulo="Para onde"
          placeholder="Ex: Rodoviária do Plano Piloto"
          valor={destino}
          onDefinir={onDefinir}
          onEscolherNoMapa={onEscolherNoMapa}
          escolhendo={escolhendoNoMapa === "destino"}
          onUsarMinhaLocalizacao={onUsarMinhaLocalizacao}
          temLocalizacao={temLocalizacao}
        />

        <button type="submit" className="plan-buscar" disabled={!podeBuscar}>
          {calculando ? (
            <>
              <LoaderCircle size={15} className="plan-girando" /> Calculando...
            </>
          ) : (
            <>
              <Search size={15} /> Ver opções de ônibus
            </>
          )}
        </button>
      </form>

      {erro && (
        <p className="plan-erro" role="alert">
          {erro}
        </p>
      )}

      {opcoes !== null && opcoes.length === 0 && !calculando && !erro && (
        <p className="plan-vazio">
          Nenhuma linha liga esses dois pontos, nem com uma baldeação.
          Tente um ponto de referência mais próximo de uma via principal.
        </p>
      )}

      {opcoes !== null && opcoes.length > 0 && (
        <div className="plan-resultados">
          <div className="plan-resultados-titulo">
            {opcoes.length} {opcoes.length === 1 ? "opção" : "opções"}
            {(() => {
              // A lista mistura diretas e baldeações, ordenadas por
              // tempo — às vezes a baldeação é a mais rápida. Um rótulo
              // baseado só na primeira opção mentiria sobre o resto.
              const diretas = opcoes.filter((o) => o.baldeacoes === 0).length;
              const comTroca = opcoes.length - diretas;
              if (diretas && comTroca) {
                return ` · ${diretas} direta${diretas > 1 ? "s" : ""}, ${comTroca} com baldeação`;
              }
              if (comTroca) return " · todas com baldeação";
              return ` · direta${diretas > 1 ? "s" : ""}`;
            })()}
          </div>

          <ul className="plan-opcoes">
            {opcoes.map((opcao, indice) => (
              <li key={indice}>
                <button
                  type="button"
                  className={`plan-opcao${
                    indice === opcaoSelecionada ? " selecionada" : ""
                  }`}
                  onClick={() => onSelecionarOpcao(indice)}
                  aria-expanded={indice === opcaoSelecionada}
                >
                  <ResumoOpcao opcao={opcao} />

                  {indice === opcaoSelecionada && (
                    <ol className="plan-passos">
                      {opcao.pernas.map((perna, i) => (
                        <li key={`${perna.numero}-${i}`}>
                          <div className="plan-passo-linha">
                            <em className="plan-badge-linha">{perna.numero}</em>
                            <span className="plan-passo-nome">{perna.nome}</span>
                          </div>

                          {/* US #16 no contexto da US #20: quem planeja a
                              viagem quer saber onde está o ônibus que vai
                              pegar, sem ter que buscar a linha de novo. */}
                          <div className="plan-passo-aovivo">
                            {(() => {
                              const rodando = veiculosPorLinha[perna.numero] ?? 0;
                              if (rodando > 0) {
                                return (
                                  <>
                                    <span className="mapa-pulso" />
                                    <Bus size={12} />
                                    <span>
                                      <strong>{rodando}</strong>{" "}
                                      {rodando === 1
                                        ? "ônibus rodando agora"
                                        : "ônibus rodando agora"}
                                    </span>
                                  </>
                                );
                              }
                              return (
                                <span className="plan-passo-sem-onibus">
                                  {rastreando
                                    ? "Nenhum ônibus desta linha reportando posição agora"
                                    : "Procurando ônibus..."}
                                </span>
                              );
                            })()}
                          </div>
                          <div className="plan-passo-detalhe">
                            <span>
                              Embarque em{" "}
                              <strong>
                                {rotuloDoPonto(
                                  perna.embarque.parada_nome,
                                  perna.embarque.lat,
                                  perna.embarque.lng
                                )}
                              </strong>
                              {perna.embarque.caminhada_metros > 0 && (
                                <em>
                                  {" "}
                                  ({perna.embarque.caminhada_metros} m a pé)
                                </em>
                              )}
                            </span>
                            <span className="plan-passo-meio">
                              <ArrowRight size={12} />
                              {perna.paradas_no_trecho > 0
                                ? `${perna.paradas_no_trecho} paradas · `
                                : ""}
                              {perna.distancia_km} km
                            </span>
                            <span>
                              Desça em{" "}
                              <strong>
                                {rotuloDoPonto(
                                  perna.desembarque.parada_nome,
                                  perna.desembarque.lat,
                                  perna.desembarque.lng
                                )}
                              </strong>
                              {perna.desembarque.caminhada_metros > 0 && (
                                <em>
                                  {" "}
                                  ({perna.desembarque.caminhada_metros} m a pé)
                                </em>
                              )}
                            </span>
                          </div>
                        </li>
                      ))}
                    </ol>
                  )}
                </button>
              </li>
            ))}
          </ul>

          <p className="plan-ressalva">
            Tempo estimado por velocidade média, sem horário de tabela.
            Planejamento por horário de partida está em desenvolvimento.
          </p>
        </div>
      )}
    </aside>
  );
}
