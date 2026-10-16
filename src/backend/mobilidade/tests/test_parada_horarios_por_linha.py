"""
Painel da parada (US #18) — follow-up da issue #174.

  • horários por linha, e não 3 no total misturando as linhas;
  • o dia certo (RN-08: dia útil, sábado e domingo nunca se misturam);
  • custo da consulta: sem uma ida ao banco por rota;
  • a regra IDA×VOLTA do vínculo parada↔rota existe num lugar só.

Semeia `Parada`/`RotaParada`/`Rota` à mão sobre o trajeto sintético de
test_rota_service.py, para que cada asserção seja conferível na mão.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from mobilidade import chegada_service, parada_service
from mobilidade.main import app
from mobilidade.models.linha import Linha
from mobilidade.models.parada import Parada, RotaParada
from mobilidade.models.rota import Rota, RotaCelula
from mobilidade.parada_service import ParadaService, vinculos_por_linha
from mobilidade.posicao_service import FUSO_SEMOB
from mobilidade.tests.test_rota_service import _semear, _trajeto
from shared.database import SessionLocal, engine

client = TestClient(app)

TRAJETO = _trajeto()
INDICE_PARADA = 100
LAT, LNG = TRAJETO[INDICE_PARADA]
CODIGO = "PR-T174A"

LINHA_A = "T174.A01"
LINHA_B = "T174.B02"
LINHA_MUITAS = [f"T174.M{i:02d}" for i in range(12)]
TODAS = [LINHA_A, LINHA_B, *LINHA_MUITAS]

# Dias de teste conhecidos: 2026-10-12 é segunda-feira; 2026-10-17, sábado;
# 2026-10-18, domingo.
SEGUNDA_10H = datetime(2026, 10, 12, 10, 0, tzinfo=FUSO_SEMOB)
SABADO_10H = datetime(2026, 10, 17, 10, 0, tzinfo=FUSO_SEMOB)
DOMINGO_10H = datetime(2026, 10, 18, 10, 0, tzinfo=FUSO_SEMOB)

UTEIS = ["09:00", "10:15", "10:45", "11:30", "12:00"]
SABADO = ["10:05", "10:50"]
DOMINGO = ["10:30", "13:00", "15:00", "17:00"]


def _por_dia(uteis=None, sabado=None, domingo=None):
    """Mapa {"0".."6": [...]} (segunda=0), como a ingestão grava."""
    return {
        **{str(d): list(uteis or []) for d in range(5)},
        "5": list(sabado or []),
        "6": list(domingo or []),
    }


def _limpar(db) -> None:
    for numero in TODAS:
        db.query(RotaParada).filter(RotaParada.numero == numero).delete(synchronize_session=False)
        db.query(RotaCelula).filter(RotaCelula.numero == numero).delete(synchronize_session=False)
        db.query(Rota).filter(Rota.numero == numero).delete(synchronize_session=False)
        db.query(Linha).filter(Linha.numero == numero).delete(synchronize_session=False)
    db.query(Parada).filter(Parada.codigo == CODIGO).delete(synchronize_session=False)
    db.commit()


def _vincular(db, parada, numero, sentido="IDA", distancia_ao_trajeto=2.0):
    db.add(
        RotaParada(
            numero=numero,
            sentido=sentido,
            parada_id=parada.id,
            ordem=5,
            indice_trajeto=INDICE_PARADA,
            distancia_acumulada_m=1000.0,
            distancia_ao_trajeto_m=distancia_ao_trajeto,
        )
    )


def _rota(db, numero, sentido="IDA", por_dia=None, tempo=60):
    _semear(db, numero, sentido, TRAJETO)
    db.flush()  # a SessionLocal do projeto tem autoflush desligado
    rota = db.query(Rota).filter(Rota.numero == numero, Rota.sentido == sentido).one()
    rota.horarios_por_dia = por_dia
    rota.tempo_percurso_min = tempo
    return rota


@pytest.fixture
def db():
    sessao = SessionLocal()
    _limpar(sessao)
    yield sessao
    _limpar(sessao)
    sessao.close()


@pytest.fixture
def parada(db):
    p = Parada(codigo=CODIGO, nome="Parada do teste #174", lat=LAT, lng=LNG)
    db.add(p)
    db.flush()
    return p


@pytest.fixture
def duas_linhas(db, parada):
    """A (horários próprios) e B (outros) param no mesmo abrigo."""
    _rota(db, LINHA_A, por_dia=_por_dia(uteis=UTEIS, sabado=SABADO, domingo=DOMINGO))
    _rota(db, LINHA_B, por_dia=_por_dia(uteis=["10:20", "23:00"], sabado=["10:20"], domingo=[]))
    _vincular(db, parada, LINHA_A)
    _vincular(db, parada, LINHA_B)
    db.commit()
    return db


def _linha(encontrada, numero):
    return next(l for l in encontrada.linhas if l.numero == numero)


# --------------------------------------------------------------------------
# horários por linha
# --------------------------------------------------------------------------


def test_cada_linha_recebe_os_proprios_tres_proximos_horarios(duas_linhas):
    encontrada = ParadaService()._por_parada_fisica(duas_linhas, LAT, LNG, SEGUNDA_10H)

    # A: depois das 10:00 → 10:15, 10:45, 11:30 (três, e não os que sobrassem
    # da mistura com a outra linha).
    assert _linha(encontrada, LINHA_A).proximos_horarios == ["10:15", "10:45", "11:30"]
    # B só tem 10:20 e 23:00 hoje; completa com o começo do dia só se existir.
    assert _linha(encontrada, LINHA_B).proximos_horarios == ["10:20", "23:00"]


def test_linha_com_poucos_horarios_nao_rouba_vagas_da_outra(duas_linhas):
    """O defeito original: 3 no total. Com B tendo 10:20, A perdia uma vaga."""
    encontrada = ParadaService()._por_parada_fisica(duas_linhas, LAT, LNG, SEGUNDA_10H)

    assert len(_linha(encontrada, LINHA_A).proximos_horarios) == 3
    assert "10:20" not in _linha(encontrada, LINHA_A).proximos_horarios


def test_lista_combinada_da_parada_segue_igual_para_clientes_antigos(duas_linhas):
    encontrada = ParadaService()._por_parada_fisica(duas_linhas, LAT, LNG, SEGUNDA_10H)

    # Mesma regra de antes: 3 no total, misturando as linhas.
    assert encontrada.proximos_horarios == ["10:15", "10:20", "10:45"]


# --------------------------------------------------------------------------
# RN-08 — o dia certo
# --------------------------------------------------------------------------


def test_sabado_usa_so_os_horarios_de_sabado(duas_linhas):
    encontrada = ParadaService()._por_parada_fisica(duas_linhas, LAT, LNG, SABADO_10H)

    assert _linha(encontrada, LINHA_A).proximos_horarios == ["10:05", "10:50"]
    assert _linha(encontrada, LINHA_B).proximos_horarios == ["10:20"]


def test_domingo_nao_herda_horario_de_dia_util_nem_de_sabado(duas_linhas):
    encontrada = ParadaService()._por_parada_fisica(duas_linhas, LAT, LNG, DOMINGO_10H)

    a = _linha(encontrada, LINHA_A).proximos_horarios
    assert a == ["10:30", "13:00", "15:00"]
    assert not set(a) & set(UTEIS + SABADO)
    # B não sai aos domingos: lista vazia, e não os horários de segunda.
    assert _linha(encontrada, LINHA_B).proximos_horarios == []


def test_segunda_nao_traz_horario_de_domingo(duas_linhas):
    encontrada = ParadaService()._por_parada_fisica(duas_linhas, LAT, LNG, SEGUNDA_10H)

    todos = {h for l in encontrada.linhas for h in l.proximos_horarios}
    assert not todos & set(DOMINGO)


# --------------------------------------------------------------------------
# caminho antigo: rota ainda sem horarios_por_dia
# --------------------------------------------------------------------------


def test_rota_sem_horarios_por_dia_usa_a_lista_antiga_da_propria_linha(db, parada):
    _rota(db, LINHA_A, por_dia=None)
    _rota(db, LINHA_B, por_dia=None)
    _vincular(db, parada, LINHA_A)
    _vincular(db, parada, LINHA_B)
    for numero, horarios in ((LINHA_A, ["10:30", "11:00"]), (LINHA_B, ["10:10"])):
        db.add(
            Linha(
                numero=numero,
                nome=numero,
                sentido="Circular",
                paradas=[],
                trajeto=[],
                horarios_previstos=horarios,
            )
        )
    db.commit()

    encontrada = ParadaService()._por_parada_fisica(db, LAT, LNG, SEGUNDA_10H)

    assert _linha(encontrada, LINHA_A).proximos_horarios == ["10:30", "11:00"]
    assert _linha(encontrada, LINHA_B).proximos_horarios == ["10:10"]


def _contar_consultas(chamada) -> int:
    consultas: list[str] = []

    def _conta(conn, cursor, statement, parameters, context, executemany):
        consultas.append(statement)

    event.listen(engine, "before_cursor_execute", _conta)
    try:
        chamada()
    finally:
        event.remove(engine, "before_cursor_execute", _conta)
    return len(consultas)


def test_custo_nao_cresce_com_o_numero_de_linhas_na_ingestao_antiga(db, parada):
    """Antes: 2 + uma consulta por rota (12 linhas = 14). Agora: constante."""
    for numero in LINHA_MUITAS:
        _rota(db, numero, por_dia=None)
        _vincular(db, parada, numero)
        db.add(
            Linha(
                numero=numero,
                nome=numero,
                sentido="Circular",
                paradas=[],
                trajeto=[],
                horarios_previstos=["10:30"],
            )
        )
    db.commit()

    servico = ParadaService()
    resultado = {}

    def chamar():
        resultado["r"] = servico._por_parada_fisica(db, LAT, LNG, SEGUNDA_10H)

    consultas = _contar_consultas(chamar)

    assert len(resultado["r"].linhas) == len(LINHA_MUITAS)
    assert all(l.proximos_horarios == ["10:30"] for l in resultado["r"].linhas)
    assert consultas <= 3


def test_custo_com_ingestao_nova_e_de_duas_consultas(duas_linhas):
    servico = ParadaService()
    consultas = _contar_consultas(
        lambda: servico._por_parada_fisica(duas_linhas, LAT, LNG, SEGUNDA_10H)
    )

    assert consultas == 2  # a parada perto + os vínculos (join com a rota)


# --------------------------------------------------------------------------
# caminho do catálogo (antes da reingestão) — também por linha
# --------------------------------------------------------------------------

LAT_CATALOGO, LNG_CATALOGO = -15.2345, -47.1234  # longe de qualquer parada semeada


def test_catalogo_antigo_tambem_devolve_horarios_por_linha(db):
    ponto = {"nome": "Ponto do catálogo", "lat": LAT_CATALOGO, "lng": LNG_CATALOGO}
    db.add(
        Linha(
            numero=LINHA_A,
            nome="A",
            sentido="Circular",
            paradas=[ponto],
            trajeto=[],
            horarios_previstos=["10:30", "11:00", "11:30", "12:00"],
        )
    )
    db.add(
        Linha(
            numero=LINHA_B,
            nome="B",
            sentido="Circular",
            paradas=[ponto],
            trajeto=[],
            horarios_previstos=["10:10"],
        )
    )
    db.commit()

    encontrada = ParadaService()._por_linhas_cacheadas(db, LAT_CATALOGO, LNG_CATALOGO, SEGUNDA_10H)

    assert {l.numero for l in encontrada.linhas} == {LINHA_A, LINHA_B}
    assert _linha(encontrada, LINHA_A).proximos_horarios == ["10:30", "11:00", "11:30"]
    assert _linha(encontrada, LINHA_B).proximos_horarios == ["10:10"]
    assert encontrada.nome == "Ponto do catálogo"


def test_catalogo_ignora_pontos_fora_do_raio_e_nao_conta_a_linha_duas_vezes(db):
    perto = {"nome": "Perto", "lat": LAT_CATALOGO, "lng": LNG_CATALOGO}
    perto_de_novo = {"nome": "Perto 2", "lat": LAT_CATALOGO + 0.00005, "lng": LNG_CATALOGO}
    longe = {"nome": "Longe", "lat": LAT_CATALOGO + 0.01, "lng": LNG_CATALOGO}
    db.add(
        Linha(
            numero=LINHA_A,
            nome="A",
            sentido="Circular",
            paradas=[longe, perto, perto_de_novo],
            trajeto=[],
            horarios_previstos=["10:30"],
        )
    )
    db.add(
        Linha(
            numero=LINHA_B,
            nome="B",
            sentido="Circular",
            paradas=[longe],
            trajeto=[],
            horarios_previstos=["10:31"],
        )
    )
    db.commit()

    encontrada = ParadaService()._por_linhas_cacheadas(db, LAT_CATALOGO, LNG_CATALOGO, SEGUNDA_10H)

    assert [l.numero for l in encontrada.linhas] == [LINHA_A]


def test_catalogo_sem_parada_perto_devolve_none(db):
    db.add(
        Linha(
            numero=LINHA_A,
            nome="A",
            sentido="Circular",
            paradas=[{"nome": "Longe", "lat": LAT_CATALOGO + 0.01, "lng": LNG_CATALOGO}],
            trajeto=[],
            horarios_previstos=["10:30"],
        )
    )
    db.commit()

    assert ParadaService()._por_linhas_cacheadas(db, LAT_CATALOGO, LNG_CATALOGO, SEGUNDA_10H) is None


# --------------------------------------------------------------------------
# regra IDA×VOLTA num lugar só (issue #174, item d)
# --------------------------------------------------------------------------


def test_vinculo_ida_volta_vale_o_de_menor_distancia_ao_trajeto(db, parada):
    _rota(db, LINHA_A, "IDA")
    _rota(db, LINHA_A, "VOLTA")
    _vincular(db, parada, LINHA_A, "IDA", distancia_ao_trajeto=30.0)
    _vincular(db, parada, LINHA_A, "VOLTA", distancia_ao_trajeto=4.0)
    db.commit()

    vinculo, rota = vinculos_por_linha(db, parada.id)[LINHA_A]

    assert rota.sentido == "VOLTA"
    assert vinculo.distancia_ao_trajeto_m == 4.0


def test_painel_e_chegadas_usam_a_mesma_funcao_de_vinculo():
    assert chegada_service.vinculos_por_linha is parada_service.vinculos_por_linha


def test_painel_mostra_o_mesmo_sentido_que_as_chegadas_escolhem(db, parada):
    _rota(db, LINHA_A, "IDA")
    _rota(db, LINHA_A, "VOLTA")
    _vincular(db, parada, LINHA_A, "IDA", distancia_ao_trajeto=30.0)
    _vincular(db, parada, LINHA_A, "VOLTA", distancia_ao_trajeto=4.0)
    db.commit()

    encontrada = ParadaService()._por_parada_fisica(db, LAT, LNG, SEGUNDA_10H)
    _, rota_das_chegadas = chegada_service.vinculos_por_linha(db, parada.id)[LINHA_A]

    assert _linha(encontrada, LINHA_A).rota_sentido == rota_das_chegadas.sentido == "VOLTA"


# --------------------------------------------------------------------------
# contrato da API
# --------------------------------------------------------------------------


def test_api_traz_horarios_por_linha_e_mantem_a_lista_da_parada(db, parada):
    todos_os_dias = {
        str(d): [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)] for d in range(7)
    }
    _rota(db, LINHA_A, por_dia=todos_os_dias)
    _rota(db, LINHA_B, por_dia=todos_os_dias)
    _vincular(db, parada, LINHA_A)
    _vincular(db, parada, LINHA_B)
    db.commit()

    resposta = client.get("/mobilidade/paradas", params={"lat": LAT, "lng": LNG})

    assert resposta.status_code == 200
    dados = resposta.json()
    por_numero = {l["numero"]: l for l in dados["linhas"]}
    assert set(por_numero) == {LINHA_A, LINHA_B}
    for linha in por_numero.values():
        assert len(linha["proximos_horarios"]) == 3
    # compatibilidade: o campo antigo continua lá, com até 3 horários
    assert 1 <= len(dados["proximos_horarios"]) <= 3
