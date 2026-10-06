"use client";

import Link from "next/link";
import { Bus, Navigation, Route, Star } from "lucide-react";
import { RotaFavorita } from "@/lib/api";

/** Quantas favoritas cabem no destaque; o resto fica em /favoritos. */
const MAX_VISIVEIS = 3;

interface FavoritosDestaqueProps {
  favoritos: RotaFavorita[];
  /** Cenário 2 da US #25: acesso direto ao rastreamento da linha. */
  onRastrear: (numeroLinha: string) => void;
  /** Reabre a rota salva no planejador, já calculada. */
  onAbrirRota: (favorito: RotaFavorita) => void;
}

/**
 * US #25 — Rotas favoritas em destaque na tela principal do mapa.
 * Só renderiza quando o usuário tem ao menos uma favorita.
 */
export default function FavoritosDestaque({
  favoritos,
  onRastrear,
  onAbrirRota,
}: FavoritosDestaqueProps) {
  if (favoritos.length === 0) return null;

  const visiveis = favoritos.slice(0, MAX_VISIVEIS);

  return (
    <section className="fav-destaque" aria-label="Minhas rotas favoritas">
      <header className="fav-destaque-topo">
        <Star size={14} fill="currentColor" />
        <h2>Minhas rotas</h2>
        {favoritos.length > MAX_VISIVEIS && (
          <Link href="/favoritos" className="fav-destaque-todas">
            Ver todas ({favoritos.length})
          </Link>
        )}
      </header>
      <ul>
        {visiveis.map((fav) => (
          <li key={fav.id} className="fav-destaque-item">
            <div className="fav-destaque-texto">
              <strong>{fav.label}</strong>
              <span>
                <Bus size={12} /> {fav.numero_linha}
              </span>
            </div>
            <button
              type="button"
              onClick={() => onRastrear(fav.numero_linha)}
              aria-label={`Rastrear linha ${fav.numero_linha} (${fav.label})`}
              title="Rastrear a linha"
            >
              <Navigation size={14} />
              Rastrear
            </button>
            <button
              type="button"
              onClick={() => onAbrirRota(fav)}
              aria-label={`Abrir rota ${fav.label}`}
              title="Ver a rota no planejador"
            >
              <Route size={14} />
              Rota
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
