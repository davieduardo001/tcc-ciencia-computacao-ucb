"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Bell, BellOff, CircleAlert, CircleCheck } from "lucide-react";
import AppShell from "../mapa/AppShell";
import {
  alternarTodasNotificacoes,
  ANTECEDENCIAS_ALERTA,
  atualizarTipoNotificacao,
  buscarPreferencias,
  buscarUsuarioAtual,
  PreferenciasNotificacao,
  salvarAntecedencia,
  TipoNotificacao,
} from "@/lib/api";
import { TEXTOS_AVISOS_PUSH, useAvisosPush } from "../configuracoes/useAvisosPush";
import "./alertas.css";

/**
 * US #29 — Tela "Alertas" / Preferências de Notificação.
 *
 * Mapeia os campos do serviço de Colaboração:
 * - antecedencia_minutos (5, 10, 30, 60)  -> seletor de antecedência
 * - alerta_chegada / alerta_cancelamento  -> um interruptor por tipo
 * - notificacoes_ativas                   -> "desativar todas" / reativar
 *
 * Cada alteração é salva na hora; a tela só reflete o que o servidor
 * devolveu (nada de "salvo" otimista).
 */

const TIPOS: { tipo: TipoNotificacao; campo: "alertaChegada" | "alertaCancelamento"; titulo: string; descricao: string; desativado: string; ativado: string }[] = [
  {
    tipo: "chegada",
    campo: "alertaChegada",
    titulo: "Chegada do ônibus",
    descricao: "Avisa quando o ônibus da sua parada estiver chegando.",
    desativado: "Notificações de chegada desativadas.",
    ativado: "Notificações de chegada ativadas.",
  },
  {
    tipo: "cancelamento",
    campo: "alertaCancelamento",
    titulo: "Cancelamento de viagem",
    descricao: "Avisa quando uma viagem da linha que você acompanha for cancelada.",
    desativado: "Notificações de cancelamento desativadas.",
    ativado: "Notificações de cancelamento ativadas.",
  },
];

type Feedback = { tipo: "sucesso" | "erro"; texto: string };

function mensagemDeErro(erro: unknown, padrao: string): string {
  return erro instanceof Error && erro.message ? erro.message : padrao;
}

export default function AlertasPage() {
  const router = useRouter();
  const avisosPush = useAvisosPush();
  const textoPush = TEXTOS_AVISOS_PUSH[avisosPush.estado.tipo];

  const [usuarioId, setUsuarioId] = useState<string | null>(null);
  const [prefs, setPrefs] = useState<PreferenciasNotificacao | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erroCarga, setErroCarga] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErroCarga(null);
    try {
      const usuario = await buscarUsuarioAtual();
      if (!usuario) {
        router.push("/login");
        return;
      }
      setUsuarioId(usuario.id);
      setPrefs(await buscarPreferencias(usuario.id));
    } catch (erro) {
      setErroCarga(
        mensagemDeErro(erro, "Não foi possível carregar suas preferências. Tente novamente.")
      );
    } finally {
      setCarregando(false);
    }
  }, [router]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  async function aplicar(
    acao: (id: string) => Promise<PreferenciasNotificacao>,
    mensagem: (novas: PreferenciasNotificacao) => string
  ) {
    if (!usuarioId || salvando) return;
    setSalvando(true);
    setFeedback(null);
    try {
      const novas = await acao(usuarioId);
      setPrefs(novas);
      setFeedback({ tipo: "sucesso", texto: mensagem(novas) });
    } catch (erro) {
      setFeedback({
        tipo: "erro",
        texto: mensagemDeErro(erro, "Não foi possível salvar. Tente novamente."),
      });
    } finally {
      setSalvando(false);
    }
  }

  function escolherAntecedencia(minutos: number) {
    if (prefs?.antecedenciaMinutos === minutos) return;
    aplicar(
      (id) => salvarAntecedencia(id, minutos),
      (n) => `Alertas serão enviados com ${n.antecedenciaMinutos} minutos de antecedência.`
    );
  }

  function alternarTipo(item: (typeof TIPOS)[number]) {
    if (!prefs) return;
    const ativar = !prefs[item.campo];
    aplicar(
      (id) => atualizarTipoNotificacao(id, item.tipo, ativar),
      () => (ativar ? item.ativado : item.desativado)
    );
  }

  function alternarTodas() {
    if (!prefs) return;
    const reativar = !prefs.notificacoesAtivas;
    aplicar(
      (id) => alternarTodasNotificacoes(id, reativar),
      () =>
        reativar
          ? "Notificações reativadas."
          : "Todas as notificações foram desativadas."
    );
  }

  return (
    <AppShell active="alertas">
      <div className="alt-page">
        <div className="alt-cabecalho">
          <Bell size={20} aria-hidden="true" />
          <h1>Alertas</h1>
        </div>

        {carregando ? (
          <p className="alt-carregando" role="status">
            Carregando suas preferências...
          </p>
        ) : erroCarga || !prefs ? (
          <div className="alt-erro-carga" role="alert">
            <p>{erroCarga ?? "Não foi possível carregar suas preferências."}</p>
            <button type="button" className="alt-btn" onClick={carregar}>
              Tentar novamente
            </button>
          </div>
        ) : (
          <>
            <div className="alt-feedback-area" role="status" aria-live="polite">
              {feedback && (
                <p className={`alt-feedback ${feedback.tipo}`}>
                  {feedback.tipo === "sucesso" ? (
                    <CircleCheck size={16} aria-hidden="true" />
                  ) : (
                    <CircleAlert size={16} aria-hidden="true" />
                  )}
                  <span>{feedback.texto}</span>
                </p>
              )}
            </div>

            <section className="alt-secao" aria-labelledby="alt-antecedencia-titulo">
              <h2 id="alt-antecedencia-titulo">Antecedência dos alertas de chegada</h2>
              <p className="alt-dica" id="alt-antecedencia-dica">
                Com quantos minutos antes da chegada do ônibus você quer ser avisado.
              </p>
              <div
                className="alt-opcoes"
                role="radiogroup"
                aria-labelledby="alt-antecedencia-titulo"
                aria-describedby="alt-antecedencia-dica"
              >
                {ANTECEDENCIAS_ALERTA.map((minutos) => (
                  <label
                    key={minutos}
                    className={`alt-opcao${
                      prefs.antecedenciaMinutos === minutos ? " selecionada" : ""
                    }`}
                  >
                    <input
                      type="radio"
                      name="antecedencia"
                      value={minutos}
                      checked={prefs.antecedenciaMinutos === minutos}
                      disabled={salvando}
                      onChange={() => escolherAntecedencia(minutos)}
                    />
                    <span>{minutos} min</span>
                  </label>
                ))}
              </div>
            </section>

            <section className="alt-secao" aria-labelledby="alt-tipos-titulo">
              <h2 id="alt-tipos-titulo">Tipos de notificação</h2>
              {!prefs.notificacoesAtivas && (
                <p className="alt-aviso-geral">
                  Todas as notificações estão desativadas. Seus ajustes abaixo voltam a valer
                  quando você reativá-las.
                </p>
              )}
              <ul className="alt-tipos">
                {TIPOS.map((item) => {
                  const ligado = prefs[item.campo];
                  return (
                    <li key={item.tipo} className="alt-tipo">
                      <div className="alt-tipo-info">
                        <h3 id={`alt-tipo-${item.tipo}`}>{item.titulo}</h3>
                        <p id={`alt-tipo-${item.tipo}-desc`}>{item.descricao}</p>
                      </div>
                      <button
                        type="button"
                        role="switch"
                        aria-checked={ligado}
                        aria-labelledby={`alt-tipo-${item.tipo}`}
                        aria-describedby={`alt-tipo-${item.tipo}-desc`}
                        className={`alt-switch${ligado ? " ligado" : ""}`}
                        disabled={salvando}
                        onClick={() => alternarTipo(item)}
                      >
                        <span className="alt-switch-bolinha" aria-hidden="true" />
                        <span className="alt-sr">{ligado ? "Ativado" : "Desativado"}</span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </section>

            <section className="alt-secao" aria-labelledby="alt-todas-titulo">
              <h2 id="alt-todas-titulo">Todas as notificações</h2>
              <p className="alt-dica">
                {prefs.notificacoesAtivas
                  ? "Desative tudo de uma vez. Você pode reativar quando quiser."
                  : "Estão desativadas. Reative para voltar a receber os alertas."}
              </p>
              <button
                type="button"
                className={`alt-btn ${prefs.notificacoesAtivas ? "perigo" : ""}`}
                disabled={salvando}
                onClick={alternarTodas}
              >
                {prefs.notificacoesAtivas ? (
                  <>
                    <BellOff size={16} aria-hidden="true" /> Desativar todas
                  </>
                ) : (
                  <>
                    <Bell size={16} aria-hidden="true" /> Reativar notificações
                  </>
                )}
              </button>
            </section>

            <section className="alt-secao" aria-labelledby="alt-push-titulo">
              <h2 id="alt-push-titulo">Avisos com a tela bloqueada</h2>
              <p className="alt-dica">{textoPush.descricao}</p>
              <Link href="/configuracoes" className="alt-link">
                Gerenciar em Configurações
              </Link>
            </section>
          </>
        )}
      </div>
    </AppShell>
  );
}
