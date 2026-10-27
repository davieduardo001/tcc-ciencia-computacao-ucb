"use client";

import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { LoaderCircle, MapPin, Plus, ThumbsUp, TriangleAlert, X } from "lucide-react";
import AppShell from "../mapa/AppShell";
import {
  confirmarOcorrencia,
  ConfirmarOcorrenciaError,
  listarOcorrencias,
  ListarOcorrenciasError,
  OcorrenciaListada,
} from "@/lib/api";
import { TIPOS } from "./tipos";
import "./ocorrencias.css";

const DEBOUNCE_FILTRO_MS = 300;

/**
 * O backend entrega `criado_em` em UTC com fuso explícito ("...Z"), então
 * `new Date()` lê o instante certo independente do fuso do navegador.
 */
function tempoDecorrido(criadoEm: string): string {
  const minutos = Math.max(0, Math.floor((Date.now() - new Date(criadoEm).getTime()) / 60000));
  if (minutos < 1) return "agora mesmo";
  if (minutos < 60) return `há ${minutos} min`;
  return `há ${Math.floor(minutos / 60)} h`;
}

function rotuloConfirmacoes(ocorrencia: OcorrenciaListada): string {
  if (ocorrencia.status !== "confirmada") return "Aguardando confirmação";
  const n = ocorrencia.contadorConfirmacoes;
  if (n <= 0) return "Confirmada";
  return `Confirmada · ${n} ${n === 1 ? "confirmação" : "confirmações"}`;
}

/**
 * `useSearchParams` exige renderização no cliente — sem o Suspense o
 * `next build` falha na geração estática (mesmo padrão de app/mapa/page.tsx).
 */
export default function OcorrenciasPage() {
  return (
    <Suspense fallback={null}>
      <OcorrenciasConteudo />
    </Suspense>
  );
}

function OcorrenciasConteudo() {
  const router = useRouter();
  const routerRef = useRef(router);
  routerRef.current = router;

  const searchParams = useSearchParams();
  const [linhaFiltro, setLinhaFiltro] = useState(searchParams.get("linha") ?? "");

  const [ocorrencias, setOcorrencias] = useState<OcorrenciaListada[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const primeiraCarga = useRef(true);

  // US #26 — ID da ocorrência em processo de confirmação (evita duplo clique)
  // e mensagens por ocorrência.
  const [confirmando, setConfirmando] = useState<string | null>(null);
  const [mensagensConfirmacao, setMensagensConfirmacao] = useState<
    Record<string, { texto: string; tipo: "sucesso" | "erro" }>
  >({});

  useEffect(() => {
    let cancelado = false;
    const atraso = primeiraCarga.current ? 0 : DEBOUNCE_FILTRO_MS;
    primeiraCarga.current = false;

    const timer = setTimeout(async () => {
      setCarregando(true);
      setErro(null);
      try {
        const lista = await listarOcorrencias(linhaFiltro);
        if (!cancelado) setOcorrencias(lista);
      } catch (falha) {
        if (cancelado) return;
        if (falha instanceof ListarOcorrenciasError && falha.naoAutenticado) {
          routerRef.current.push("/login");
          return;
        }
        setErro(
          falha instanceof ListarOcorrenciasError
            ? falha.message
            : "Não foi possível carregar as ocorrências."
        );
      } finally {
        if (!cancelado) setCarregando(false);
      }
    }, atraso);

    return () => {
      cancelado = true;
      clearTimeout(timer);
    };
  }, [linhaFiltro]);

  // US #26 — confirmar ocorrência de outro passageiro.
  const handleConfirmar = useCallback(async (ocorrenciaId: string) => {
    if (confirmando) return; // evita duplo clique

    setConfirmando(ocorrenciaId);
    setMensagensConfirmacao((prev) => {
      const copia = { ...prev };
      delete copia[ocorrenciaId];
      return copia;
    });

    try {
      const resultado = await confirmarOcorrencia(ocorrenciaId);
      // Atualiza o estado local da ocorrência com os dados retornados.
      setOcorrencias((prev) =>
        prev.map((oc) =>
          oc.id === ocorrenciaId
            ? {
                ...oc,
                status: resultado.status,
                contadorConfirmacoes: resultado.contador_confirmacoes,
              }
            : oc
        )
      );
      setMensagensConfirmacao((prev) => ({
        ...prev,
        [ocorrenciaId]: { texto: resultado.mensagem, tipo: "sucesso" },
      }));
    } catch (falha) {
      const msg =
        falha instanceof ConfirmarOcorrenciaError
          ? falha.message
          : "Não foi possível confirmar. Tente novamente.";
      const status = falha instanceof ConfirmarOcorrenciaError ? falha.status : 0;

      if (status === 401) {
        routerRef.current.push("/login");
        return;
      }

      setMensagensConfirmacao((prev) => ({
        ...prev,
        [ocorrenciaId]: { texto: msg, tipo: "erro" },
      }));
    } finally {
      setConfirmando(null);
    }
  }, [confirmando]);

  const filtro = linhaFiltro.trim();
  const hrefReportar = filtro
    ? `/ocorrencias/reportar?linha=${encodeURIComponent(filtro)}`
    : "/ocorrencias/reportar";

  return (
    <AppShell active="ocorrencias">
      <div className="ocor-page">
        <div className="ocor-cabecalho">
          <div>
            <h1>Ocorrências da comunidade</h1>
            <p className="ocor-sub">
              Reportes de outros passageiros que ainda estão valendo. Cada
              ocorrência sai da lista sozinha quando perde a validade.
            </p>
          </div>
          <Link href={hrefReportar} className="ocor-btn-reportar">
            <Plus size={16} />
            Reportar
          </Link>
        </div>

        <label className="ocor-campo ocor-filtro">
          <span>Filtrar por linha</span>
          <div className="ocor-filtro-linha">
            <input
              value={linhaFiltro}
              onChange={(evento) => setLinhaFiltro(evento.target.value)}
              placeholder="Ex: 0.110"
              autoComplete="off"
            />
            {linhaFiltro && (
              <button
                type="button"
                className="ocor-filtro-limpar"
                onClick={() => setLinhaFiltro("")}
                aria-label="Limpar filtro de linha"
              >
                <X size={16} />
              </button>
            )}
          </div>
        </label>

        <div aria-live="polite">
          {carregando && <p className="ocor-estado">Carregando ocorrências...</p>}

          {!carregando && erro && <p className="ocor-mensagem erro">{erro}</p>}

          {!carregando && !erro && ocorrencias.length === 0 && (
            <p className="ocor-estado">
              {filtro
                ? `Nenhuma ocorrência ativa na linha ${filtro}.`
                : "Nenhuma ocorrência ativa no momento."}
            </p>
          )}

          {!carregando && !erro && ocorrencias.length > 0 && (
            <ul className="ocor-lista">
              {ocorrencias.map((ocorrencia) => {
                const tipo = TIPOS.find((t) => t.id === ocorrencia.tipo);
                const Icone = tipo?.Icone ?? TriangleAlert;
                const msgConfirmacao = mensagensConfirmacao[ocorrencia.id];

                return (
                  <li key={ocorrencia.id} className={`ocor-card ${ocorrencia.status}`}>
                    <div className="ocor-card-icone">
                      <Icone size={20} />
                    </div>
                    <div className="ocor-card-corpo">
                      <div className="ocor-card-topo">
                        <strong>
                          {tipo?.label ?? ocorrencia.tipo} — {ocorrencia.linhaNumero}
                        </strong>
                        <span className="ocor-card-tempo">
                          {tempoDecorrido(ocorrencia.criadoEm)}
                        </span>
                      </div>
                      {ocorrencia.local && (
                        <div className="ocor-card-local">
                          <MapPin size={13} />
                          {ocorrencia.local}
                        </div>
                      )}
                      {ocorrencia.descricao && (
                        <p className="ocor-card-desc">{ocorrencia.descricao}</p>
                      )}
                      <span className={`ocor-badge ${ocorrencia.status}`}>
                        {rotuloConfirmacoes(ocorrencia)}
                      </span>

                      {/* US #26 — botão de confirmação.
                          Cenário 2: escondido para o autor da ocorrência (campo
                          `ehAutor` retornado pelo backend — nunca expõe userId).
                          Não exibido quando a ocorrência já está confirmada. */}
                      {!ocorrencia.ehAutor && ocorrencia.status === "pendente" && (
                        <div className="ocor-confirmar-area">
                          <button
                            type="button"
                            className="ocor-btn-confirmar"
                            onClick={() => handleConfirmar(ocorrencia.id)}
                            disabled={confirmando === ocorrencia.id}
                            aria-label={`Confirmar ocorrência: ${tipo?.label ?? ocorrencia.tipo} na linha ${ocorrencia.linhaNumero}`}
                          >
                            {confirmando === ocorrencia.id ? (
                              <>
                                <LoaderCircle size={14} className="ocor-girando" />
                                Confirmando...
                              </>
                            ) : (
                              <>
                                <ThumbsUp size={14} />
                                Eu também vi isso
                              </>
                            )}
                          </button>
                          {msgConfirmacao && (
                            <p
                              className={`ocor-confirmacao-msg ${msgConfirmacao.tipo}`}
                              role="status"
                            >
                              {msgConfirmacao.texto}
                            </p>
                          )}
                        </div>
                      )}

                      {/* Feedback após confirmação bem-sucedida (status mudou) */}
                      {!ocorrencia.ehAutor &&
                        ocorrencia.status === "confirmada" &&
                        msgConfirmacao?.tipo === "sucesso" && (
                          <p className="ocor-confirmacao-msg sucesso" role="status">
                            {msgConfirmacao.texto}
                          </p>
                        )}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </div>
    </AppShell>
  );
}
