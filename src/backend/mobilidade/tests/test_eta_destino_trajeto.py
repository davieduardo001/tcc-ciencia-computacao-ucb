"""
US #172 — ETA até a parada de destino, medido ao longo do trajeto.

Antes o alerta de proximidade media em linha reta até o ponto da parada:
ignorava a direção, não sabia se o ônibus já tinha passado e acompanhava o
ônibus mais próximo da linha, não o da viagem. Estes testes usam o trajeto
sintético dos testes de viagem (linha reta leste-oeste, um ponto a cada
~107 m, paradas A=40, B=100, C=160) e conferem na mão cada resposta.

Como o trajeto é uma reta, a distância pelo traçado e a em linha reta
coincidem à frente do ônibus. O que muda — e o que os testes de regressão
abaixo travam — é o que a linha reta deixava passar: ônibus que já passou do
destino, sentido oposto e ônibus errado.
"""

import uuid
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from mobilidade.models.alerta_proximidade import AlertaProximidade
from mobilidade.providers.contratos_proximidade import (
    EtaDoDestinoProvider,
    PreferenciasDeNotificacao,
    ViagemAtiva,
)
from mobilidade.providers.eta_destino_trajeto import EtaDoDestinoPorTrajeto
from mobilidade.rota_service import RotaService
from mobilidade.services.servico_notificacoes import NotificadorMock
from mobilidade.services.servico_proximidade import (
    EVENTO_DISPARADO,
    EVENTO_SEM_POSICAO,
    ServicoProximidade,
)
from mobilidade.tests.test_viagem import (  # noqa: F401  (db é fixture)
    COD,
    COD_FORA,
    IDX,
    LINHA,
    LINHA_CIRCULAR,
    LINHA_SEM_PARADAS,
    MEDIDO,
    PASSAGEIRO,
    TRAJETO,
    _veiculo,
    db,
)

METROS_POR_MIN_A_30_KMH = 30 * 1000 / 60


def _viagem(destino="C", linha=LINHA, sentido="IDA", prefixo="440001", codigo=None):
    lat, lng = TRAJETO[IDX[destino]]
    return ViagemAtiva(
        viagem_id=str(uuid.uuid4()),
        usuario_id=PASSAGEIRO,
        numero_linha=linha,
        parada_destino_codigo=codigo or COD[destino],
        parada_destino_lat=lat,
        parada_destino_lng=lng,
        parada_destino_nome=f"Parada {destino}",
        veiculo_prefixo=prefixo,
        sentido=sentido,
    )


def _eta(db, viagem, veiculo):
    provider = EtaDoDestinoPorTrajeto(RotaService())
    return provider.eta_minutos(viagem, veiculo, datetime.now(timezone.utc), db)


def _esperado_a_30_kmh(indice_veiculo, indice_destino, idade_s=5):
    metros = MEDIDO.metros_entre(indice_veiculo, indice_destino)
    return metros / METROS_POR_MIN_A_30_KMH - idade_s / 60


class TestMedeAoLongoDoTrajeto:
    def test_cumpre_o_contrato(self):
        assert isinstance(EtaDoDestinoPorTrajeto(RotaService()), EtaDoDestinoProvider)

    def test_ate_a_parada_de_destino_pelo_tracado(self, db):
        eta = _eta(db, _viagem("C"), _veiculo(indice=IDX["B"]))

        assert eta == pytest.approx(_esperado_a_30_kmh(IDX["B"], IDX["C"]), abs=0.15)

    def test_o_destino_define_o_alvo(self, db):
        # Do mesmo ponto, a parada C está mais longe que a B.
        veiculo = _veiculo(indice=IDX["A"])

        ate_b = _eta(db, _viagem("B"), veiculo)
        ate_c = _eta(db, _viagem("C"), veiculo)

        assert ate_b == pytest.approx(_esperado_a_30_kmh(IDX["A"], IDX["B"]), abs=0.15)
        assert ate_c == pytest.approx(_esperado_a_30_kmh(IDX["A"], IDX["C"]), abs=0.15)
        assert ate_c > ate_b

    def test_velocidade_media_vence_a_do_instante(self, db):
        # 30 km/h agora, mas 60 km/h de média nos últimos minutos: metade do tempo.
        instantaneo = _eta(db, _viagem("C"), _veiculo(indice=IDX["B"]))
        com_media = _eta(
            db, _viagem("C"), replace(_veiculo(indice=IDX["B"]), velocidade_media_kmh=60.0)
        )

        assert com_media == pytest.approx(
            (instantaneo + 5 / 60) / 2 - 5 / 60, abs=0.2
        )

    def test_usa_a_velocidade_media_mesmo_com_o_onibus_parado_no_ponto(self, db):
        # Parado agora (semáforo), mas andou 20 km/h nos últimos minutos.
        veiculo = replace(_veiculo(indice=IDX["B"]), velocidade=0.0, velocidade_media_kmh=20.0)

        assert _eta(db, _viagem("C"), veiculo) is not None

    def test_sentido_de_agora_do_veiculo_vale_mais_que_o_do_embarque(self, db):
        # A viagem foi gravada sem sentido confiável ("VOLTA" velho); o feed diz IDA.
        eta = _eta(db, _viagem("C", sentido="VOLTA"), _veiculo(indice=IDX["B"], sentido="IDA"))

        assert eta == pytest.approx(_esperado_a_30_kmh(IDX["B"], IDX["C"]), abs=0.15)

    def test_linha_circular_com_veiculo_sem_sentido(self, db):
        # O ônibus de linha circular nunca reporta "CIRCULAR": a rota entra
        # sempre como última tentativa.
        eta = _eta(
            db,
            _viagem("B", linha=LINHA_CIRCULAR, sentido=None),
            _veiculo(indice=IDX["A"], sentido=None),
        )

        assert eta == pytest.approx(_esperado_a_30_kmh(IDX["A"], IDX["B"]), abs=0.15)


class TestSemDadoConfiavelNaoInventa:
    def test_onibus_que_ja_passou_do_destino(self, db):
        # Dois pontos além da parada C (~214 m): não volta, não é "chegando".
        assert _eta(db, _viagem("C"), _veiculo(indice=IDX["C"] + 2)) is None

    def test_sentido_oposto(self, db):
        # A linha só tem rota IDA; o ônibus vai no sentido contrário.
        assert _eta(db, _viagem("C"), _veiculo(indice=IDX["B"], sentido="VOLTA")) is None

    def test_veiculo_sem_sentido_em_linha_que_nao_e_circular(self, db):
        # Não se adivinha o sentido (igual à pílula e à faixa de viagem).
        assert _eta(db, _viagem("C"), _veiculo(indice=IDX["B"], sentido=None)) is None

    def test_onibus_parado_a_janela_inteira(self, db):
        veiculo = replace(_veiculo(indice=IDX["B"]), velocidade=30.0, velocidade_media_kmh=1.0)

        assert _eta(db, _viagem("C"), veiculo) is None

    def test_onibus_parado_sem_historico(self, db):
        veiculo = replace(_veiculo(indice=IDX["B"]), velocidade=0.0, velocidade_media_kmh=None)

        assert _eta(db, _viagem("C"), veiculo) is None

    def test_onibus_sem_velocidade(self, db):
        veiculo = replace(_veiculo(indice=IDX["B"]), velocidade=None)

        assert _eta(db, _viagem("C"), veiculo) is None

    def test_posicao_velha(self, db):
        # Mais de 5 min sem reportar: o ônibus já andou.
        assert _eta(db, _viagem("C"), _veiculo(indice=IDX["B"], idade_s=6 * 60)) is None

    def test_onibus_fora_do_tracado(self, db):
        # ~1,1 km ao lado do traçado (acima da tolerância de 150 m).
        assert _eta(db, _viagem("C"), _veiculo(indice=IDX["B"], deslocar_lat=0.01)) is None

    def test_linha_sem_rota_ingerida_nao_cai_em_linha_reta(self, db):
        # O ônibus está colado no ponto do destino; em linha reta daria ~0.
        # Sem rota ingerida, não há como afirmar nada — e não se avisa.
        viagem = _viagem("C", linha="T20.V99")

        assert _eta(db, viagem, _veiculo(indice=IDX["C"] - 1)) is None

    def test_destino_que_nao_e_parada_da_linha(self, db):
        viagem = _viagem("C", codigo=COD_FORA)

        assert _eta(db, viagem, _veiculo(indice=IDX["B"])) is None

    def test_linha_sem_paradas_vinculadas(self, db):
        viagem = _viagem("A", linha=LINHA_SEM_PARADAS)

        assert _eta(db, viagem, _veiculo(indice=IDX["A"] - 5)) is None

    def test_codigo_de_parada_desconhecido(self, db):
        viagem = _viagem("C", codigo="PR-V171SUMIU")

        assert _eta(db, viagem, _veiculo(indice=IDX["B"])) is None


# ---------------------------------------------------------------------------
# O ciclo completo do alerta, com o provider real
# ---------------------------------------------------------------------------


class _Viagens:
    def __init__(self, viagens):
        self._viagens = viagens

    def listar_ativas(self):
        return list(self._viagens)


class _Veiculos:
    def __init__(self, veiculos):
        self._veiculos = veiculos

    def obter_das_linhas(self, numeros):
        return {n: list(self._veiculos) for n in numeros}


class _Preferencias:
    def obter(self, usuario_id, db):
        return PreferenciasDeNotificacao(antecedencia_minutos=10)


@pytest.fixture
def sem_alertas(db):
    db.query(AlertaProximidade).filter_by(usuario_id=PASSAGEIRO).delete()
    db.commit()
    yield
    db.query(AlertaProximidade).filter_by(usuario_id=PASSAGEIRO).delete()
    db.commit()


def _ciclo(db, viagem, veiculos, notificador=None):
    servico = ServicoProximidade(
        viagens=_Viagens([viagem]),
        veiculos=_Veiculos(veiculos),
        preferencias=_Preferencias(),
        notificador=notificador or NotificadorMock(),
        eta=EtaDoDestinoPorTrajeto(RotaService()),
    )
    return servico.verificar_proximidades(db)


@pytest.mark.usefixtures("sem_alertas")
class TestCicloDoAlerta:
    def test_dispara_com_o_onibus_da_viagem_a_caminho(self, db):
        notificador = NotificadorMock()
        # 20 vértices (~2,1 km) antes de C, a 30 km/h: ~4 min, dentro dos 10.
        eventos = _ciclo(db, _viagem("C"), [_veiculo(indice=IDX["C"] - 20)], notificador)

        assert eventos == [EVENTO_DISPARADO]
        alerta = db.query(AlertaProximidade).filter_by(usuario_id=PASSAGEIRO).one()
        assert alerta.eta_minutos == pytest.approx(_esperado_a_30_kmh(IDX["C"] - 20, IDX["C"]), abs=0.15)
        assert notificador.chamadas[0][0] == "proximidade"

    def test_nao_dispara_se_o_onibus_ja_passou_do_destino(self, db):
        # Regressão: em linha reta, ~214 m do destino dava ETA ≈ 0 e avisava
        # "está chegando" a quem já tinha passado da parada.
        notificador = NotificadorMock()

        eventos = _ciclo(db, _viagem("C"), [_veiculo(indice=IDX["C"] + 2)], notificador)

        assert eventos == [EVENTO_SEM_POSICAO]
        assert db.query(AlertaProximidade).filter_by(usuario_id=PASSAGEIRO).count() == 0
        assert notificador.chamadas == []

    def test_nao_dispara_com_o_onibus_em_sentido_oposto(self, db):
        # Regressão: a linha reta ignorava a direção.
        eventos = _ciclo(db, _viagem("C"), [_veiculo(indice=IDX["C"] - 5, sentido="VOLTA")])

        assert eventos == [EVENTO_SEM_POSICAO]
        assert db.query(AlertaProximidade).filter_by(usuario_id=PASSAGEIRO).count() == 0

    def test_outro_onibus_da_linha_perto_nao_dispara_para_quem_esta_longe(self, db):
        # Regressão: o ônibus da viagem está a ~13 min (fora dos 10); outro da
        # mesma linha está a 1 min do destino. Antes, o segundo disparava.
        longe = _veiculo(indice=IDX["B"], prefixo="440001")
        perto = _veiculo(indice=IDX["C"] - 5, prefixo="440002")

        eventos = _ciclo(db, _viagem("C", prefixo="440001"), [perto, longe])

        assert eventos == []
        assert db.query(AlertaProximidade).filter_by(usuario_id=PASSAGEIRO).count() == 0

    def test_onibus_da_viagem_parado_no_semaforo_usa_a_media(self, db):
        # Parado agora, mas com 30 km/h de média: segue valendo o ETA.
        parado = replace(
            _veiculo(indice=IDX["C"] - 20), velocidade=0.0, velocidade_media_kmh=30.0
        )

        assert _ciclo(db, _viagem("C"), [parado]) == [EVENTO_DISPARADO]

    def test_nao_repete_o_alerta_no_ciclo_seguinte(self, db):
        viagem = _viagem("C")
        veiculos = [_veiculo(indice=IDX["C"] - 20)]

        _ciclo(db, viagem, veiculos)
        segundo = _ciclo(db, viagem, veiculos)

        assert segundo == ["ja_disparado"]
        assert db.query(AlertaProximidade).filter_by(usuario_id=PASSAGEIRO).count() == 1
