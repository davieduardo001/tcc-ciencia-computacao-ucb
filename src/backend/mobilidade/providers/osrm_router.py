# Road-snapping via OSRM — servidor demo público, sem API key.
#
# O LinhaMockProvider só conhece 3-4 pontos crus por linha (os próprios
# pontos das paradas) — desenhado direto no Leaflet, isso vira uma reta
# entre eles, cortando quarteirão, ignorando rua. Este módulo passa
# esses pontos como waypoints pro OSRM e recebe de volta uma geometria
# real, seguindo as ruas de verdade do OpenStreetMap (mesma fonte de
# mapa que o app já usa).
#
# Best-effort e isolado: se o OSRM falhar (fora do ar, timeout, rota
# impossível), devolve None — quem chama cai de volta pros pontos
# originais. Nunca deve derrubar uma busca de linha por causa disso.
#
# Não usado pelo LinhaGoogleMapsProvider — a Routes API já devolve
# geometria real, road-snapping seria redundante ali.

from __future__ import annotations

import httpx

_OSRM_URL_BASE = "https://router.project-osrm.org/route/v1/driving/"


async def rotear(pontos: list[tuple[float, float]]) -> list[tuple[float, float]] | None:
    """
    Recebe uma lista de pontos [(lat, lng), ...] (>= 2) e devolve uma
    geometria de rota real passando por eles, na mesma ordem, ou None
    se o OSRM não conseguiu (rede, timeout, sem rota encontrada).
    """
    if len(pontos) < 2:
        return None

    # OSRM espera "lng,lat;lng,lat;..." (ordem invertida da nossa).
    coordenadas = ";".join(f"{lng},{lat}" for lat, lng in pontos)

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                f"{_OSRM_URL_BASE}{coordenadas}",
                params={"overview": "full", "geometries": "geojson"},
            )
            resp.raise_for_status()
            dados = resp.json()
    except (httpx.HTTPError, ValueError):
        return None

    rotas = dados.get("routes") or []
    if not rotas:
        return None

    geometria = rotas[0].get("geometry", {}).get("coordinates") or []
    if not geometria:
        return None

    return [(lat, lng) for lng, lat in geometria]
