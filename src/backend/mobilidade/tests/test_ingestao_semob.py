"""Ingestão do SEMOB com as respostas da rede mockadas.

Usa banco de verdade (como os outros testes de serviço do mobilidade),
mas nunca chama dados.semob.df.gov.br — os payloads são amostras com a
mesma forma da API real.
"""

import asyncio
from unittest.mock import AsyncMock, patch

from mobilidade.ingestao_semob import ingerir
from mobilidade.models.linha import Linha
from mobilidade.semob_source import URL_ESPACIAIS, URL_HORARIO, URL_PONTOS
from shared.database import SessionLocal

NUMERO_TESTE = "9.997"
OUTRO_NUMERO = "9.998"

ESPACIAIS = [
    {
        "Numero": NUMERO_TESTE,
        "Sentido": "IDA",
        "GeoLinhas": {
            "type": "LineString",
            "coordinates": [[-47.8826, -15.7944], [-47.8800, -15.7900]],
        },
    },
    {
        "Numero": NUMERO_TESTE,
        "Sentido": "CIRCULAR",
        "GeoLinhas": {
            "type": "LineString",
            "coordinates": [[-47.8826, -15.7944], [-47.8810, -15.7920], [-47.8826, -15.7944]],
        },
    },
    {
        # Sem geometria: não deve virar registro.
        "Numero": OUTRO_NUMERO,
        "Sentido": "IDA",
        "GeoLinhas": {"type": "LineString", "coordinates": []},
    },
]

HORARIOS = [
    {"numero": NUMERO_TESTE, "sentido": "C", "horarios": [{"horario": "06:00"}, {"horario": "06:30"}]},
    {"numero": NUMERO_TESTE, "sentido": "I", "horarios": [{"horario": "23:00"}]},
]

PONTOS = [
    {"latitude": -15.7944, "longitude": -47.8826, "endereco": "Rodoviária, Brasília, CEP: 70070-000"},
    {"latitude": -15.7920, "longitude": -47.8810, "endereco": "Meio do Caminho, Brasília, CEP: 70000-000"},
    {"latitude": -15.9500, "longitude": -48.3000, "endereco": "Longe Demais, Brasília, CEP: 72000-000"},
]


def _baixar_falso(url, timeout=180.0):
    if url == URL_ESPACIAIS:
        return ESPACIAIS
    if url == URL_HORARIO:
        return HORARIOS
    if url == URL_PONTOS:
        return PONTOS
    raise AssertionError(f"URL inesperada na ingestão: {url}")


def _limpar(db):
    db.query(Linha).filter(Linha.numero.in_([NUMERO_TESTE, OUTRO_NUMERO])).delete(
        synchronize_session=False
    )
    db.commit()


def _rodar_ingestao(db):
    with patch(
        "mobilidade.ingestao_semob.baixar_json",
        AsyncMock(side_effect=_baixar_falso),
    ):
        return asyncio.run(ingerir(db))


def test_ingestao_grava_linha_com_trajeto_paradas_e_horarios():
    db = SessionLocal()
    try:
        _limpar(db)

        resumo = _rodar_ingestao(db)

        registro = db.query(Linha).filter(Linha.numero == NUMERO_TESTE).one()
        # CIRCULAR tem prioridade sobre IDA quando a linha tem os dois.
        assert registro.sentido == "Circular"
        assert len(registro.trajeto) == 3
        assert registro.trajeto[0] == [-15.7944, -47.8826]  # (lat, lng)
        assert registro.horarios_previstos == ["06:00", "06:30"]

        nomes = [p["nome"] for p in registro.paradas]
        assert "Rodoviária" in nomes
        assert "Longe Demais" not in nomes  # fora do raio da junção espacial

        assert resumo.linhas_gravadas == 1
        assert resumo.paradas_encontradas >= 1
    finally:
        _limpar(db)
        db.close()


def test_ingestao_ignora_linha_sem_geometria():
    db = SessionLocal()
    try:
        _limpar(db)

        _rodar_ingestao(db)

        assert db.query(Linha).filter(Linha.numero == OUTRO_NUMERO).first() is None
    finally:
        _limpar(db)
        db.close()


def test_ingestao_e_idempotente():
    db = SessionLocal()
    try:
        _limpar(db)

        _rodar_ingestao(db)
        _rodar_ingestao(db)

        assert db.query(Linha).filter(Linha.numero == NUMERO_TESTE).count() == 1
    finally:
        _limpar(db)
        db.close()


def test_linha_sem_nome_oficial_recebe_nome_generico():
    # 9.997 não existe no dados/nomes_linhas.json (só linhas reais do DF).
    db = SessionLocal()
    try:
        _limpar(db)

        resumo = _rodar_ingestao(db)

        registro = db.query(Linha).filter(Linha.numero == NUMERO_TESTE).one()
        assert registro.nome == f"Linha {NUMERO_TESTE}"
        assert resumo.linhas_sem_nome_oficial == 1
    finally:
        _limpar(db)
        db.close()
