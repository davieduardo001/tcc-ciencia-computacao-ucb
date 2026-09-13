"use client";

import dynamic from "next/dynamic";
import { useCallback, useRef, useState } from "react";
import AppShell from "./AppShell";
import {
  buscarLinha,
  BuscarLinhaError,
  LinhaDetalhada,
  LinhaResumo,
  sugerirLinhas,
} from "@/lib/api";

const MapaInterativo = dynamic(() => import("./MapaInterativo"), {
  ssr: false,
  loading: () => <p className="mapa-carregando">Carregando mapa...</p>,
});

const DEBOUNCE_SUGESTOES_MS = 250;

export default function MapaPage() {
  const [linha, setLinha] = useState<LinhaDetalhada | null>(null);
  const [erroBusca, setErroBusca] = useState<string | null>(null);
  const [buscandoLinha, setBuscandoLinha] = useState(false);
  const [sugestoesLinha, setSugestoesLinha] = useState<LinhaResumo[]>([]);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleBuscarLinha = useCallback(async (termo: string) => {
    const numero = termo.trim();
    if (!numero) return;

    setBuscandoLinha(true);
    setErroBusca(null);

    try {
      const resultado = await buscarLinha(numero);
      if (!resultado) {
        setLinha(null);
        setErroBusca(`Linha "${numero}" não encontrada.`);
        return;
      }
      setLinha(resultado);
    } catch (err) {
      setLinha(null);
      setErroBusca(
        err instanceof BuscarLinhaError
          ? err.message
          : "Não foi possível buscar a linha. Tente novamente."
      );
    } finally {
      setBuscandoLinha(false);
    }
  }, []);

  // US #17 (autocomplete) — sugere enquanto digita, com debounce pra não
  // disparar uma chamada a cada tecla. Nunca mostra erro: sugestão é
  // best-effort, quem trata falha de verdade é a busca principal acima.
  const handleDigitarBuscaLinha = useCallback((termo: string) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (!termo.trim()) {
      setSugestoesLinha([]);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      const resultado = await sugerirLinhas(termo);
      setSugestoesLinha(resultado);
    }, DEBOUNCE_SUGESTOES_MS);
  }, []);

  const handleSelecionarSugestaoLinha = useCallback(
    (numero: string) => {
      setSugestoesLinha([]);
      handleBuscarLinha(numero);
    },
    [handleBuscarLinha]
  );

  const handleFecharLinha = useCallback(() => {
    setLinha(null);
    setErroBusca(null);
  }, []);

  return (
    <AppShell
      active="mapa"
      onBuscarLinha={handleBuscarLinha}
      buscandoLinha={buscandoLinha}
      onDigitarBuscaLinha={handleDigitarBuscaLinha}
      sugestoesLinha={sugestoesLinha}
      onSelecionarSugestaoLinha={handleSelecionarSugestaoLinha}
    >
      <MapaInterativo
        linha={linha}
        erroBusca={erroBusca}
        onFecharLinha={handleFecharLinha}
      />
    </AppShell>
  );
}
