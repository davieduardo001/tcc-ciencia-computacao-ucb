"""US #115 — cálculo de horário sobre as opções de viagem (sem banco)."""

from datetime import datetime

from mobilidade.planejamento_horario import (
    ESPERA_MAXIMA_MIN,
    DadosPerna,
    planejar_chegando_ate,
    planejar_saindo_as,
)
from mobilidade.posicao_service import FUSO_SEMOB

SEGUNDA = (2026, 11, 2)  # weekday() == 0


def _em(hhmm: str, data=SEGUNDA) -> datetime:
    horas, minutos = hhmm.split(":")
    return datetime(*data, int(horas), int(minutos), tzinfo=FUSO_SEMOB)


def _hhmm(instante: datetime) -> str:
    return instante.astimezone(FUSO_SEMOB).strftime("%H:%M")


def _perna(saidas, percurso=60.0, embarque=0.0, desembarque=1.0, caminhada=0.0, dia="0"):
    return DadosPerna(
        saidas_por_dia={dia: saidas},
        percurso_min=percurso,
        fracao_embarque=embarque,
        fracao_desembarque=desembarque,
        caminhada_ate_embarque_min=caminhada,
    )


# --- Cenário 1: sair às X --------------------------------------------------


def test_sair_as_pega_o_primeiro_onibus_depois_da_partida():
    plano = planejar_saindo_as([_perna(["07:00", "07:30", "08:00"])], 0.0, _em("07:10"))

    assert _hhmm(plano.pernas[0].embarca_em) == "07:30"
    assert _hhmm(plano.pernas[0].desembarca_em) == "08:30"
    assert plano.pernas[0].espera_min == 20
    assert _hhmm(plano.saida_casa) == "07:10"
    assert _hhmm(plano.chegada_destino) == "08:30"


def test_sair_as_desconta_a_caminhada_ate_o_ponto():
    # Sai 07:10, caminha 10 min: chega no ponto 07:20 e perde o das 07:15.
    plano = planejar_saindo_as(
        [_perna(["07:15", "07:45"], caminhada=10.0)], 0.0, _em("07:10")
    )

    assert _hhmm(plano.pernas[0].embarca_em) == "07:45"
    assert plano.pernas[0].espera_min == 25


def test_embarque_no_meio_do_trajeto_usa_a_fracao_do_percurso():
    # Sobe a 50% do percurso de 60 min: o ônibus das 07:00 passa às 07:30
    # e desce a 100%, às 08:00.
    plano = planejar_saindo_as(
        [_perna(["07:00"], embarque=0.5, desembarque=1.0)], 0.0, _em("07:00")
    )

    assert _hhmm(plano.pernas[0].embarca_em) == "07:30"
    assert _hhmm(plano.pernas[0].desembarca_em) == "08:00"


# --- Cenário 3: baldeação com espera ---------------------------------------


def test_baldeacao_mostra_a_espera_no_ponto_de_troca():
    primeira = _perna(["07:00"], percurso=30.0)  # chega 07:30
    segunda = _perna(["07:20", "07:45"], percurso=40.0)  # perde 07:20, pega 07:45

    plano = planejar_saindo_as([primeira, segunda], 0.0, _em("07:00"))

    assert _hhmm(plano.pernas[0].desembarca_em) == "07:30"
    assert _hhmm(plano.pernas[1].embarca_em) == "07:45"
    assert plano.pernas[1].espera_min == 15
    assert _hhmm(plano.chegada_destino) == "08:25"


def test_baldeacao_conta_a_caminhada_entre_as_paradas():
    primeira = _perna(["07:00"], percurso=30.0)  # chega 07:30
    segunda = _perna(["07:35", "08:00"], percurso=20.0, caminhada=8.0)  # ponto 07:38

    plano = planejar_saindo_as([primeira, segunda], 0.0, _em("07:00"))

    assert _hhmm(plano.pernas[1].embarca_em) == "08:00"
    assert plano.pernas[1].espera_min == 22


def test_caminhada_final_entra_na_chegada():
    plano = planejar_saindo_as([_perna(["07:00"])], 5.0, _em("07:00"))

    assert _hhmm(plano.chegada_destino) == "08:05"


# --- Cenário 4: dia da semana ----------------------------------------------


def test_usa_a_tabela_do_dia_da_semana():
    # Só há saída no sábado ("5"): numa segunda não há ônibus.
    sabado = _perna(["09:00"], dia="5")

    assert planejar_saindo_as([sabado], 0.0, _em("08:00")) is None
    plano = planejar_saindo_as([sabado], 0.0, _em("08:00", data=(2026, 10, 31)))
    assert _hhmm(plano.pernas[0].embarca_em) == "09:00"


def test_saida_da_madrugada_do_dia_anterior_passa_depois_da_meia_noite():
    # Saída 23:50 de domingo, com 60 min de percurso e parada a 50%:
    # passa às 00:20 de segunda.
    perna = DadosPerna(
        saidas_por_dia={"6": ["23:50"]},
        percurso_min=60.0,
        fracao_embarque=0.5,
        fracao_desembarque=1.0,
        caminhada_ate_embarque_min=0.0,
    )

    plano = planejar_saindo_as([perna], 0.0, _em("00:10"))

    assert _hhmm(plano.pernas[0].embarca_em) == "00:20"


# --- Cenário 5: sem viagem possível ----------------------------------------


def test_sem_onibus_no_horario_devolve_none():
    assert planejar_saindo_as([_perna(["06:00"])], 0.0, _em("23:30")) is None


def test_espera_maior_que_o_limite_nao_e_viagem():
    # Primeiro ônibus daqui a mais que ESPERA_MAXIMA_MIN.
    assert planejar_saindo_as([_perna(["12:00"])], 0.0, _em("07:00")) is None
    assert ESPERA_MAXIMA_MIN == 180.0


# --- Cenário 2: chegar até X -----------------------------------------------


def test_chegar_ate_escolhe_o_onibus_mais_tardio_que_chega_a_tempo():
    # Precisa estar lá às 08:00. O das 07:00 chega 08:00; o das 07:30, 08:30.
    plano = planejar_chegando_ate([_perna(["06:30", "07:00", "07:30"])], 0.0, _em("08:00"))

    assert _hhmm(plano.pernas[0].embarca_em) == "07:00"
    assert _hhmm(plano.pernas[0].desembarca_em) == "08:00"
    assert _hhmm(plano.saida_casa) == "07:00"
    assert _hhmm(plano.chegada_destino) == "08:00"


def test_chegar_ate_desconta_caminhadas():
    # Chegar até 08:00 com 5 min a pé no fim: o ônibus tem de descer até 07:55
    # (o das 07:00 desce 08:00 → fica o das 06:30, que desce 07:30).
    # Saída de casa = embarque - 10 min de caminhada.
    plano = planejar_chegando_ate(
        [_perna(["06:30", "07:00"], caminhada=10.0)], 5.0, _em("08:00")
    )

    assert _hhmm(plano.pernas[0].embarca_em) == "06:30"
    assert _hhmm(plano.saida_casa) == "06:20"
    assert _hhmm(plano.chegada_destino) == "07:35"


def test_chegar_ate_com_baldeacao_encadeia_de_tras_para_frente():
    primeira = _perna(["06:00", "06:30", "07:00"], percurso=30.0)
    segunda = _perna(["07:30", "08:00"], percurso=30.0)  # precisa descer até 09:00

    plano = planejar_chegando_ate([primeira, segunda], 0.0, _em("09:00"))

    # 2ª perna: o das 08:00 chega 08:30... o das 08:00 é o último que chega até 09:00
    assert _hhmm(plano.pernas[1].embarca_em) == "08:00"
    assert _hhmm(plano.pernas[1].desembarca_em) == "08:30"
    # 1ª perna: precisa descer até 08:00; o das 07:00 desce 07:30 → espera 30 min
    assert _hhmm(plano.pernas[0].desembarca_em) == "07:30"
    assert plano.pernas[1].espera_min == 30
    assert _hhmm(plano.saida_casa) == "07:00"


def test_chegar_ate_sem_onibus_devolve_none():
    assert planejar_chegando_ate([_perna(["11:00"])], 0.0, _em("08:00")) is None
