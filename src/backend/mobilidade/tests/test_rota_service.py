"""
US #20 — cálculo de rota origem → destino.

Os cenários usam trajetos sintéticos em linha reta, não os dados do
SEMOB: o que está sendo testado é a regra de "passa perto dos dois, e
nessa ordem", e um traçado inventado deixa cada asserção verificável na
mão. A junção com os dados reais já é coberta por test_semob_source.py.
"""

import pytest
from sqlalchemy import text

from mobilidade.ingestao_semob import _celulas_do_trajeto
from mobilidade.models.rota import Rota, RotaCelula
from mobilidade.rota_service import RotaService
from shared.database import SessionLocal

# Trecho leste-oeste na altura de Taguatinga, um ponto a cada ~110 m.
LAT = -15.80
LNG_INICIO = -48.10
PASSO = 0.001
QTD_PONTOS = 200

OESTE = (LAT, LNG_INICIO)                                   # início do traçado
LESTE = (LAT, LNG_INICIO + PASSO * (QTD_PONTOS - 1))        # fim do traçado
MEIO = (LAT, LNG_INICIO + PASSO * 100)

PREFIXO = "T20."


def _trajeto(inverso: bool = False) -> list[tuple[float, float]]:
    pontos = [(LAT, LNG_INICIO + PASSO * i) for i in range(QTD_PONTOS)]
    return list(reversed(pontos)) if inverso else pontos


def _paradas_padrao(trajeto) -> list[dict]:
    """Uma parada a cada ~2 km, incluindo o ponto final do traçado."""
    indices = list(range(0, len(trajeto), 20))
    if indices[-1] != len(trajeto) - 1:
        indices.append(len(trajeto) - 1)
    return [
        {"nome": f"Parada {i}", "lat": trajeto[i][0], "lng": trajeto[i][1]}
        for i in indices
    ]


def _semear(db, numero: str, sentido: str, trajeto, paradas=None) -> None:
    db.add(
        Rota(
            numero=numero,
            sentido=sentido,
            nome=f"{numero} — rota de teste",
            trajeto=[[lat, lng] for lat, lng in trajeto],
            paradas=paradas if paradas is not None else _paradas_padrao(trajeto),
        )
    )
    for (cel_lat, cel_lng), (minimo, maximo) in _celulas_do_trajeto(trajeto).items():
        db.add(
            RotaCelula(
                numero=numero,
                sentido=sentido,
                cel_lat=cel_lat,
                cel_lng=cel_lng,
                indice_min=minimo,
                indice_max=maximo,
            )
        )


@pytest.fixture
def db():
    sessao = SessionLocal()
    _limpar(sessao)
    yield sessao
    _limpar(sessao)
    sessao.close()


def _limpar(sessao) -> None:
    for modelo in (RotaCelula, Rota):
        sessao.query(modelo).filter(
            text("numero LIKE :p").bindparams(p=f"{PREFIXO}%")
        ).delete(synchronize_session=False)
    sessao.commit()


@pytest.fixture
def servico():
    return RotaService()


def test_encontra_linha_direta_no_sentido_certo(db, servico):
    _semear(db, f"{PREFIXO}001", "IDA", _trajeto())
    db.commit()

    opcoes = servico.calcular(db, OESTE, LESTE)

    assert len(opcoes) == 1
    opcao = opcoes[0]
    assert opcao.baldeacoes == 0
    assert opcao.pernas[0].numero == f"{PREFIXO}001"
    assert opcao.pernas[0].sentido == "IDA"
    assert opcao.distancia_km > 10


def test_nao_sugere_linha_que_passa_no_destino_antes_da_origem(db, servico):
    """
    O coração da US: uma linha que só faz oeste→leste não serve pra
    quem vai de leste→oeste. Sem essa checagem, buscar a volta
    devolveria exatamente as mesmas linhas da ida.
    """
    _semear(db, f"{PREFIXO}002", "IDA", _trajeto())
    db.commit()

    assert servico.calcular(db, OESTE, LESTE) != []
    assert servico.calcular(db, LESTE, OESTE) == []


def test_sentido_volta_atende_o_caminho_inverso(db, servico):
    _semear(db, f"{PREFIXO}003", "IDA", _trajeto())
    _semear(db, f"{PREFIXO}003", "VOLTA", _trajeto(inverso=True))
    db.commit()

    ida = servico.calcular(db, OESTE, LESTE)
    volta = servico.calcular(db, LESTE, OESTE)

    assert [p.sentido for o in ida for p in o.pernas] == ["IDA"]
    assert [p.sentido for o in volta for p in o.pernas] == ["VOLTA"]


def test_origem_longe_do_trajeto_nao_devolve_nada(db, servico):
    _semear(db, f"{PREFIXO}004", "IDA", _trajeto())
    db.commit()

    # ~11 km ao sul do traçado — muito além do raio de caminhada.
    longe = (LAT - 0.1, LNG_INICIO)

    assert servico.calcular(db, longe, LESTE) == []


def test_origem_e_destino_no_mesmo_lugar_nao_sugere_onibus(db, servico):
    _semear(db, f"{PREFIXO}005", "IDA", _trajeto())
    db.commit()

    assert servico.calcular(db, MEIO, MEIO) == []


def test_embarque_e_desembarque_apontam_paradas_do_trajeto(db, servico):
    _semear(db, f"{PREFIXO}006", "IDA", _trajeto())
    db.commit()

    perna = servico.calcular(db, OESTE, LESTE)[0].pernas[0]

    assert perna.embarque.parada_nome.startswith("Parada ")
    assert perna.desembarque.parada_nome.startswith("Parada ")
    assert perna.embarque.caminhada_metros < 200
    assert perna.desembarque.caminhada_metros < 200
    assert perna.paradas_no_trecho > 0
    # O trajeto devolvido é só o trecho a bordo, não a linha inteira.
    assert len(perna.trajeto) <= QTD_PONTOS


def test_ponto_sem_parada_conhecida_fica_sem_nome_em_vez_de_inventar(db, servico):
    # Uma única parada, no comecinho: o desembarque lá no leste fica a
    # ~20 km dela e não deve herdar o nome dela.
    _semear(
        db,
        f"{PREFIXO}007",
        "IDA",
        _trajeto(),
        paradas=[{"nome": "Única Parada", "lat": LAT, "lng": LNG_INICIO}],
    )
    db.commit()

    perna = servico.calcular(db, OESTE, LESTE)[0].pernas[0]

    assert perna.embarque.parada_nome == "Única Parada"
    assert perna.desembarque.parada_nome == ""


def test_monta_baldeacao_quando_nao_existe_linha_direta(db, servico):
    """
    Duas linhas em L: a primeira vai pro leste, a segunda sobe pro
    norte a partir do meio do caminho. Não há direta entre o oeste e o
    ponto ao norte, mas há uma baldeação óbvia.
    """
    _semear(db, f"{PREFIXO}008", "IDA", _trajeto())

    subida = [(LAT + PASSO * i, MEIO[1]) for i in range(200)]
    _semear(db, f"{PREFIXO}009", "IDA", subida)
    db.commit()

    norte = subida[-1]

    assert servico.calcular(db, OESTE, LESTE)[0].baldeacoes == 0

    opcoes = servico.calcular(db, OESTE, norte)

    assert opcoes, "esperava ao menos uma opção com baldeação"
    opcao = opcoes[0]
    assert opcao.baldeacoes == 1
    assert [p.numero for p in opcao.pernas] == [f"{PREFIXO}008", f"{PREFIXO}009"]
    # A segunda perna embarca onde a primeira deixou o passageiro.
    assert opcao.pernas[1].embarque.caminhada_metros < 400


def test_sem_nenhuma_rota_cadastrada_devolve_lista_vazia(db, servico):
    assert servico.calcular(db, OESTE, LESTE) == []
