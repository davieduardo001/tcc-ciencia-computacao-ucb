# Fonte de dados real das linhas do DF — SEMOB (dados.semob.df.gov.br)
#
# Endpoints públicos, sem chave e sem billing, que alimentam o próprio
# app oficial "DF no Ponto":
#
#   /espaciais  1.408 trajetos (923 linhas x IDA/VOLTA/CIRCULAR), GeoJSON
#               LineString já seguindo rua. ~28 MB.
#   /horario    horários por linha/sentido, com dias da semana. ~6.5 MB.
#   /pontos     7.140 abrigos de parada com lat/lng e endereço. ~2.2 MB.
#   /posicao    GPS ao vivo da frota (usado pela US #16, não aqui).
#
# Nenhum deles aceita filtro por query string — sempre devolvem o payload
# inteiro. Por isso a leitura é feita em lote pela ingestão
# (ingestao_semob.py), que popula a tabela `linha`, e não a cada busca de
# usuário.
#
# Ressalva registrada em docs/pesquisa-integracao-onibus-df.md: são
# endpoints públicos de domínio oficial, mas sem documentação/SLA
# publicados. Por isso os dados são copiados para o nosso banco — se o
# SEMOB sair do ar, a busca continua funcionando com o último snapshot.

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

import httpx

BASE_URL = "https://dados.semob.df.gov.br"

URL_ESPACIAIS = f"{BASE_URL}/espaciais"
URL_HORARIO = f"{BASE_URL}/horario"
URL_PONTOS = f"{BASE_URL}/pontos"
URL_POSICAO = f"{BASE_URL}/posicao"

# /horario abrevia o sentido; /espaciais escreve por extenso.
SENTIDO_POR_INICIAL = {"I": "IDA", "V": "VOLTA", "C": "CIRCULAR"}

# Quando uma linha tem mais de um sentido, esse é o que vira o trajeto
# exibido (a tabela `linha` guarda um trajeto por número de linha).
PRIORIDADE_SENTIDO = {"CIRCULAR": 0, "IDA": 1, "VOLTA": 2}

_ARQUIVO_NOMES = Path(__file__).parent / "dados" / "nomes_linhas.json"

# Raio de busca da junção espacial entre o traçado da linha e os abrigos
# de parada. 40 m cobre o afastamento normal entre o eixo da via (onde
# fica a geometria) e a calçada (onde fica o abrigo).
RAIO_PARADA_METROS = 40.0

# Lado da célula do índice espacial, em graus (~55 m). Precisa ser >= ao
# raio de busca para que 3x3 células cubram toda a vizinhança relevante.
_LADO_CELULA_GRAUS = 0.0005


@dataclass(frozen=True)
class ParadaProxima:
    """Abrigo de parada encontrado ao longo do traçado de uma linha."""

    nome: str
    lat: float
    lng: float


async def baixar_json(url: str, timeout: float = 180.0) -> object:
    """Baixa um dos payloads do SEMOB. Deixa erro de rede subir."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        resposta = await client.get(url)
        resposta.raise_for_status()
        return resposta.json()


def carregar_nomes_oficiais() -> dict[str, str]:
    """Denominação oficial por número de linha (ver dados/README.md)."""
    return json.loads(_ARQUIVO_NOMES.read_text(encoding="utf-8"))


def nome_da_parada(endereco: str) -> str:
    """
    Encurta o endereço do abrigo pra virar nome de parada exibível.

    "W3 Sul, SQS 315, Brasília, CEP: 70384-000" -> "W3 Sul, SQS 315"
    """
    limpo = endereco.split(", CEP:")[0]
    for sufixo in (", Brasília", ", Brasilia"):
        if limpo.endswith(sufixo):
            limpo = limpo[: -len(sufixo)]
    return limpo.strip() or endereco.strip()


# O SEMOB publica a denominação em CAIXA ALTA ("CIRCULAR - RODOVIÁRIA DO
# PLANO PILOTO / UNB"). Title case puro estragaria as siglas e as
# preposições ("Rodoviária Do Plano Piloto / Unb"), então tratamos os dois
# casos. Lista montada a partir dos tokens que realmente aparecem nas 823
# denominações (ver dados/README.md).
_CONECTORES = {"de", "do", "da", "dos", "das", "e", "em", "no", "na"}

_SIGLAS = {
    "APAE", "BASEVI", "BR", "CA", "CAESB", "CAUB", "CIPLAN", "CJF", "CNB",
    "DF", "DNOCS", "EC", "EPIA", "EPNB", "EPTG", "EQN", "EQS", "GDF", "IFB",
    "JK", "L2", "P1", "P2", "PTU", "QD", "QE", "QGEX", "QI", "QN", "QNL",
    "QNR", "QS", "RCG", "SAAN", "SAMDU", "SGCV", "SIA", "SIG", "SMU", "SQN",
    "SQS", "STJ", "STPC", "TAS", "TJDFT", "TST", "UNB", "UNDF", "UPIS", "W3",
}

_ROMANOS = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"}


def _formatar_termo(termo: str, primeiro: bool) -> str:
    """Aplica as regras de caixa a um termo já sem pontuação em volta."""
    if not termo:
        return termo
    if termo.upper() in _SIGLAS or termo.upper() in _ROMANOS:
        return termo.upper()
    if any(caractere.isdigit() for caractere in termo):
        # DF-095, QE 38, 110.2 — número não vira title case.
        return termo.upper()
    if not primeiro and termo.lower() in _CONECTORES:
        return termo.lower()
    return termo.capitalize()


def formatar_nome_linha(denominacao: str) -> str:
    """
    "CIRCULAR - RODOVIÁRIA DO PLANO PILOTO / UNB"
        -> "Circular - Rodoviária do Plano Piloto / UNB"

    Preserva pontuação e siglas; separadores internos (hífen, barra) são
    tratados parte a parte, pra "EIXO N-S" não virar "Eixo N-s".
    """
    saida: list[str] = []

    for indice, palavra in enumerate(denominacao.split()):
        # Pontuação sozinha ("-", "/") passa direto.
        if not any(caractere.isalnum() for caractere in palavra):
            saida.append(palavra)
            continue

        partes = re.split(r"([^0-9A-Za-zÀ-ÿ]+)", palavra)
        primeiro_termo = indice == 0
        formatada: list[str] = []

        for parte in partes:
            if not parte or not any(c.isalnum() for c in parte):
                formatada.append(parte)  # separador preservado
                continue
            formatada.append(_formatar_termo(parte, primeiro_termo))
            primeiro_termo = False

        saida.append("".join(formatada))

    return " ".join(saida)


def _distancia_metros(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distância plana — suficiente e barata na escala de dezenas de metros."""
    dlat = (lat1 - lat2) * 111_320
    dlng = (lng1 - lng2) * 111_320 * math.cos(math.radians(lat1))
    return math.hypot(dlat, dlng)


def indexar_pontos(pontos: list[dict]) -> dict[tuple[int, int], list[dict]]:
    """
    Índice espacial (grid hash) dos abrigos de parada.

    Sem isso, casar 7 mil paradas com 930 mil pontos de traçado seria
    força bruta na casa dos bilhões de comparações.
    """
    indice: dict[tuple[int, int], list[dict]] = {}
    for ponto in pontos:
        lat, lng = ponto.get("latitude"), ponto.get("longitude")
        if lat is None or lng is None:
            continue
        chave = (int(lat / _LADO_CELULA_GRAUS), int(lng / _LADO_CELULA_GRAUS))
        indice.setdefault(chave, []).append(ponto)
    return indice


def paradas_ao_longo_do_trajeto(
    trajeto: list[tuple[float, float]],
    indice_pontos: dict[tuple[int, int], list[dict]],
    raio_metros: float = RAIO_PARADA_METROS,
) -> list[ParadaProxima]:
    """
    Paradas que ficam a até `raio_metros` do traçado, na ordem em que a
    linha passa por elas.

    É uma aproximação nossa: o SEMOB publica quais linhas param em cada
    parada (/parada) e, separadamente, a localização dos abrigos
    (/pontos) — mas os dois conjuntos não têm chave em comum, então não
    dá pra cruzar de forma exata. A proximidade geográfica é o melhor
    vínculo disponível.
    """
    encontradas: dict[tuple[float, float], tuple[int, ParadaProxima]] = {}

    for ordem, (lat, lng) in enumerate(trajeto):
        celula_i = int(lat / _LADO_CELULA_GRAUS)
        celula_j = int(lng / _LADO_CELULA_GRAUS)

        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                for ponto in indice_pontos.get((celula_i + di, celula_j + dj), ()):
                    if _distancia_metros(lat, lng, ponto["latitude"], ponto["longitude"]) > raio_metros:
                        continue

                    chave = (round(ponto["latitude"], 6), round(ponto["longitude"], 6))
                    # Mantém a primeira vez que a linha passa pela parada.
                    if chave in encontradas and encontradas[chave][0] <= ordem:
                        continue

                    encontradas[chave] = (
                        ordem,
                        ParadaProxima(
                            nome=nome_da_parada(ponto.get("endereco", "")),
                            lat=ponto["latitude"],
                            lng=ponto["longitude"],
                        ),
                    )

    return [parada for _, parada in sorted(encontradas.values(), key=lambda item: item[0])]


def coordenadas_para_trajeto(geo_linhas: dict | None) -> list[tuple[float, float]]:
    """GeoJSON do SEMOB vem em [lng, lat]; nosso padrão é (lat, lng)."""
    if not geo_linhas:
        return []
    return [(lat, lng) for lng, lat in geo_linhas.get("coordinates", [])]


def horarios_por_linha(horarios_brutos: list[dict]) -> dict[tuple[str, str], list[str]]:
    """
    Indexa /horario por (numero, sentido por extenso), já ordenado e sem
    repetição — o payload traz um registro por partida, incluindo o mesmo
    horário em dias diferentes.
    """
    indice: dict[tuple[str, str], set[str]] = {}
    for registro in horarios_brutos:
        sentido = SENTIDO_POR_INICIAL.get(registro.get("sentido", ""), "")
        if not sentido:
            continue
        chave = (registro.get("numero", ""), sentido)
        alvo = indice.setdefault(chave, set())
        for horario in registro.get("horarios", []):
            if horario.get("horario"):
                alvo.add(horario["horario"])

    return {chave: sorted(valores) for chave, valores in indice.items()}


def escolher_sentido_principal(sentidos: list[str]) -> str:
    """CIRCULAR > IDA > VOLTA — ver PRIORIDADE_SENTIDO."""
    return min(sentidos, key=lambda s: PRIORIDADE_SENTIDO.get(s, 99))


def rotulo_do_sentido(sentido: str, paradas: list[ParadaProxima]) -> str:
    """
    Texto exibido embaixo do nome da linha no app.

    Circular vira só "Circular"; ida/volta ganham origem → destino a
    partir das pontas do traçado, que é o que o passageiro precisa saber.
    """
    if sentido == "CIRCULAR" or len(paradas) < 2:
        return sentido.capitalize()
    return f"{paradas[0].nome} → {paradas[-1].nome}"
