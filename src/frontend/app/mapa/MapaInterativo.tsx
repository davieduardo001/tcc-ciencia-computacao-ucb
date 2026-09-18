"use client";

import { useEffect, useRef, useState } from "react";
import {
  MapContainer,
  Marker,
  Polyline,
  Popup,
  TileLayer,
  useMapEvents,
} from "react-leaflet";
import L from "leaflet";
import { Bus, Crosshair, Layers, X } from "lucide-react";
import {
  buscarPosicoesDaLinha,
  LinhaDetalhada,
  OpcaoViagem,
  VeiculoAoVivo,
} from "@/lib/api";
import type { PontoEscolhido } from "./PlanejadorViagem";
import "leaflet/dist/leaflet.css";
import "./mapa.css";

// Base do mapa.
//
// O tile padrão do OpenStreetMap é denso e saturado — rodovia vermelha,
// mata verde forte, rótulo em toda quadra —, o que briga com tudo que
// desenhamos por cima: trajeto, paradas, ônibus ao vivo, marcadores de
// embarque. O CARTO Voyager é o meio-termo que queremos: legível, com
// cor suave o bastante pra deixar a informação do Movecity à frente.
//
// A questão é que a CARTO passou a exigir chave. Sem ela, o servidor
// responde 200 com um PNG válido, só que com "API KEY REQUIRED"
// estampado na imagem — dá pra passar por uma verificação de status
// HTTP sem que ninguém perceba, e só aparece quando alguém olha o mapa.
//
// A chave é gratuita (5 milhões de tiles/mês, sem conta e sem cartão,
// enviada na hora por e-mail em carto.com/basemaps/apikey), e projeto
// acadêmico ganha limite maior. Mesmo padrão do GOOGLE_CLIENT_ID: vive
// como secret do GitHub e entra no bundle em build time.
//
// Sem a chave configurada, cai pro tile padrão do OSM: mais carregado,
// mas funciona sempre e não depende de ninguém. Melhor um mapa feio do
// que um mapa carimbado.
type BaseDoMapa = {
  url: string;
  subdominios: string;
  zoomMaximo: number;
  atribuicao: string;
};

const BASE_CARTO_VOYAGER = (chave: string): BaseDoMapa => ({
  // O `{r}` é substituído pelo Leaflet por "@2x" em tela retina.
  url: `https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?key=${chave}`,
  // A CARTO serve quatro subdomínios; o padrão do Leaflet é só "abc".
  subdominios: "abcd",
  // Dois níveis além do padrão 18 do Leaflet ajudam a distinguir a
  // parada certa numa via com canteiro central.
  zoomMaximo: 20,
  atribuicao:
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
});

const BASE_OSM_PADRAO: BaseDoMapa = {
  url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  subdominios: "abc",
  zoomMaximo: 19,
  atribuicao:
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
};

/** Exportada para teste: a decisão depende de variável de ambiente. */
export function escolherBaseDoMapa(chaveCarto?: string): BaseDoMapa {
  const chave = (chaveCarto ?? "").trim();
  return chave ? BASE_CARTO_VOYAGER(chave) : BASE_OSM_PADRAO;
}

const BASE_MAPA = escolherBaseDoMapa(process.env.NEXT_PUBLIC_CARTO_API_KEY);

// Área-piloto Taguatinga/Ceilândia (DF), usada quando o navegador não
// consegue obter a posição real do usuário.
const PONTO_PADRAO = { lat: -15.8305, lng: -48.0425 };
const ZOOM_PADRAO = 14;
const ZOOM_LOCALIZADO = 16;

// De quanto em quanto tempo recarregamos a posição dos ônibus. O feed do
// SEMOB atualiza a cada poucos segundos e o backend já faz cache de 20s,
// então pedir mais rápido que isso só gastaria rede à toa.
const INTERVALO_POSICOES_MS = 20000;

const iconePosicaoAtual = L.divIcon({
  className: "mapa-icone-usuario",
  html: '<span class="mapa-icone-usuario-core"></span>',
  iconSize: [20, 20],
  iconAnchor: [10, 10],
});

// US #16 — ônibus ao vivo.
//
// Abaixo disso o ônibus é tratado como parado. Medido no feed: dos
// veículos que não mudaram de posição em 140 s, a grande maioria
// reportava velocidade ~0 — estão mesmo parados, não é dado velho.
const LIMIAR_PARADO_KMH = 3;

/**
 * "atualizado há 12s". O feed do SEMOB renova a posição de cada veículo
 * a cada ~28 s (medido), e a gente consulta a cada 20 s — então de vez
 * em quando a mesma posição aparece duas vezes seguidas. Mostrar a
 * idade do dado transforma isso de "o mapa travou" em informação.
 */
function descreverIdade(atualizadoEm: string): string {
  const quando = new Date(atualizadoEm).getTime();
  if (Number.isNaN(quando)) return "";

  const segundos = Math.max(0, Math.round((Date.now() - quando) / 1000));
  if (segundos < 60) return `Posição de ${segundos}s atrás`;

  const minutos = Math.round(segundos / 60);
  return `Posição de ${minutos} min atrás`;
}

/** O número da linha vem da API e entra em innerHTML — escapa. */
function escaparHtml(texto: string): string {
  return texto.replace(
    /[&<>"']/g,
    (c) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      })[c] as string
  );
}

const GLIFO_ONIBUS = `<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round"><rect x="4.5" y="3.5" width="15" height="12" rx="3"/><path d="M4.5 10.5h15"/><path d="M8 19.5v1M16 19.5v1"/><circle cx="8.5" cy="17.5" r="1.1" fill="currentColor" stroke="none"/><circle cx="15.5" cy="17.5" r="1.1" fill="currentColor" stroke="none"/></svg>`;

/**
 * Ícone do ônibus: pílula com o número da linha, sobre o ponto exato.
 *
 * A pílula fica acima do ponto e o ponto continua marcando a posição
 * real — a pílula é larga e, ancorada no centro, faria o veículo parecer
 * deslocado da via.
 *
 * O feed do SEMOB traz `direcao` em graus (0 = norte). Veículo parado não
 * ganha seta: apontar rumo em quem está com 0 km/h mostraria a direção da
 * última vez que andou, o que engana.
 *
 * `etaMinutos` ainda não vem do backend (é a US #19). Enquanto não vier, a
 * pílula mostra só o número da linha — sem separador e sem tempo. Estimar
 * aqui, por velocidade e distância em linha reta, seria inventar número.
 */
function criarIconeOnibus(
  direcao: number | null,
  parado: boolean,
  numeroLinha: string,
  etaMinutos?: number | null
) {
  const seta =
    direcao !== null && !parado
      ? `<span class="mapa-icone-onibus-seta" style="transform: rotate(${direcao}deg)"></span>`
      : "";
  const tempo =
    typeof etaMinutos === "number" && Number.isFinite(etaMinutos)
      ? ` · ${etaMinutos} min`
      : "";
  const rotulo = escaparHtml(numeroLinha) + tempo;

  return L.divIcon({
    className: "mapa-icone-onibus" + (parado ? " parado" : ""),
    html:
      `${seta}<span class="mapa-icone-onibus-core"></span>` +
      `<span class="mapa-onibus-pilula">` +
      `<span class="mapa-onibus-glifo">${GLIFO_ONIBUS}</span>` +
      `<span class="mapa-onibus-rotulo">${rotulo}</span>` +
      `</span>`,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  });
}

const iconeParada = L.divIcon({
  className: "mapa-icone-parada",
  html: '<span class="mapa-icone-parada-core"></span>',
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

// Paleta pra diferenciar o trajeto por cor quando houver mais de uma
// linha selecionada no mapa (PRD da US #17) — hoje só uma linha por
// vez é buscada, mas a cor já é derivada da própria linha em vez de
// fixa, então múltiplas linhas simultâneas não colidiriam visualmente.
const CORES_TRAJETO = ["#1aa0ad", "#c9760a", "#2f72e8", "#1aa05a", "#d6453d"];

function corDaLinha(numero: string): string {
  let hash = 0;
  for (let i = 0; i < numero.length; i++) {
    hash = (hash * 31 + numero.charCodeAt(i)) >>> 0;
  }
  return CORES_TRAJETO[hash % CORES_TRAJETO.length];
}

/**
 * 582 dos 7.142 abrigos do SEMOB não têm nome utilizável na fonte — o
 * endereço cadastrado é só o CEP. O backend manda string vazia nesses
 * casos em vez de exibir "CEP: 71596-265" como nome de parada.
 */
function nomeDaParada(nome: string): string {
  return nome || "Parada sem nome cadastrado";
}

/** Ângulo (graus, 0 = norte) do segmento entre dois pontos [lat, lng]. */
function calcularSentido(a: [number, number], b: [number, number]): number {
  const lat1 = (a[0] * Math.PI) / 180;
  const lat2 = (b[0] * Math.PI) / 180;
  const dLng = ((b[1] - a[1]) * Math.PI) / 180;

  const y = Math.sin(dLng) * Math.cos(lat2);
  const x =
    Math.cos(lat1) * Math.sin(lat2) -
    Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLng);

  return ((Math.atan2(y, x) * 180) / Math.PI + 360) % 360;
}

function criarIconeSentido(anguloGraus: number, cor: string) {
  return L.divIcon({
    className: "mapa-icone-sentido",
    html: `<span class="mapa-icone-sentido-seta" style="transform: rotate(${anguloGraus}deg); border-bottom-color: ${cor}"></span>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
}

// US #20 — marcadores do itinerário. Numerados pra casar com a ordem
// dos passos listados no painel do planejador.
function iconeViagem(rotulo: string, classe: string) {
  return L.divIcon({
    className: `mapa-icone-viagem ${classe}`,
    html: `<span>${rotulo}</span>`,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  });
}

const iconeOrigem = iconeViagem("A", "origem");
const iconeDestino = iconeViagem("B", "destino");

type StatusLocalizacao = "carregando" | "ok" | "indisponivel";

interface Coordenadas {
  lat: number;
  lng: number;
}

/**
 * Avisa quando o mapa está em zoom.
 *
 * O Leaflet reposiciona todos os marcadores ao dar zoom. Como o ícone
 * do ônibus tem `transition: transform` pra deslizar entre uma leitura
 * de GPS e a seguinte, sem desligar isso a frota inteira sairia
 * escorregando pela tela a cada zoom.
 */
function AvisaZoom({ onZoom }: { onZoom: (emZoom: boolean) => void }) {
  useMapEvents({
    zoomstart: () => onZoom(true),
    zoomend: () => onZoom(false),
  });
  return null;
}

/** US #20 — captura o clique no mapa quando o usuário está escolhendo um ponto. */
function CapturaCliqueNoMapa({
  ativo,
  onClique,
}: {
  ativo: boolean;
  onClique: (lat: number, lng: number) => void;
}) {
  useMapEvents({
    click(evento) {
      if (ativo) onClique(evento.latlng.lat, evento.latlng.lng);
    },
  });
  return null;
}

interface MapaInterativoProps {
  /** US #17 — linha buscada, com trajeto/paradas/sentido pra desenhar. */
  linha?: LinhaDetalhada | null;
  erroBusca?: string | null;
  onFecharLinha?: () => void;
  /** US #20 — itinerário escolhido no planejador, pra desenhar no mapa. */
  viagem?: OpcaoViagem | null;
  origemViagem?: PontoEscolhido | null;
  destinoViagem?: PontoEscolhido | null;
  /** Modo "escolher no mapa": qualquer clique vira coordenada. */
  escolhendoNoMapa?: boolean;
  onCliqueNoMapa?: (lat: number, lng: number) => void;
  /** Reporta a posição do usuário pra fora (o planejador usa em "minha localização"). */
  onLocalizacao?: (coordenadas: Coordenadas | null) => void;
  /** US #16 + #20 — repassa os ônibus rastreados pra que o painel do
   * itinerário possa mostrar quantos estão rodando em cada perna. */
  onVeiculos?: (veiculos: VeiculoAoVivo[]) => void;
}

export default function MapaInterativo({
  linha,
  erroBusca,
  onFecharLinha,
  viagem,
  origemViagem,
  destinoViagem,
  escolhendoNoMapa = false,
  onCliqueNoMapa,
  onLocalizacao,
  onVeiculos,
}: MapaInterativoProps) {
  const [coordenadas, setCoordenadas] = useState<Coordenadas | null>(null);
  const [status, setStatus] = useState<StatusLocalizacao>("carregando");
  const [veiculos, setVeiculos] = useState<VeiculoAoVivo[]>([]);
  const [buscouPosicoes, setBuscouPosicoes] = useState(false);
  const [emZoom, setEmZoom] = useState(false);
  const mapRef = useRef<L.Map | null>(null);
  const jaCentralizouRef = useRef(false);

  useEffect(() => {
    if (!("geolocation" in navigator)) {
      setStatus("indisponivel");
      return;
    }

    function aoObterPosicao(posicao: GeolocationPosition) {
      setCoordenadas({
        lat: posicao.coords.latitude,
        lng: posicao.coords.longitude,
      });
      setStatus("ok");
    }

    function aoFalharPosicao() {
      setStatus("indisponivel");
    }

    navigator.geolocation.getCurrentPosition(aoObterPosicao, aoFalharPosicao, {
      enableHighAccuracy: true,
      timeout: 10000,
    });

    const watchId = navigator.geolocation.watchPosition(
      aoObterPosicao,
      aoFalharPosicao,
      { enableHighAccuracy: true }
    );

    return () => navigator.geolocation.clearWatch(watchId);
  }, []);

  useEffect(() => {
    if (status === "ok" && coordenadas && !jaCentralizouRef.current && mapRef.current) {
      mapRef.current.setView([coordenadas.lat, coordenadas.lng], ZOOM_LOCALIZADO);
      jaCentralizouRef.current = true;
    }
  }, [status, coordenadas]);

  // O planejador (US #20) precisa da posição pra oferecer "usar minha
  // localização". Quem fala com a Geolocation API é este componente, então
  // ele repassa pra cima em vez de duplicar o watchPosition.
  useEffect(() => {
    onLocalizacao?.(status === "ok" ? coordenadas : null);
  }, [status, coordenadas, onLocalizacao]);

  // Mesma ideia para os ônibus rastreados: quem faz o polling é este
  // componente, e o painel do itinerário precisa do resultado.
  useEffect(() => {
    onVeiculos?.(veiculos);
  }, [veiculos, onVeiculos]);

  // US #20 — enquadra o itinerário inteiro ao escolher uma opção.
  useEffect(() => {
    if (!viagem || !mapRef.current) return;

    const pontos = viagem.pernas.flatMap((perna) => perna.trajeto);
    if (origemViagem) pontos.push([origemViagem.lat, origemViagem.lng]);
    if (destinoViagem) pontos.push([destinoViagem.lat, destinoViagem.lng]);
    if (pontos.length === 0) return;

    mapRef.current.fitBounds(L.latLngBounds(pontos), { padding: [56, 56] });
  }, [viagem, origemViagem, destinoViagem]);

  // US #17, cenário 1 + PRD: ao selecionar uma linha, o mapa ajusta o
  // zoom automaticamente pra mostrar o trajeto inteiro.
  useEffect(() => {
    if (linha && linha.trajeto.length > 0 && mapRef.current) {
      mapRef.current.fitBounds(L.latLngBounds(linha.trajeto), {
        padding: [48, 48],
      });
    }
  }, [linha]);

  // US #16 — linhas a rastrear: a que foi buscada pelo número, ou as
  // que compõem o itinerário escolhido no planejador (US #20).
  //
  // Rastrear o itinerário também é o que faz o recurso ter serventia na
  // prática: quem planeja "Taguatinga → UCB" quer saber onde está o
  // ônibus que vai pegar, e antes só dava pra ver isso buscando a linha
  // pelo número numa segunda busca.
  //
  // `join` em vez do array para a dependência do efeito: um array novo
  // a cada render reiniciaria o polling sem parar.
  const linhasRastreadas = linha
    ? [linha.numero]
    : viagem
      ? Array.from(new Set(viagem.pernas.map((p) => p.numero)))
      : [];
  const chaveRastreio = linhasRastreadas.join(",");

  useEffect(() => {
    if (!chaveRastreio) {
      setVeiculos([]);
      setBuscouPosicoes(false);
      return;
    }

    const numeros = chaveRastreio.split(",");
    let ativo = true;

    async function atualizar() {
      // Uma chamada por linha, em paralelo. O backend cacheia o feed do
      // SEMOB, então isso não multiplica o download da origem.
      const porLinha = await Promise.all(
        // Arrow explícita: passar a função direto pro map mandaria
        // índice e array como argumentos extras.
        numeros.map((numero) => buscarPosicoesDaLinha(numero))
      );
      if (!ativo) return;
      setVeiculos(porLinha.flat());
      setBuscouPosicoes(true);
    }

    atualizar();
    const intervalo = setInterval(atualizar, INTERVALO_POSICOES_MS);

    return () => {
      ativo = false;
      clearInterval(intervalo);
    };
  }, [chaveRastreio]);

  function centralizarNaMinhaLocalizacao() {
    if (coordenadas && mapRef.current) {
      mapRef.current.setView([coordenadas.lat, coordenadas.lng], ZOOM_LOCALIZADO);
    }
  }

  const corLinha = linha ? corDaLinha(linha.numero) : undefined;

  // US #17, cenário 3: seta indicando o sentido de operação, posicionada
  // no meio do trajeto e apontando pra direção do segmento seguinte.
  let marcadorSentido: { posicao: [number, number]; angulo: number } | null = null;
  if (linha && linha.trajeto.length >= 2) {
    const meio = Math.floor(linha.trajeto.length / 2);
    const indiceAtual = Math.min(meio, linha.trajeto.length - 2);
    marcadorSentido = {
      posicao: linha.trajeto[indiceAtual],
      angulo: calcularSentido(
        linha.trajeto[indiceAtual],
        linha.trajeto[indiceAtual + 1]
      ),
    };
  }

  return (
    <div
      className={
        "mapa-canvas" +
        (escolhendoNoMapa ? " escolhendo-ponto" : "") +
        (emZoom ? " em-zoom" : "")
      }
    >
      {escolhendoNoMapa && (
        <div className="mapa-aviso destaque" role="status">
          Toque no mapa para escolher o ponto.
        </div>
      )}

      {status === "indisponivel" && (
        <div className="mapa-aviso" role="alert">
          Não foi possível obter sua localização. Exibindo a região padrão
          (Taguatinga/Ceilândia).
        </div>
      )}

      {erroBusca && (
        <div className="mapa-aviso" role="alert">
          {erroBusca}
        </div>
      )}

      <MapContainer
        center={[PONTO_PADRAO.lat, PONTO_PADRAO.lng]}
        zoom={ZOOM_PADRAO}
        ref={mapRef}
        className="mapa-leaflet"
      >
        <TileLayer
          attribution={BASE_MAPA.atribuicao}
          url={BASE_MAPA.url}
          subdomains={BASE_MAPA.subdominios}
          maxZoom={BASE_MAPA.zoomMaximo}
        />
        <CapturaCliqueNoMapa
          ativo={escolhendoNoMapa}
          onClique={(lat, lng) => onCliqueNoMapa?.(lat, lng)}
        />
        <AvisaZoom onZoom={setEmZoom} />

        {coordenadas && (
          <Marker
            position={[coordenadas.lat, coordenadas.lng]}
            icon={iconePosicaoAtual}
          />
        )}

        {/* US #20 — itinerário: uma polilinha por perna, cores distintas
            pra deixar claro onde termina um ônibus e começa o outro. */}
        {viagem && (
          <>
            {viagem.pernas.map((perna, indice) => (
              <Polyline
                key={`${perna.numero}-${perna.sentido}-${indice}`}
                positions={perna.trajeto}
                pathOptions={{
                  color: corDaLinha(perna.numero),
                  weight: 6,
                  opacity: 0.9,
                }}
              />
            ))}

            {viagem.pernas.map((perna, indice) => (
              <Marker
                key={`embarque-${indice}`}
                position={[perna.embarque.lat, perna.embarque.lng]}
                icon={iconeViagem(
                  String(indice + 1),
                  indice === 0 ? "embarque" : "baldeacao"
                )}
              >
                <Popup>
                  <strong>{perna.numero}</strong>
                  <br />
                  {indice === 0 ? "Embarque" : "Baldeação"} em{" "}
                  {perna.embarque.parada_nome || "ponto no mapa"}
                </Popup>
              </Marker>
            ))}

            {(() => {
              const ultima = viagem.pernas[viagem.pernas.length - 1];
              return (
                <Marker
                  position={[ultima.desembarque.lat, ultima.desembarque.lng]}
                  icon={iconeViagem("↓", "desembarque")}
                >
                  <Popup>
                    Desça em{" "}
                    {ultima.desembarque.parada_nome || "ponto no mapa"}
                  </Popup>
                </Marker>
              );
            })()}
          </>
        )}

        {origemViagem && (
          <Marker
            position={[origemViagem.lat, origemViagem.lng]}
            icon={iconeOrigem}
          >
            <Popup>{origemViagem.nome}</Popup>
          </Marker>
        )}

        {destinoViagem && (
          <Marker
            position={[destinoViagem.lat, destinoViagem.lng]}
            icon={iconeDestino}
          >
            <Popup>{destinoViagem.nome}</Popup>
          </Marker>
        )}

        {linha && (
          <>
            <Polyline
              positions={linha.trajeto}
              pathOptions={{ color: corLinha, weight: 5, opacity: 0.85 }}
            />

            {linha.paradas.map((parada, indice) => (
              <Marker
                key={`${parada.nome}-${indice}`}
                position={[parada.lat, parada.lng]}
                icon={iconeParada}
              >
                {/* Cenário 2 da US #17: nome da parada ao tocar/clicar */}
                <Popup>{nomeDaParada(parada.nome)}</Popup>
              </Marker>
            ))}


            {marcadorSentido && (
              <Marker
                position={marcadorSentido.posicao}
                icon={criarIconeSentido(marcadorSentido.angulo, corLinha!)}
                interactive={false}
              />
            )}
          </>
        )}

        {/* US #16 — fora do bloco da linha de propósito: os ônibus também
            aparecem quando o que está na tela é um itinerário da US #20. */}
        {veiculos.map((veiculo) => {
          const parado = (veiculo.velocidade ?? 0) < LIMIAR_PARADO_KMH;
          return (
            <Marker
              // Chave estável por veículo: é o que preserva o elemento no
              // DOM entre as atualizações, e sem isso a transição CSS que
              // faz o ônibus deslizar não teria de onde partir.
              key={`${veiculo.linha}-${veiculo.prefixo}`}
              position={[veiculo.lat, veiculo.lng]}
              icon={criarIconeOnibus(veiculo.direcao, parado, veiculo.linha)}
            >
              <Popup>
                <strong>{veiculo.linha}</strong> · carro {veiculo.prefixo}
                <br />
                {veiculo.sentido
                  ? `Sentido ${veiculo.sentido.toLowerCase()}`
                  : "Em operação"}
                {veiculo.velocidade !== null && (
                  <>
                    {" · "}
                    {parado ? "parado" : `${Math.round(veiculo.velocidade)} km/h`}
                  </>
                )}
                <br />
                <small>{descreverIdade(veiculo.atualizadoEm)}</small>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      <div className="mapa-controles">
        <button
          type="button"
          className="mapa-botao-icone"
          title="Centralizar na minha localização"
          onClick={centralizarNaMinhaLocalizacao}
          disabled={!coordenadas}
        >
          <Crosshair size={18} />
        </button>
        <button type="button" className="mapa-botao-icone" title="Camadas">
          <Layers size={18} />
        </button>
      </div>

      {linha && (
        <aside className="mapa-painel-linha">
          <div className="mapa-painel-cabecalho">
            <button
              type="button"
              className="mapa-botao-icone"
              title="Fechar"
              onClick={onFecharLinha}
            >
              <X size={16} />
            </button>
            <div>
              <strong>{linha.nome}</strong>
              <span className="mapa-painel-sentido">{linha.sentido}</span>
            </div>
          </div>

          <div className="mapa-painel-corpo">
            {/* US #16 — cenários 1 e 3 */}
            <div className="mapa-painel-aovivo" role="status">
              {veiculos.length > 0 ? (
                <>
                  <span className="mapa-pulso" />
                  <Bus size={15} />
                  <span>
                    <strong>
                      {veiculos.length}{" "}
                      {veiculos.length === 1 ? "ônibus" : "ônibus"}
                    </strong>{" "}
                    em operação agora
                  </span>
                </>
              ) : (
                <span className="mapa-painel-sem-veiculo">
                  {buscouPosicoes
                    ? "Nenhum ônibus desta linha em operação no momento."
                    : "Procurando ônibus em operação..."}
                </span>
              )}
            </div>

            <div className="mapa-painel-titulo">Trajeto e paradas</div>
            <div className="mapa-timeline">
              {linha.paradas.map((parada, indice) => (
                <div className="mapa-timeline-passo" key={`${parada.nome}-${indice}`}>
                  <span
                    className={
                      "mapa-timeline-no" +
                      (indice === 0 ? " inicio" : "") +
                      (indice === linha.paradas.length - 1 ? " fim" : "")
                    }
                  />
                  <span className="mapa-timeline-rotulo">
                    {nomeDaParada(parada.nome)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </aside>
      )}
    </div>
  );
}
