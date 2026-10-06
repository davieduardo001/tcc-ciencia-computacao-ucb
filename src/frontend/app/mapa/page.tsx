"use client";

import dynamic from "next/dynamic";
import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Navigation } from "lucide-react";
import AppShell from "./AppShell";
import PlanejadorViagem, { Extremo, PontoEscolhido } from "./PlanejadorViagem";
import {
  buscarLinha,
  BuscarLinhaError,
  calcularRotas,
  CalcularRotaError,
  cachearFavoritos,
  lerFavoritosCache,
  listarFavoritos,
  LinhaDetalhada,
  LinhaResumo,
  nomearLugar,
  OpcaoViagem,
  RotaFavorita,
  sugerirLinhas,
  VeiculoAoVivo,
} from "@/lib/api";

const MapaInterativo = dynamic(() => import("./MapaInterativo"), {
  ssr: false,
  loading: () => <p className="mapa-carregando">Carregando mapa...</p>,
});

const DEBOUNCE_SUGESTOES_MS = 250;

interface Coordenadas {
  lat: number;
  lng: number;
}

/**
 * `useSearchParams` obriga o componente a ser renderizado no cliente. A
 * página inteira é estática, então o Suspense isola essa parte — sem
 * ele o `next build` falha na geração estática.
 */
export default function MapaPage() {
  return (
    <Suspense fallback={<p className="mapa-carregando">Carregando mapa...</p>}>
      <MapaConteudo />
    </Suspense>
  );
}

function MapaConteudo() {
  const [linha, setLinha] = useState<LinhaDetalhada | null>(null);
  const [erroBusca, setErroBusca] = useState<string | null>(null);
  const [buscandoLinha, setBuscandoLinha] = useState(false);
  const [sugestoesLinha, setSugestoesLinha] = useState<LinhaResumo[]>([]);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const sequenciaBuscaRef = useRef(0);

  // US #20 — planejamento de viagem origem → destino.
  const [planejadorAberto, setPlanejadorAberto] = useState(false);
  const [origem, setOrigem] = useState<PontoEscolhido | null>(null);
  const [destino, setDestino] = useState<PontoEscolhido | null>(null);
  const [opcoes, setOpcoes] = useState<OpcaoViagem[] | null>(null);
  const [opcaoSelecionada, setOpcaoSelecionada] = useState<number | null>(null);
  const [calculandoRota, setCalculandoRota] = useState(false);
  const [erroRota, setErroRota] = useState<string | null>(null);
  const [escolhendoNoMapa, setEscolhendoNoMapa] = useState<Extremo | null>(null);
  const [localizacao, setLocalizacao] = useState<Coordenadas | null>(null);
  const [veiculos, setVeiculos] = useState<VeiculoAoVivo[] | null>(null);
  const [focarBusca, setFocarBusca] = useState(0);

  // US #25 — chaves lógicas dos favoritos salvos (para marcar a estrela).
  const [favoritosChaves, setFavoritosChaves] = useState<Set<string>>(new Set());

  // Os itens "Rotas" e "Linhas de Ônibus" da navegação abrem esta mesma
  // página, só que com o painel certo já aberto — as duas
  // funcionalidades vivem no mapa, não em páginas separadas.
  const searchParams = useSearchParams();
  const painel = searchParams.get("painel");
  // US #25 — query params injetados pelo clique em favorito.
  const origemLatParam = searchParams.get("origem_lat");
  const origemLngParam = searchParams.get("origem_lng");
  const destinoLatParam = searchParams.get("destino_lat");
  const destinoLngParam = searchParams.get("destino_lng");
  const origemNomeParam = searchParams.get("origem_nome");
  const destinoNomeParam = searchParams.get("destino_nome");

  useEffect(() => {
    if (painel === "rotas") {
      setPlanejadorAberto(true);
    } else if (painel === "linhas") {
      setPlanejadorAberto(false);
      // Nonce em vez de booleano: clicar em "Linhas de Ônibus" duas
      // vezes seguidas tem que focar o campo nas duas.
      setFocarBusca((n) => n + 1);
    }
  }, [painel]);

  // US #25 — ao abrir o planejador via favorito, pré-preenche origem/destino
  // a partir dos query params e calcula a rota automaticamente.

  useEffect(() => {
    if (
      painel === "rotas" &&
      origemLatParam &&
      origemLngParam &&
      destinoLatParam &&
      destinoLngParam
    ) {
      const orig: PontoEscolhido = {
        nome: origemNomeParam ?? `${parseFloat(origemLatParam).toFixed(4)}, ${parseFloat(origemLngParam).toFixed(4)}`,
        lat: parseFloat(origemLatParam),
        lng: parseFloat(origemLngParam),
      };
      const dest: PontoEscolhido = {
        nome: destinoNomeParam ?? `${parseFloat(destinoLatParam).toFixed(4)}, ${parseFloat(destinoLngParam).toFixed(4)}`,
        lat: parseFloat(destinoLatParam),
        lng: parseFloat(destinoLngParam),
      };
      setOrigem(orig);
      setDestino(dest);
      // O cálculo será disparado pelo useEffect seguinte que observa origem/destino.
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [painel, origemLatParam, origemLngParam, destinoLatParam, destinoLngParam]);

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

    // Toda busca recebe um número de sequência e só aplica o resultado se
    // ainda for a mais recente. Sem isso, uma busca anterior que demore
    // mais pra responder sobrescreve a atual: digitar "asa norte" pausando
    // depois do "a" disparava uma busca por "a" (que casa com quase toda
    // linha) e a lista errada chegava depois, parecendo que a busca não
    // filtrava nada.
    const sequencia = ++sequenciaBuscaRef.current;

    if (!termo.trim()) {
      setSugestoesLinha([]);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      const resultado = await sugerirLinhas(termo);
      if (sequencia === sequenciaBuscaRef.current) {
        setSugestoesLinha(resultado);
      }
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

  // -- US #20 ---------------------------------------------------------------

  const definirPonto = useCallback(
    (extremo: Extremo, ponto: PontoEscolhido | null) => {
      (extremo === "origem" ? setOrigem : setDestino)(ponto);
      // Mudou uma das pontas: o resultado anterior não vale mais.
      setOpcoes(null);
      setOpcaoSelecionada(null);
      setErroRota(null);
    },
    []
  );

  const handleInverter = useCallback(() => {
    setOrigem(destino);
    setDestino(origem);
    setOpcoes(null);
    setOpcaoSelecionada(null);
  }, [origem, destino]);

  const handleUsarMinhaLocalizacao = useCallback(
    async (extremo: Extremo) => {
      if (!localizacao) return;

      // Mostra a coordenada na hora e troca pelo nome quando chegar —
      // esperar o Nominatim pra preencher o campo daria a impressão de
      // que o botão não funcionou.
      definirPonto(extremo, {
        nome: "Minha localização",
        lat: localizacao.lat,
        lng: localizacao.lng,
      });

      const lugar = await nomearLugar(localizacao.lat, localizacao.lng);
      if (lugar) {
        definirPonto(extremo, {
          nome: lugar.nome,
          lat: localizacao.lat,
          lng: localizacao.lng,
        });
      }
    },
    [localizacao, definirPonto]
  );

  const handleEscolherNoMapa = useCallback((extremo: Extremo) => {
    setEscolhendoNoMapa((atual) => (atual === extremo ? null : extremo));
  }, []);

  const handleCliqueNoMapa = useCallback(
    async (lat: number, lng: number) => {
      const extremo = escolhendoNoMapa;
      if (!extremo) return;

      setEscolhendoNoMapa(null);
      definirPonto(extremo, {
        nome: `${lat.toFixed(4)}, ${lng.toFixed(4)}`,
        lat,
        lng,
      });

      const lugar = await nomearLugar(lat, lng);
      if (lugar) {
        definirPonto(extremo, { nome: lugar.nome, lat, lng });
      }
    },
    [escolhendoNoMapa, definirPonto]
  );

  const handleCalcularRota = useCallback(async () => {
    if (!origem || !destino) return;

    setCalculandoRota(true);
    setErroRota(null);
    setOpcoes(null);
    setOpcaoSelecionada(null);
    // O trajeto de uma linha buscada por número atrapalharia a leitura
    // do itinerário — são duas coisas diferentes no mesmo mapa.
    setLinha(null);

    try {
      const resultado = await calcularRotas(origem, destino);
      setOpcoes(resultado);
      // Abre a primeira opção já expandida: quase sempre é a escolhida.
      setOpcaoSelecionada(resultado.length > 0 ? 0 : null);
    } catch (err) {
      setErroRota(
        err instanceof CalcularRotaError
          ? err.message
          : "Não foi possível calcular a rota. Tente novamente."
      );
    } finally {
      setCalculandoRota(false);
    }
  }, [origem, destino]);

  const handleFecharPlanejador = useCallback(() => {
    setPlanejadorAberto(false);
    setEscolhendoNoMapa(null);
  }, []);

  // US #25 — carrega favoritos na montagem para marcar as estrelas.
  useEffect(() => {
    listarFavoritos().then((lista) => {
      const chaves = new Set(
        lista.map(
          (f) =>
            `${f.numero_linha}:${f.origem_lat.toFixed(4)},${f.origem_lng.toFixed(4)}:${f.destino_lat.toFixed(4)},${f.destino_lng.toFixed(4)}`
        )
      );
      setFavoritosChaves(chaves);
    });
  }, []);

  // US #25 — ao salvar um favorito, atualiza o Set de chaves para marcar a estrela.
  const handleFavoritoSalvo = useCallback((favorito: RotaFavorita) => {
    const chave = `${favorito.numero_linha}:${favorito.origem_lat.toFixed(4)},${favorito.origem_lng.toFixed(4)}:${favorito.destino_lat.toFixed(4)},${favorito.destino_lng.toFixed(4)}`;
    setFavoritosChaves((prev) => new Set([...prev, chave]));
    // Atualiza o cache local adicionando o novo item.
    const cached = lerFavoritosCache();
    cachearFavoritos([favorito, ...cached]);
  }, []);

  const viagem =
    opcoes && opcaoSelecionada !== null ? opcoes[opcaoSelecionada] : null;

  // US #16 no painel da US #20: quantos ônibus estão rodando cada linha
  // do itinerário escolhido.
  const veiculosPorLinha = (veiculos ?? []).reduce<Record<string, number>>(
    (acc, veiculo) => {
      acc[veiculo.linha] = (acc[veiculo.linha] ?? 0) + 1;
      return acc;
    },
    {}
  );

  return (
    <AppShell
      active="mapa"
      onBuscarLinha={handleBuscarLinha}
      buscandoLinha={buscandoLinha}
      onDigitarBuscaLinha={handleDigitarBuscaLinha}
      sugestoesLinha={sugestoesLinha}
      onSelecionarSugestaoLinha={handleSelecionarSugestaoLinha}
      focarBusca={focarBusca}
    >
      <MapaInterativo
        linha={linha}
        erroBusca={erroBusca}
        onFecharLinha={handleFecharLinha}
        viagem={viagem}
        origemViagem={origem}
        destinoViagem={destino}
        escolhendoNoMapa={escolhendoNoMapa !== null}
        onCliqueNoMapa={handleCliqueNoMapa}
        onLocalizacao={setLocalizacao}
        onVeiculos={setVeiculos}
      />

      {planejadorAberto ? (
        <PlanejadorViagem
          origem={origem}
          destino={destino}
          onDefinir={definirPonto}
          onInverter={handleInverter}
          onBuscar={handleCalcularRota}
          onEscolherNoMapa={handleEscolherNoMapa}
          escolhendoNoMapa={escolhendoNoMapa}
          onUsarMinhaLocalizacao={handleUsarMinhaLocalizacao}
          temLocalizacao={localizacao !== null}
          opcoes={opcoes}
          opcaoSelecionada={opcaoSelecionada}
          onSelecionarOpcao={setOpcaoSelecionada}
          calculando={calculandoRota}
          erro={erroRota}
          onFechar={handleFecharPlanejador}
          veiculosPorLinha={veiculosPorLinha}
          rastreando={veiculos !== null}
          favoritosIds={favoritosChaves}
          onFavoritoSalvo={handleFavoritoSalvo}
        />
      ) : (
        <button
          type="button"
          className="plan-abrir"
          onClick={() => setPlanejadorAberto(true)}
        >
          <Navigation size={16} />
          Para onde você vai?
        </button>
      )}
    </AppShell>
  );
}
