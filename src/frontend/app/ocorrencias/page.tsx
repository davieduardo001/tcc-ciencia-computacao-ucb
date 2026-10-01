"use client";

import { FormEvent, Suspense, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Ban,
  Clock,
  Construction,
  LocateFixed,
  LucideIcon,
  Send,
  ShieldAlert,
  Siren,
  Users,
  Wrench,
} from "lucide-react";
import AppShell from "../mapa/AppShell";
import {
  LinhaResumo,
  nomearLugar,
  reportarOcorrencia,
  ReportarOcorrenciaError,
  sugerirLinhas,
  TipoOcorrencia,
} from "@/lib/api";
import "./ocorrencias.css";

const DEBOUNCE_BUSCA_MS = 250;

const TIPOS: { id: TipoOcorrencia; label: string; Icone: LucideIcon }[] = [
  { id: "atraso", label: "Atraso", Icone: Clock },
  { id: "nao_passou", label: "Ônibus não passou", Icone: Ban },
  { id: "lotacao", label: "Lotação", Icone: Users },
  { id: "obra_via", label: "Obra na via", Icone: Construction },
  { id: "onibus_quebrou", label: "Ônibus quebrou", Icone: Wrench },
  { id: "acidente", label: "Acidente", Icone: Siren },
  { id: "seguranca", label: "Segurança", Icone: ShieldAlert },
];

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
  // US #23 — vindo do atalho "Reportar ocorrência nesta linha" (detalhe
  // da linha no mapa), a linha já chega preenchida; quem abre a tela
  // direto (pelo "+" ou pela sidebar) continua digitando do zero.
  const searchParams = useSearchParams();
  const linhaDaUrl = searchParams.get("linha") ?? "";

  const [linhaNumero, setLinhaNumero] = useState(linhaDaUrl);
  const [sugestoes, setSugestoes] = useState<LinhaResumo[]>([]);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [tipo, setTipo] = useState<TipoOcorrencia | null>(null);
  const [descricao, setDescricao] = useState("");
  const [local, setLocal] = useState("");
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [localizando, setLocalizando] = useState(false);

  const [enviando, setEnviando] = useState(false);
  const [mensagem, setMensagem] = useState<{ tipo: "sucesso" | "erro"; texto: string } | null>(null);

  function aoDigitarLinha(termo: string) {
    setLinhaNumero(termo);
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (termo.trim().length === 0) {
      setSugestoes([]);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setSugestoes(await sugerirLinhas(termo));
    }, DEBOUNCE_BUSCA_MS);
  }

  function selecionarLinha(linha: LinhaResumo) {
    setLinhaNumero(linha.numero);
    setSugestoes([]);
  }

  // Geolocalização pedida só agora, no momento do uso — nunca no load da
  // tela. Se o usuário negar, o campo "Local" continua editável à mão:
  // a tela não depende do GPS pra funcionar.
  function usarMinhaLocalizacao() {
    if (!("geolocation" in navigator)) return;

    setLocalizando(true);
    navigator.geolocation.getCurrentPosition(
      async ({ coords: { latitude, longitude } }) => {
        setCoords({ lat: latitude, lng: longitude });
        const lugar = await nomearLugar(latitude, longitude);
        if (lugar) setLocal(lugar.endereco || lugar.nome);
        setLocalizando(false);
      },
      () => setLocalizando(false),
      { timeout: 8000 }
    );
  }

  async function enviarReporte(evento: FormEvent) {
    evento.preventDefault();

    if (!linhaNumero.trim() || !tipo) {
      setMensagem({ tipo: "erro", texto: "Selecione a linha e o tipo de ocorrência." });
      return;
    }

    setEnviando(true);
    setMensagem(null);

    try {
      await reportarOcorrencia({
        linhaNumero: linhaNumero.trim(),
        tipo,
        descricao: descricao.trim() || undefined,
        local: local.trim() || undefined,
        lat: coords?.lat,
        lng: coords?.lng,
      });

      setMensagem({
        tipo: "sucesso",
        texto: "Reporte enviado! Obrigado por ajudar outros passageiros.",
      });
      setTipo(null);
      setDescricao("");
    } catch (erro) {
      if (erro instanceof ReportarOcorrenciaError) {
        if (erro.message.startsWith("Faça login")) {
          router.push("/login");
          return;
        }
        setMensagem({ tipo: "erro", texto: erro.message });
      } else {
        setMensagem({ tipo: "erro", texto: "Não foi possível registrar o reporte. Tente novamente." });
      }
    } finally {
      setEnviando(false);
    }
  }

  return (
    <AppShell active="ocorrencias">
      <div className="ocor-page">
        <h1>Reportar ocorrência</h1>
        <p className="ocor-sub">
          Ajude outros passageiros. Ocorrências como atraso, lotação e obra na via são
          validadas por cruzamento (mínimo 2 confirmações) antes de aparecer como
          confirmadas; acidente e segurança aparecem na hora.
        </p>

        <form className="ocor-form" onSubmit={enviarReporte}>
          <label className="ocor-campo">
            <span>Linha</span>
            <input
              value={linhaNumero}
              onChange={(evento) => aoDigitarLinha(evento.target.value)}
              placeholder="Ex: 0.110"
              autoComplete="off"
            />
            {sugestoes.length > 0 && (
              <ul className="ocor-sugestoes" role="listbox">
                {sugestoes.map((linha) => (
                  <li key={linha.numero}>
                    <button type="button" onClick={() => selecionarLinha(linha)}>
                      <strong>{linha.numero}</strong>
                      <span>{linha.nome}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </label>

          <span className="ocor-label-tipo">Tipo de ocorrência</span>
          <div className="ocor-grid-tipos">
            {TIPOS.map(({ id, label, Icone }) => (
              <button
                key={id}
                type="button"
                className={`ocor-chip${tipo === id ? " on" : ""}`}
                onClick={() => setTipo(id)}
                aria-pressed={tipo === id}
              >
                <Icone size={22} />
                <span>{label}</span>
              </button>
            ))}
          </div>

          <label className="ocor-campo">
            <span>Descrição (opcional)</span>
            <textarea
              value={descricao}
              onChange={(evento) => setDescricao(evento.target.value)}
              placeholder="Conte o que aconteceu para ajudar outros passageiros..."
            />
          </label>

          <label className="ocor-campo">
            <span>Local (opcional)</span>
            <div className="ocor-local-linha">
              <input
                value={local}
                onChange={(evento) => setLocal(evento.target.value)}
                placeholder="Parada ou endereço"
              />
              <button
                type="button"
                className="ocor-btn-localizar"
                onClick={usarMinhaLocalizacao}
                disabled={localizando}
              >
                <LocateFixed size={16} />
                {localizando ? "Localizando..." : "Usar minha localização"}
              </button>
            </div>
          </label>

          {mensagem && <p className={`ocor-mensagem ${mensagem.tipo}`}>{mensagem.texto}</p>}

          <button type="submit" className="ocor-btn-enviar" disabled={enviando}>
            <Send size={16} />
            {enviando ? "Enviando..." : "Enviar reporte"}
          </button>
        </form>
      </div>
    </AppShell>
  );
}
