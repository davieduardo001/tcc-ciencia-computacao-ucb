from datetime import datetime
from zoneinfo import ZoneInfo

from mobilidade.eta_service import (
    VELOCIDADE_MINIMA_KMH,
    calcular_eta_minutos,
    proximo_horario_previsto,
)

FUSO = ZoneInfo("America/Sao_Paulo")

# ~1.1 km em linha reta na altura de Taguatinga (0.01° de latitude).
LAT_USUARIO, LNG_USUARIO = -15.8300, -48.0500
LAT_VEICULO, LNG_VEICULO = -15.8400, -48.0500


def test_eta_calculado_com_veiculo_em_movimento():
    # Cenário 1 da US #19: GPS disponível e veículo andando.
    eta = calcular_eta_minutos(
        lat_veiculo=LAT_VEICULO,
        lng_veiculo=LNG_VEICULO,
        velocidade_kmh=30.0,
        lat_usuario=LAT_USUARIO,
        lng_usuario=LNG_USUARIO,
    )

    assert eta is not None
    # ~1.11 km a 30 km/h ≈ 2.2 min.
    assert 1.5 < eta < 3.0


def test_eta_indisponivel_para_veiculo_parado():
    # Cenário 5: sem velocidade confiável, sem ETA — nunca um valor
    # aproximado no cliente.
    eta = calcular_eta_minutos(
        lat_veiculo=LAT_VEICULO,
        lng_veiculo=LNG_VEICULO,
        velocidade_kmh=VELOCIDADE_MINIMA_KMH - 0.1,
        lat_usuario=LAT_USUARIO,
        lng_usuario=LNG_USUARIO,
    )

    assert eta is None


def test_eta_indisponivel_sem_velocidade_informada():
    eta = calcular_eta_minutos(
        lat_veiculo=LAT_VEICULO,
        lng_veiculo=LNG_VEICULO,
        velocidade_kmh=None,
        lat_usuario=LAT_USUARIO,
        lng_usuario=LNG_USUARIO,
    )

    assert eta is None


def test_proximo_horario_previsto_encontra_o_seguinte():
    agora = datetime(2026, 9, 27, 6, 10, tzinfo=FUSO)

    assert (
        proximo_horario_previsto(["06:00", "06:20", "06:40"], agora) == "06:20"
    )


def test_proximo_horario_previsto_apos_ultimo_do_dia_cai_pro_primeiro():
    # Cenário 3: sem GPS e já passou do último horário — melhor sugerir
    # a primeira partida de amanhã do que não devolver nada.
    agora = datetime(2026, 9, 27, 23, 50, tzinfo=FUSO)

    assert proximo_horario_previsto(["06:00", "06:20"], agora) == "06:00"


def test_proximo_horario_previsto_lista_vazia():
    agora = datetime(2026, 9, 27, 6, 10, tzinfo=FUSO)

    assert proximo_horario_previsto([], agora) is None


def test_proximo_horario_previsto_ignora_horarios_invalidos():
    agora = datetime(2026, 9, 27, 6, 10, tzinfo=FUSO)

    assert (
        proximo_horario_previsto(["nao é horário", "06:20"], agora) == "06:20"
    )
