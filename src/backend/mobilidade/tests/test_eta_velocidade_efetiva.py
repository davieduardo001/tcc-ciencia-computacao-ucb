"""
ETA com a velocidade efetivamente percorrida e sem linha reta voltada ao
usuário (card #179: D3b e D4).

Reaproveita o trajeto sintético de test_eta_trajeto.py (linha reta em
latitude fixa, ~111 m entre pontos).
"""

from dataclasses import replace

import pytest

from mobilidade.eta_service import (
    VELOCIDADE_MINIMA_KMH,
    eta_ate_indice,
    eta_minutos_veiculo,
    velocidade_para_eta,
)
from mobilidade.tests.test_eta_trajeto import (
    AGORA,
    INDICE_EMBARQUE,
    TRAJETO,
    TRAJETO_MEDIDO,
    _veiculo,
)


def _com_media(veiculo, media):
    return replace(veiculo, velocidade_media_kmh=media)


# --------------------------------------------------------------------------
# velocidade_para_eta
# --------------------------------------------------------------------------


def test_sem_historico_usa_a_velocidade_do_instante():
    assert velocidade_para_eta(_veiculo(10, velocidade=30.0)) == 30.0


def test_com_historico_prefere_a_media_a_do_instante():
    veiculo = _com_media(_veiculo(10, velocidade=60.0), 20.0)

    assert velocidade_para_eta(veiculo) == 20.0


def test_parado_agora_mas_com_media_em_movimento_conta_a_media():
    # Parado num semáforo: o instante diz 0, mas ele andou 15 km/h nos
    # últimos minutos e vai voltar a andar. Antes o ETA simplesmente sumia.
    veiculo = _com_media(_veiculo(10, velocidade=0.0), 15.0)

    assert velocidade_para_eta(veiculo) == 15.0


def test_media_abaixo_do_minimo_e_veiculo_parado_mesmo_com_instante_alto():
    # Ficou a janela inteira sem sair do lugar; a leitura de 40 km/h do
    # instante não muda isso.
    veiculo = _com_media(_veiculo(10, velocidade=40.0), VELOCIDADE_MINIMA_KMH - 0.5)

    assert velocidade_para_eta(veiculo) is None


def test_sem_velocidade_nenhuma_nao_ha_eta():
    assert velocidade_para_eta(_veiculo(10, velocidade=None)) is None
    assert velocidade_para_eta(_veiculo(10, velocidade=VELOCIDADE_MINIMA_KMH - 0.1)) is None


# --------------------------------------------------------------------------
# o ETA usa essa velocidade
# --------------------------------------------------------------------------


def _eta(veiculo, **kwargs):
    lat, lng = TRAJETO[INDICE_EMBARQUE]
    return eta_minutos_veiculo(
        veiculo,
        lat_alvo=lat,
        lng_alvo=lng,
        agora=AGORA,
        trajeto=TRAJETO_MEDIDO,
        sentido_alvo="IDA",
        **kwargs,
    )


def test_eta_usa_a_media_e_nao_a_do_instante():
    instante = _veiculo(10, velocidade=60.0)  # ~2,2 km do alvo

    so_instante = _eta(instante)
    com_media = _eta(_com_media(instante, 20.0))

    # a média é 1/3 da velocidade do instante → ETA ~3x maior
    assert com_media == pytest.approx(so_instante * 3, rel=0.02)


def test_eta_de_onibus_parado_no_semaforo_deixa_de_sumir():
    veiculo = _com_media(_veiculo(10, velocidade=0.0), 18.0)

    assert _eta(veiculo) is not None


def test_eta_de_onibus_parado_na_janela_inteira_continua_sem_numero():
    veiculo = _com_media(_veiculo(10, velocidade=0.0), 0.4)

    assert _eta(veiculo) is None


# --------------------------------------------------------------------------
# eta_ate_indice — alvo é uma parada com índice já calculado na ingestão
# --------------------------------------------------------------------------


def test_eta_ate_indice_bate_com_o_eta_por_coordenada_da_mesma_parada():
    veiculo = _veiculo(10, velocidade=30.0)

    por_indice = eta_ate_indice(veiculo, TRAJETO_MEDIDO, INDICE_EMBARQUE, "IDA", AGORA)

    assert por_indice == _eta(veiculo)


def test_eta_ate_indice_descarta_onibus_que_ja_passou_da_parada():
    veiculo = _veiculo(INDICE_EMBARQUE + 5, velocidade=30.0)

    assert eta_ate_indice(veiculo, TRAJETO_MEDIDO, INDICE_EMBARQUE, "IDA", AGORA) is None


def test_eta_ate_indice_descarta_sentido_errado():
    veiculo = _veiculo(10, velocidade=30.0, sentido="VOLTA")

    assert eta_ate_indice(veiculo, TRAJETO_MEDIDO, INDICE_EMBARQUE, "IDA", AGORA) is None


# --------------------------------------------------------------------------
# D4 — a linha reta não é número que se mostre como ETA
# --------------------------------------------------------------------------


def test_sem_trajeto_o_padrao_continua_caindo_em_linha_reta():
    # Compatibilidade: o alerta de atraso (#27) e o de proximidade (#172)
    # ainda dependem disso e não foram tocados.
    lat, lng = TRAJETO[INDICE_EMBARQUE]

    eta = eta_minutos_veiculo(_veiculo(10, velocidade=30.0), lat_alvo=lat, lng_alvo=lng, agora=AGORA)

    assert eta is not None and eta > 0


def test_sem_trajeto_e_sem_permitir_linha_reta_nao_ha_eta():
    lat, lng = TRAJETO[INDICE_EMBARQUE]

    eta = eta_minutos_veiculo(
        _veiculo(10, velocidade=30.0),
        lat_alvo=lat,
        lng_alvo=lng,
        agora=AGORA,
        permitir_linha_reta=False,
    )

    assert eta is None


def test_alvo_longe_do_tracado_e_sem_permitir_linha_reta_nao_ha_eta():
    # O usuário está a > 150 m do traçado: antes caía em linha reta
    # (ignorando direção e se o ônibus já passou).
    eta = eta_minutos_veiculo(
        _veiculo(10, velocidade=30.0),
        lat_alvo=TRAJETO[INDICE_EMBARQUE][0] + 0.05,
        lng_alvo=TRAJETO[INDICE_EMBARQUE][1],
        agora=AGORA,
        trajeto=TRAJETO_MEDIDO,
        sentido_alvo="IDA",
        permitir_linha_reta=False,
    )

    assert eta is None


def test_permitir_linha_reta_nao_afeta_quando_ha_trajeto():
    veiculo = _veiculo(10, velocidade=30.0)

    assert _eta(veiculo, permitir_linha_reta=False) == _eta(veiculo, permitir_linha_reta=True)
