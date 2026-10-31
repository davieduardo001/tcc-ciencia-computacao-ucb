import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mobilidade.linhas_alternativas import (
    SOBREPOSICAO_MINIMA,
    buscar_alternativas,
)
from mobilidade.models.parada import Parada, RotaParada


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Parada.__table__.create(engine)
    RotaParada.__table__.create(engine)
    sessao = sessionmaker(bind=engine)()
    yield sessao
    sessao.close()


def _cadastrar_paradas(db, quantidade):
    for indice in range(quantidade):
        db.add(Parada(codigo=f"ALT{indice:04d}", nome="Parada", lat=-15.8, lng=-48.0))
    db.commit()
    return [p.id for p in db.query(Parada).order_by(Parada.id).all()]


def _vincular(db, numero, paradas, sentido="IDA"):
    for ordem, parada_id in enumerate(paradas):
        db.add(
            RotaParada(
                numero=numero,
                sentido=sentido,
                parada_id=parada_id,
                ordem=ordem,
                indice_trajeto=ordem,
                distancia_acumulada_m=ordem * 500.0,
                distancia_ao_trajeto_m=10.0,
            )
        )
    db.commit()


def test_sobreposicao_de_70_por_cento_ou_mais_eh_sugerida(db):
    """Cancelada com 10 paradas, candidata cobre 7 (70%) — passa no corte."""
    ids = _cadastrar_paradas(db, 12)
    _vincular(db, "0.110", ids[:10])
    _vincular(db, "0.900", ids[:7])

    alternativas = buscar_alternativas(db, "0.110")

    assert [a.numero for a in alternativas] == ["0.900"]
    assert alternativas[0].sobreposicao == pytest.approx(0.70)


def test_sobreposicao_abaixo_de_70_por_cento_nao_eh_sugerida(db):
    """Cancelada com 3 paradas, candidata cobre 2 (66,7%) — não passa."""
    ids = _cadastrar_paradas(db, 4)
    _vincular(db, "0.110", ids[:3])
    _vincular(db, "0.900", ids[1:])  # 2 das 3 da cancelada

    assert buscar_alternativas(db, "0.110") == []


def test_linha_sem_rota_ingerida_devolve_vazio(db):
    """Sem paradas vinculadas não há como medir similaridade (Cenário 2)."""
    _cadastrar_paradas(db, 3)

    assert buscar_alternativas(db, "0.110") == []


def test_resultado_ordenado_por_maior_sobreposicao(db):
    """A candidata que cobre mais paradas vem primeiro."""
    ids = _cadastrar_paradas(db, 10)
    _vincular(db, "0.110", ids)
    _vincular(db, "0.500", ids[:7])  # 70%
    _vincular(db, "0.900", ids[:9])  # 90%

    alternativas = buscar_alternativas(db, "0.110")

    assert [a.numero for a in alternativas] == ["0.900", "0.500"]


def test_candidata_maior_que_a_cancelada_com_todas_as_paradas(db):
    """Candidata cobre 100% das paradas da cancelada e ainda tem outras."""
    ids = _cadastrar_paradas(db, 6)
    _vincular(db, "0.110", ids[:3])
    _vincular(db, "0.900", ids)  # cobre as 3 da cancelada + 3 próprias

    alternativas = buscar_alternativas(db, "0.110")

    assert alternativas[0].numero == "0.900"
    assert alternativas[0].sobreposicao == pytest.approx(1.0)


def test_constante_do_corte_eh_a_da_spec():
    assert SOBREPOSICAO_MINIMA == pytest.approx(0.70)
