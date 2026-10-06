"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Bus, MapPin, Navigation, Star, Trash2, WifiOff } from "lucide-react";
import AppShell from "../mapa/AppShell";
import {
  cachearFavoritos,
  lerFavoritosCache,
  listarFavoritosRemoto,
  removerFavorito,
  RotaFavorita,
  SalvarFavoritoError,
} from "@/lib/api";
import "./favoritos.css";

/**
 * US #25 — Tela "Minhas Rotas" / Rotas Salvas.
 *
 * Exibe as rotas favoritas do usuário, permite removê-las e navegar
 * para o mapa com a rota pré-calculada (Cenário 2 da US).
 *
 * Estratégia de cache:
 * 1. Exibe imediatamente o cache local (acesso rápido / offline).
 * 2. Busca do servidor em background e atualiza a lista quando volta.
 * 3. Sem servidor (offline), mantém o cache com banner informativo.
 */
export default function FavoritosPage() {
  const router = useRouter();
  const [favoritos, setFavoritos] = useState<RotaFavorita[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [offline, setOffline] = useState(false);
  const [removendo, setRemovendo] = useState<string | null>(null);
  const [erroRemover, setErroRemover] = useState<string | null>(null);

  useEffect(() => {
    // Exibe o cache imediatamente para não deixar a tela em branco.
    const cache = lerFavoritosCache();
    if (cache.length > 0) {
      setFavoritos(cache);
      setCarregando(false);
    }

    // Busca do servidor em background.
    listarFavoritosRemoto()
      .then((lista) => {
        setFavoritos(lista);
        setOffline(false);
      })
      .catch(() => {
        // Servidor inalcançável: mantém o cache já exibido e avisa.
        setOffline(true);
      })
      .finally(() => setCarregando(false));
  }, []);

  async function handleRemover(id: string) {
    setRemovendo(id);
    setErroRemover(null);
    try {
      await removerFavorito(id);
      // Remove da lista local e atualiza o cache (fora do updater: ele
      // precisa ser puro).
      const nova = favoritos.filter((f) => f.id !== id);
      setFavoritos(nova);
      cachearFavoritos(nova);
    } catch (err) {
      if (err instanceof SalvarFavoritoError) {
        setErroRemover(err.message);
      } else {
        setErroRemover("Não foi possível remover o favorito.");
      }
    } finally {
      setRemovendo(null);
    }
  }

  function handleIrParaRota(favorito: RotaFavorita) {
    // Navega para o mapa com o planejador aberto e os pontos pré-preenchidos.
    // O mapa/page.tsx lê esses query params e preenche origem/destino
    // automaticamente, disparando o cálculo da rota.
    const params = new URLSearchParams({
      painel: "rotas",
      origem_lat: String(favorito.origem_lat),
      origem_lng: String(favorito.origem_lng),
      destino_lat: String(favorito.destino_lat),
      destino_lng: String(favorito.destino_lng),
    });
    // Inclui o label como nome legível dos pontos.
    // O label é montado como "origem → destino" (com espaços) ao salvar.
    const separador = favorito.label.indexOf(" → ");
    if (separador > 0) {
      params.set("origem_nome", favorito.label.slice(0, separador).trim());
      params.set("destino_nome", favorito.label.slice(separador + 3).trim());
    }

    router.push(`/mapa?${params.toString()}`);
  }

  return (
    <AppShell active="favoritos">
      <div className="fav-page">
        <div className="fav-cabecalho">
          <Star size={20} />
          <h1>Minhas Rotas</h1>
        </div>

        {offline && (
          <div className="fav-banner-offline" role="status">
            <WifiOff size={14} />
            <span>Você está offline. Exibindo rotas salvas anteriormente.</span>
          </div>
        )}

        {erroRemover && (
          <p className="fav-erro" role="alert">
            {erroRemover}
          </p>
        )}

        {carregando && favoritos.length === 0 ? (
          <p className="fav-carregando">Carregando suas rotas favoritas...</p>
        ) : favoritos.length === 0 ? (
          <div className="fav-vazio">
            <Star size={40} strokeWidth={1} />
            <p>Você ainda não salvou nenhuma rota.</p>
            <p className="fav-vazio-dica">
              Calcule uma rota no mapa e clique na estrela para salvá-la aqui.
            </p>
            <button
              type="button"
              className="fav-btn-ir-mapa"
              onClick={() => router.push("/mapa?painel=rotas")}
            >
              <Navigation size={16} /> Ir para o mapa
            </button>
          </div>
        ) : (
          <ul className="fav-lista">
            {favoritos.map((fav) => (
              <li key={fav.id} className="fav-card">
                <div className="fav-card-corpo">
                  <strong className="fav-label">{fav.label}</strong>
                  <div className="fav-linha-info">
                    <Bus size={13} />
                    <span>
                      <strong>{fav.numero_linha}</strong>
                      {fav.nome_linha !== fav.numero_linha && (
                        <em> — {fav.nome_linha.replace(fav.numero_linha, "").replace(/^[\s—–-]+/, "")}</em>
                      )}
                    </span>
                  </div>
                  <div className="fav-coords">
                    <MapPin size={12} />
                    <span>
                      {fav.origem_lat.toFixed(4)}, {fav.origem_lng.toFixed(4)}
                      {" → "}
                      {fav.destino_lat.toFixed(4)}, {fav.destino_lng.toFixed(4)}
                    </span>
                  </div>
                </div>
                <div className="fav-card-acoes">
                  <button
                    type="button"
                    className="fav-btn-ir"
                    onClick={() => handleIrParaRota(fav)}
                    title="Abrir rota no mapa"
                    aria-label={`Abrir rota ${fav.label} no mapa`}
                  >
                    <Navigation size={15} />
                    <span>Ir</span>
                  </button>
                  <button
                    type="button"
                    className="fav-btn-remover"
                    onClick={() => handleRemover(fav.id)}
                    disabled={removendo === fav.id}
                    title="Remover dos favoritos"
                    aria-label={`Remover ${fav.label} dos favoritos`}
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </AppShell>
  );
}
