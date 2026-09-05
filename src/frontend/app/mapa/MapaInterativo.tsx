"use client";

import { useEffect, useRef, useState } from "react";
import { MapContainer, Marker, TileLayer } from "react-leaflet";
import L from "leaflet";
import { Crosshair, Layers } from "lucide-react";
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

type StatusLocalizacao = "carregando" | "ok" | "indisponivel";

interface Coordenadas {
  lat: number;
  lng: number;
}

export default function MapaInterativo() {
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

  function centralizarNaMinhaLocalizacao() {
    if (coordenadas && mapRef.current) {
      mapRef.current.setView([coordenadas.lat, coordenadas.lng], ZOOM_LOCALIZADO);
    }
  }

  return (
    <div className="mapa-canvas">
      {status === "indisponivel" && (
        <div className="mapa-aviso" role="alert">
          Não foi possível obter sua localização. Exibindo a região padrão
          (Taguatinga/Ceilândia).
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
    </div>
  );
}
