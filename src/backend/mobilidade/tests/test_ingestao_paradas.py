"""Ingestão de paradas físicas e vínculos com rotas (US #173).

Banco de verdade, rede mockada — mesmo padrão de test_ingestao_semob.py.
"""

import asyncio
from unittest.mock import AsyncMock, patch

from mobilidade.ingestao_semob import ingerir
from mobilidade.models.linha import Linha
from mobilidade.models.parada import Parada, RotaParada
from mobilidade.models.rota import Rota, RotaCelula
from mobilidade.semob_source import URL_ESPACIAIS, URL_HORARIO, URL_PONTOS
from shared.database import SessionLocal

LINHA_1 = "9.996"
LINHA_2 = "9.995"
NUMEROS = [LINHA_1, LINHA_2]

# Trajeto reto de A (rodoviária) a D, com um vértice a cada ~170 m.
A = (-15.7944, -47.8826)
B = (-15.7930, -47.8818)
C = (-15.7915, -47.8808)
D = (-15.7900, -47.8800)
# Segundo registro do MESMO abrigo da rodoviária, ~4,5 m ao norte.
A_DUPLICADO = (-15.79436, -47.8826)


def _geo(*pontos):
    return {"type": "LineString", "coordinates": [[lng, lat] for lat, lng in pontos]}


ESPACIAIS = [
    {"Numero": LINHA_1, "Sentido": "IDA", "GeoLinhas": _geo(A, B, C, D)},
    {"Numero": LINHA_1, "Sentido": "VOLTA", "GeoLinhas": _geo(D, C, B, A)},
    # Outra linha que passa pelas mesmas paradas físicas.
    {"Numero": LINHA_2, "Sentido": "IDA", "GeoLinhas": _geo(A, B, C, D)},
]

HORARIOS = [
    {
        "numero": LINHA_1,
        "sentido": "I",
        "tempo_percurso": 80,
        "horarios": [
            {"horario": "06:00", "dias_semana": "SSSSSNN"},
            {"horario": "08:00", "dias_semana": "NNNNNNS"},
        ],
    },
]

PONTOS = [
    {"latitude": A[0], "longitude": A[1], "endereco": "Rodoviária, Brasília, CEP: 70070-000"},
    {"latitude": A_DUPLICADO[0], "longitude": A_DUPLICADO[1], "endereco": "Rodoviária (outro registro), Brasília"},
    {"latitude": C[0], "longitude": C[1], "endereco": "Meio do Caminho, Brasília, CEP: 70000-000"},
]


def _baixar_falso(url, timeout=180.0):
    return {URL_ESPACIAIS: ESPACIAIS, URL_HORARIO: HORARIOS, URL_PONTOS: PONTOS}[url]


def _limpar(db):
    # A ingestão reconstrói rota, rota_celula e parada do zero (inclusive
    # as que não são destes testes) — aqui só garantimos o estado limpo.
    db.query(RotaParada).delete(synchronize_session=False)
    db.query(Parada).delete(synchronize_session=False)
    db.query(RotaCelula).delete(synchronize_session=False)
    db.query(Rota).delete(synchronize_session=False)
    db.query(Linha).filter(Linha.numero.in_(NUMEROS)).delete(synchronize_session=False)
    db.commit()


def _rodar(db):
    with patch(
        "mobilidade.ingestao_semob.baixar_json", AsyncMock(side_effect=_baixar_falso)
    ):
        return asyncio.run(ingerir(db))


def _vinculos(db, numero, sentido):
    return (
        db.query(RotaParada, Parada)
        .join(Parada, Parada.id == RotaParada.parada_id)
        .filter(RotaParada.numero == numero, RotaParada.sentido == sentido)
        .order_by(RotaParada.ordem)
        .all()
    )


def test_abrigos_duplicados_viram_uma_parada_fisica():
    db = SessionLocal()
    try:
        _limpar(db)
        resumo = _rodar(db)

        # 3 registros em /pontos, 2 paradas físicas: rodoviária e meio.
        assert db.query(Parada).count() == 2
        assert resumo.paradas_fisicas == 2
        assert {p.nome for p in db.query(Parada)} >= {"Meio do Caminho"}
    finally:
        _limpar(db)
        db.close()


def test_mesma_parada_tem_um_unico_codigo_em_linhas_e_sentidos_diferentes():
    # Cenário 1 e 4 da #173: o código não depende da linha de acesso.
    db = SessionLocal()
    try:
        _limpar(db)
        _rodar(db)

        codigos = {
            (numero, sentido): [p.codigo for _, p in _vinculos(db, numero, sentido)]
            for numero, sentido in [(LINHA_1, "IDA"), (LINHA_1, "VOLTA"), (LINHA_2, "IDA")]
        }

        assert set(codigos[(LINHA_1, "IDA")]) == set(codigos[(LINHA_1, "VOLTA")])
        assert set(codigos[(LINHA_1, "IDA")]) == set(codigos[(LINHA_2, "IDA")])
        assert len(set(codigos[(LINHA_1, "IDA")])) == 2
        assert all(c.startswith("PR-") for c in codigos[(LINHA_1, "IDA")])
    finally:
        _limpar(db)
        db.close()


def test_vinculo_guarda_ordem_indice_e_distancias_na_ordem_do_trajeto():
    db = SessionLocal()
    try:
        _limpar(db)
        _rodar(db)

        ida = _vinculos(db, LINHA_1, "IDA")
        volta = _vinculos(db, LINHA_1, "VOLTA")

        # IDA: rodoviária (vértice 0) antes do meio (vértice 2).
        assert [(v.ordem, v.indice_trajeto) for v, _ in ida] == [(0, 0), (1, 2)]
        assert ida[0][0].distancia_acumulada_m == 0
        assert ida[1][0].distancia_acumulada_m > ida[0][0].distancia_acumulada_m
        # VOLTA percorre ao contrário: meio (vértice 1) antes da rodoviária (3).
        assert [(v.ordem, v.indice_trajeto) for v, _ in volta] == [(0, 1), (1, 3)]
        # Parada colada no traçado: distância ao trajeto de poucos metros.
        assert all(v.distancia_ao_trajeto_m < 10 for v, _ in ida)
    finally:
        _limpar(db)
        db.close()


def test_codigos_sao_estaveis_entre_ingestoes():
    db = SessionLocal()
    try:
        _limpar(db)
        _rodar(db)
        antes = sorted(p.codigo for p in db.query(Parada))

        _rodar(db)
        depois = sorted(p.codigo for p in db.query(Parada))

        assert antes == depois
        # A tabela é reconstruída, não acumulada.
        assert db.query(Parada).count() == 2
        assert db.query(RotaParada).count() == 6
    finally:
        _limpar(db)
        db.close()


def test_rota_recebe_horarios_por_dia_e_tempo_de_percurso():
    db = SessionLocal()
    try:
        _limpar(db)
        _rodar(db)

        ida = db.query(Rota).filter(Rota.numero == LINHA_1, Rota.sentido == "IDA").one()
        assert ida.tempo_percurso_min == 80
        assert ida.horarios_por_dia["0"] == ["06:00"]  # segunda
        assert ida.horarios_por_dia["6"] == ["08:00"]  # domingo

        # Sentido sem /horario: colunas nulas, não erro.
        volta = db.query(Rota).filter(Rota.numero == LINHA_1, Rota.sentido == "VOLTA").one()
        assert volta.horarios_por_dia is None
        assert volta.tempo_percurso_min is None
    finally:
        _limpar(db)
        db.close()


def test_linha_continua_com_horarios_previstos_sem_recorte_de_dia():
    # Compatibilidade: quem ainda lê `linha.horarios_previstos` não muda.
    db = SessionLocal()
    try:
        _limpar(db)
        _rodar(db)

        linha = db.query(Linha).filter(Linha.numero == LINHA_1).one()
        assert linha.horarios_previstos == ["06:00", "08:00"]
    finally:
        _limpar(db)
        db.close()
