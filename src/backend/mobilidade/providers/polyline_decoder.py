# Decodificador de "Google Encoded Polyline" (precisão 5).
#
# Formato padrão usado pela Routes/Directions API do Google Maps para
# comprimir uma sequência de pontos [lat, lng] em uma única string.
# Implementação própria (algoritmo público, sem dependência externa) —
# ver https://developers.google.com/maps/documentation/utilities/polylinealgorithm

from __future__ import annotations


def decodificar_polyline(codificada: str) -> list[tuple[float, float]]:
    """
    Decodifica uma polyline codificada do Google Maps em uma lista de
    pontos (lat, lng) com 5 casas decimais de precisão.

    Retorna lista vazia para entrada vazia. Não lança exceção para
    entrada malformada além dos erros naturais de índice do Python.
    """
    if not codificada:
        return []

    pontos: list[tuple[float, float]] = []
    indice = 0
    lat = 0
    lng = 0
    tamanho = len(codificada)

    while indice < tamanho:
        lat += _decodificar_valor(codificada, indice)
        indice += _bytes_consumidos(codificada, indice)

        lng += _decodificar_valor(codificada, indice)
        indice += _bytes_consumidos(codificada, indice)

        pontos.append((lat / 1e5, lng / 1e5))

    return pontos


def _bytes_consumidos(codificada: str, indice: int) -> int:
    consumidos = 0
    while True:
        byte = ord(codificada[indice + consumidos]) - 63
        consumidos += 1
        if byte < 0x20:
            break
    return consumidos


def _decodificar_valor(codificada: str, indice: int) -> int:
    resultado = 0
    shift = 0
    while True:
        byte = ord(codificada[indice]) - 63
        indice += 1
        resultado |= (byte & 0x1F) << shift
        shift += 5
        if byte < 0x20:
            break

    if resultado & 1:
        return ~(resultado >> 1)
    return resultado >> 1
