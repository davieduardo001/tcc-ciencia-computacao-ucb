"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { MapPin, Plus, TriangleAlert, X } from "lucide-react";
import AppShell from "../mapa/AppShell";
import {
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
  // `useRouter` do Next é estável, mas guardar em ref mantém o efeito de
  // carga dependendo só do filtro — sem refetch se a identidade mudar.
  const routerRef = useRef(router);
  routerRef.current = router;

  // US #24 — vindo do detalhe da linha ("Ver ocorrências desta linha"),
  // a lista já chega filtrada; quem abre direto vê todas as ativas.
  const searchParams = useSearchParams();
  const [linhaFiltro, setLinhaFiltro] = useState(searchParams.get("linha") ?? "");

  const [ocorrencias, setOcorrencias] = useState<OcorrenciaListada[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const primeiraCarga = useRef(true);

  useEffect(() => {
    let cancelado = false;
    // A 1ª carga é imediata; só a digitação no filtro espera o debounce.
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
