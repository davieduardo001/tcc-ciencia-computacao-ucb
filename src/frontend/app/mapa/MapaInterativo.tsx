"use client";

import { useEffect, useRef, useState } from "react";
import { MapContainer, Marker, Polyline, Popup, TileLayer } from "react-leaflet";
import L from "leaflet";
import { Crosshair, Layers, X } from "lucide-react";
import { LinhaDetalhada } from "@/lib/api";
import "leaflet/dist/leaflet.css";
import "./mapa.css";

// Ponto padrão: área-piloto Taguatinga/Ceilândia (DF), usada quando o
// navegador não consegue obter a posição real do usuário.
const PONTO_PADRAO = { lat: -15.8305, lng: -48.0425 };
const ZOOM_PADRAO = 14;
const ZOOM_LOCALIZADO = 16;

const iconePosicaoAtual = L.divIcon({
  className: "mapa-icone-usuario",
  html: '<span class="mapa-icone-usuario-core"></span>',
  iconSize: [20, 20],
  iconAnchor: [10, 10],
});

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

type StatusLocalizacao = "carregando" | "ok" | "indisponivel";

interface Coordenadas {
  lat: number;
  lng: number;
}

interface MapaInterativoProps {
  /** US #17 — linha buscada, com trajeto/paradas/sentido pra desenhar. */
  linha?: LinhaDetalhada | null;
  erroBusca?: string | null;
  onFecharLinha?: () => void;
}

export default function MapaInterativo({
  linha,
  erroBusca,
  onFecharLinha,
}: MapaInterativoProps) {
  const [coordenadas, setCoordenadas] = useState<Coordenadas | null>(null);
  const [status, setStatus] = useState<StatusLocalizacao>("carregando");
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

  // US #17, cenário 1 + PRD: ao selecionar uma linha, o mapa ajusta o
  // zoom automaticamente pra mostrar o trajeto inteiro.
  useEffect(() => {
    if (linha && linha.trajeto.length > 0 && mapRef.current) {
      mapRef.current.fitBounds(L.latLngBounds(linha.trajeto), {
        padding: [48, 48],
      });
    }
  }, [linha]);

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
    <div className="mapa-canvas">
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
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {coordenadas && (
          <Marker
            position={[coordenadas.lat, coordenadas.lng]}
            icon={iconePosicaoAtual}
          />
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
                <Popup>{parada.nome}</Popup>
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
                  <span className="mapa-timeline-rotulo">{parada.nome}</span>
                </div>
              ))}
            </div>
          </div>
        </aside>
      )}
    </div>
  );
}
