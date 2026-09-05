"use client";

import dynamic from "next/dynamic";
import AppShell from "./AppShell";

const MapaInterativo = dynamic(() => import("./MapaInterativo"), {
  ssr: false,
  loading: () => <p className="mapa-carregando">Carregando mapa...</p>,
});

export default function MapaPage() {
  return (
    <AppShell active="mapa">
      <MapaInterativo />
    </AppShell>
  );
}
