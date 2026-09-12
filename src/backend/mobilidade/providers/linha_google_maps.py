# Provider real de LinhaProvider — US #15
#
# Consulta a Routes API do Google Maps (mode=TRANSIT) para obter paradas,
# trajeto e horário estimado de uma linha. Como a Routes API responde por
# par origem→destino (não por "número de linha"), mantemos aqui um mapa
# manual dos terminais de cada linha piloto (Taguatinga/Ceilândia).
#
# IMPORTANTE — status: implementação AINDA NÃO validada contra a API real
# (aguardando GOOGLE_MAPS_API_KEY, ver docs/pesquisa-integracao-onibus-df.md).
# Os caminhos do JSON de resposta usados abaixo seguem a documentação
# pública da Routes API (computeRoutes, travelMode=TRANSIT), mas PRECISAM
# ser confirmados com uma chamada real antes de considerar isso pronto
# para produção — em especial `horarios_previstos`, que a Routes API só
# devolve para o horário consultado (não é uma tabela de horários; ver
# ressalva no docstring de buscar_linha).
#
# Terminais abaixo são endereços de referência para geocoding do próprio
# Google — ainda não confirmados com fonte oficial (DFTRANS/SEMOB).

from __future__ import annotations

import httpx

from mobilidade.providers.contratos import LinhaEncontrada, LinhaProvider, ParadaLinha
from mobilidade.providers.polyline_decoder import decodificar_polyline
from shared.config import get_settings

_ROUTES_API_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

# numero_linha -> (endereço origem, endereço destino, nome, sentido)
# TODO: confirmar terminais reais com o DFTRANS/SEMOB antes de produção.
_TERMINAIS_LINHAS_PILOTO: dict[str, tuple[str, str, str, str]] = {
    "0.110": (
        "Terminal Taguatinga Centro, Taguatinga, DF",
        "Rodoviária do Plano Piloto, Brasília, DF",
        "0.110 — Taguatinga / Rodoviária",
        "Taguatinga → Rodoviária do Plano Piloto",
    ),
    "0.108": (
        "Terminal Ceilândia Centro, Ceilândia, DF",
        "Rodoviária do Plano Piloto, Brasília, DF",
        "0.108 — Ceilândia / Plano Piloto",
        "Ceilândia → Plano Piloto",
    ),
}

_FIELD_MASK = (
    "routes.legs.steps.transitDetails,"
    "routes.legs.duration,"
    "routes.polyline.encodedPolyline"
)


class LinhaGoogleMapsProvider:
    """
    Provider real de linhas via Routes API do Google Maps.

    Só busca linhas presentes em _TERMINAIS_LINHAS_PILOTO — qualquer outro
    número resulta em None (mesmo comportamento de "linha não encontrada"
    do mock, já que ainda não temos uma fonte que cubra todas as linhas
    do DF).
    """

    def __init__(self) -> None:
        self._api_key = get_settings().GOOGLE_MAPS_API_KEY

    async def buscar_linha(self, numero_linha: str) -> LinhaEncontrada | None:
        terminais = _TERMINAIS_LINHAS_PILOTO.get(numero_linha)
        if terminais is None:
            return None

        origem, destino, nome, sentido = terminais

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                _ROUTES_API_URL,
                json={
                    "origin": {"address": origem},
                    "destination": {"address": destino},
                    "travelMode": "TRANSIT",
                },
                headers={
                    "X-Goog-Api-Key": self._api_key,
                    "X-Goog-FieldMask": _FIELD_MASK,
                },
            )
            resp.raise_for_status()
            dados = resp.json()

        rotas = dados.get("routes") or []
        if not rotas:
            return None

        rota = rotas[0]
        polyline_codificada = rota.get("polyline", {}).get("encodedPolyline", "")
        trajeto = decodificar_polyline(polyline_codificada)

        paradas: list[ParadaLinha] = []
        horarios_previstos: list[str] = []

        for leg in rota.get("legs", []):
            for step in leg.get("steps", []):
                detalhes = step.get("transitDetails")
                if not detalhes:
                    continue

                partida = detalhes.get("stopDetails", {}).get("departureStop", {})
                chegada = detalhes.get("stopDetails", {}).get("arrivalStop", {})

                for parada_bruta in (partida, chegada):
                    ponto = parada_bruta.get("location", {}).get("latLng")
                    if ponto and parada_bruta.get("name"):
                        paradas.append(
                            ParadaLinha(
                                nome=parada_bruta["name"],
                                lat=ponto["latitude"],
                                lng=ponto["longitude"],
                            )
                        )

                horario = detalhes.get("stopDetails", {}).get("departureTime")
                if horario:
                    horarios_previstos.append(horario)

        return LinhaEncontrada(
            numero=numero_linha,
            nome=nome,
            sentido=sentido,
            paradas=paradas,
            trajeto=trajeto,
            horarios_previstos=horarios_previstos,
        )


# Verificação estática: garante que LinhaGoogleMapsProvider satisfaz o
# contrato em tempo de importação, antes de qualquer execução da rota.
assert isinstance(LinhaGoogleMapsProvider(), LinhaProvider), (
    "LinhaGoogleMapsProvider não satisfaz o contrato LinhaProvider. "
    "Verifique se o método buscar_linha está correto."
)
