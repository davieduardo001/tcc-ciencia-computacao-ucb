"use client";

import { useState } from "react";
import { useViagem } from "./ViagemContext";

interface BotaoPegueiProps {
  numeroLinha: string;
  prefixo: string;
  /** Posição do usuário; só confirma que ele está perto do ônibus (RN-06). */
  posicaoDoUsuario: { lat: number; lng: number } | null;
}

/**
 * "Peguei este ônibus", dentro do popup do veículo (US #171, Cenários 1 e 4).
 *
 * O servidor decide se o embarque vale (ônibus da linha a até 100 m): este
 * botão só pergunta. Sem posição do usuário não há como perguntar, e a tela
 * diz isso em vez de deixar um botão que nunca funciona.
 */
export function BotaoPegueiOnibus({ numeroLinha, prefixo, posicaoDoUsuario }: BotaoPegueiProps) {
  const { viagem, ocupado, embarcar } = useViagem();
  const [mensagem, setMensagem] = useState<string | null>(null);

  if (viagem) {
    const esteOnibus = viagem.numeroLinha === numeroLinha && viagem.veiculoPrefixo === prefixo;
    return esteOnibus ? (
      <p className="mapa-pegar-onibus-aviso" role="status">
        Você está neste ônibus.
      </p>
    ) : null;
  }

  if (!posicaoDoUsuario) {
    return (
      <p className="mapa-pegar-onibus-aviso">
        Ative a localização para indicar que pegou este ônibus.
      </p>
    );
  }

  async function aoTocar() {
    setMensagem(null);
    const resultado = await embarcar({
      numeroLinha,
      lat: posicaoDoUsuario!.lat,
      lng: posicaoDoUsuario!.lng,
    });
    if (!resultado.ok) {
      setMensagem(resultado.mensagem ?? "Não foi possível registrar o embarque.");
    }
  }

  return (
    <div className="mapa-pegar-onibus">
      <button
        type="button"
        className="mapa-pegar-onibus-btn"
        onClick={aoTocar}
        disabled={ocupado}
      >
        Peguei este ônibus
      </button>
      {mensagem && (
        <p className="mapa-pegar-onibus-erro" role="alert">
          {mensagem}
        </p>
      )}
    </div>
  );
}

interface BotaoPegueiNaRotaProps {
  numeroLinha: string;
  /** `parada.codigo` do desembarque do trecho; vira o destino da viagem. */
  paradaDestinoCodigo: string | null;
  /** Posição do usuário; só confirma que ele está perto do ônibus (RN-06). */
  posicaoDoUsuario: { lat: number; lng: number } | null;
}

/**
 * "Peguei este ônibus" a partir de um trecho da rota montada (issue #190).
 *
 * Diferente do botão do popup, aqui não se escolhe um ônibus: o servidor
 * decide qual da linha confirma o embarque (a até o raio do usuário, ou
 * chegando à parada dele). Com sucesso, a parada de desembarque do trecho já
 * fica como destino da viagem — sem escolher de novo no mapa. Sem código de
 * parada, a viagem começa sem destino e o usuário pode escolhê-lo depois.
 */
export function BotaoPegueiNaRota({
  numeroLinha,
  paradaDestinoCodigo,
  posicaoDoUsuario,
}: BotaoPegueiNaRotaProps) {
  const { viagem, ocupado, embarcar } = useViagem();
  const [mensagem, setMensagem] = useState<string | null>(null);

  if (viagem) {
    return viagem.numeroLinha === numeroLinha ? (
      <p className="mapa-pegar-onibus-aviso" role="status">
        Você está nesta linha.
      </p>
    ) : null;
  }

  if (!posicaoDoUsuario) {
    return (
      <p className="mapa-pegar-onibus-aviso">
        Ative a localização para indicar que pegou o ônibus.
      </p>
    );
  }

  async function aoTocar() {
    setMensagem(null);
    const resultado = await embarcar({
      numeroLinha,
      lat: posicaoDoUsuario!.lat,
      lng: posicaoDoUsuario!.lng,
      ...(paradaDestinoCodigo ? { paradaDestinoCodigo } : {}),
    });
    if (!resultado.ok) {
      setMensagem(resultado.mensagem ?? "Não foi possível registrar o embarque.");
    }
  }

  return (
    <div className="mapa-pegar-onibus">
      <button
        type="button"
        className="mapa-pegar-onibus-btn"
        onClick={aoTocar}
        disabled={ocupado}
      >
        Peguei este ônibus
      </button>
      {mensagem && (
        <p className="mapa-pegar-onibus-erro" role="alert">
          {mensagem}
        </p>
      )}
    </div>
  );
}

interface BotaoDescerProps {
  codigoDaParada: string;
  /** Linhas que passam por esta parada. */
  numerosDasLinhas: string[];
}

/**
 * "Descer nesta parada", no painel da parada (US #171): escolhe o destino da
 * viagem em andamento tocando no mapa. Só aparece quando a linha da viagem
 * passa por aqui — o servidor recusaria o resto, e o botão não deve
 * prometer o que não vai funcionar.
 */
export function BotaoDescerNestaParada({ codigoDaParada, numerosDasLinhas }: BotaoDescerProps) {
  const { viagem, ocupado, definirDestino } = useViagem();
  const [mensagem, setMensagem] = useState<string | null>(null);

  if (!viagem || !numerosDasLinhas.includes(viagem.numeroLinha)) return null;

  const ehODestino = viagem.paradaDestinoCodigo === codigoDaParada;

  async function aoTocar() {
    setMensagem(null);
    const resultado = await definirDestino(ehODestino ? null : codigoDaParada);
    if (!resultado.ok) {
      setMensagem(resultado.mensagem ?? "Não foi possível salvar o destino.");
    }
  }

  return (
    <div className="mapa-descer">
      <p className="mapa-descer-contexto">
        {ehODestino
          ? `Esta é a sua parada de destino na linha ${viagem.numeroLinha}.`
          : `Você está na linha ${viagem.numeroLinha}.`}
      </p>
      <button
        type="button"
        className={`mapa-descer-btn${ehODestino ? " secundario" : ""}`}
        onClick={aoTocar}
        disabled={ocupado}
      >
        {ehODestino ? "Tirar destino" : "Descer nesta parada"}
      </button>
      {mensagem && (
        <p className="mapa-pegar-onibus-erro" role="alert">
          {mensagem}
        </p>
      )}
    </div>
  );
}
