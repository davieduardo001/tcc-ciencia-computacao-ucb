"""
US #19 (ETA ao longo do trajeto) e US #159 (ETA da rota planejada).

Trajeto sintético em linha reta, no mesmo estilo de test_rota_service.py:
o que se testa aqui é a regra ("projeta no trajeto, descarta sentido
errado e quem já passou, estima headway pela mediana"), não a geometria
real do SEMOB — essa já é coberta em test_ingestao_semob.py.
"""

from datetime import datetime, timedelta, timezone

from mobilidade.eta_service import (
    EstimativaViagem,
    eta_minutos_veiculo,
    estimar_viagem,
    intervalo_medio_min,
)
from mobilidade.geometria import TrajetoMedido
from mobilidade.posicao_service import PosicaoVeiculo
from mobilidade.rota_service import PontoEmbarque, Perna, OpcaoViagem

LAT = -15.80
PASSO_GRAUS = 0.001  # ~111 m
QTD_PONTOS = 40
TRAJETO = [(LAT, -48.10 + PASSO_GRAUS * i) for i in range(QTD_PONTOS)]
TRAJETO_MEDIDO = TrajetoMedido(TRAJETO)

AGORA = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)

# Índice 30 do trajeto (~3,2 km do início) é a parada de embarque usada
# nos testes de ETA por trajeto.
INDICE_EMBARQUE = 30


def _veiculo(indice_trajeto, velocidade=30.0, sentido="IDA", idade_min=0.0, prefixo="440001"):
    lat, lng = TRAJETO[indice_trajeto]
    return PosicaoVeiculo(
        prefixo=prefixo,
        lat=lat,
        lng=lng,
        sentido=sentido,
        velocidade=velocidade,
        direcao=0.0,
        atualizado_em=AGORA - timedelta(minutes=idade_min),
        operadora="VIAÇÃO TESTE",
    )


# --------------------------------------------------------------------------
# eta_minutos_veiculo — ETA por trajeto (US #19)
# --------------------------------------------------------------------------


def test_eta_por_trajeto_veiculo_se_aproximando():
    veiculo = _veiculo(indice_trajeto=10, velocidade=30.0)  # ~2,2 km do embarque
    lat_alvo, lng_alvo = TRAJETO[INDICE_EMBARQUE]

    eta = eta_minutos_veiculo(
        veiculo,
        lat_alvo=lat_alvo,
        lng_alvo=lng_alvo,
        agora=AGORA,
        trajeto=TRAJETO_MEDIDO,
        sentido_alvo="IDA",
    )

    assert eta is not None
    assert 3.0 < eta < 6.0


def test_eta_por_trajeto_sentido_errado_fica_sem_eta():
    veiculo = _veiculo(indice_trajeto=10, sentido="VOLTA")
    lat_alvo, lng_alvo = TRAJETO[INDICE_EMBARQUE]

    eta = eta_minutos_veiculo(
        veiculo,
        lat_alvo=lat_alvo,
        lng_alvo=lng_alvo,
        agora=AGORA,
        trajeto=TRAJETO_MEDIDO,
        sentido_alvo="IDA",
    )

    assert eta is None


def test_eta_por_trajeto_veiculo_que_ja_passou_fica_sem_eta():
    # Índice 35 é depois da parada-alvo (30): o ônibus já passou.
    veiculo = _veiculo(indice_trajeto=35, sentido="IDA")
    lat_alvo, lng_alvo = TRAJETO[INDICE_EMBARQUE]

    eta = eta_minutos_veiculo(
        veiculo,
        lat_alvo=lat_alvo,
        lng_alvo=lng_alvo,
        agora=AGORA,
        trajeto=TRAJETO_MEDIDO,
        sentido_alvo="IDA",
    )

    assert eta is None


def test_eta_por_trajeto_circular_da_a_volta_para_quem_ja_passou():
    veiculo = _veiculo(indice_trajeto=35, sentido="CIRCULAR")
    lat_alvo, lng_alvo = TRAJETO[INDICE_EMBARQUE]

    eta = eta_minutos_veiculo(
        veiculo,
        lat_alvo=lat_alvo,
        lng_alvo=lng_alvo,
        agora=AGORA,
        trajeto=TRAJETO_MEDIDO,
        sentido_alvo="CIRCULAR",
    )

    assert eta is not None and eta > 0


def test_eta_por_trajeto_circular_aceita_veiculo_reportando_ida_ou_volta():
    """
    Regressão: conferido contra o feed real do SEMOB — veículo de linha
    circular nunca reporta "CIRCULAR" como o próprio sentido (vem
    "IDA", "VOLTA" ou None). Exigir igualdade rejeitaria toda linha
    circular, mesmo rodando (foi o que aconteceu na prática: 3 ônibus
    ativos na linha e nenhum ETA calculado).
    """
    lat_alvo, lng_alvo = TRAJETO[INDICE_EMBARQUE]

    for sentido_reportado in ("IDA", "VOLTA", None):
        veiculo = _veiculo(indice_trajeto=10, sentido=sentido_reportado)
        eta = eta_minutos_veiculo(
            veiculo,
            lat_alvo=lat_alvo,
            lng_alvo=lng_alvo,
            agora=AGORA,
            trajeto=TRAJETO_MEDIDO,
            sentido_alvo="CIRCULAR",
        )
        assert eta is not None and eta > 0, f"sentido reportado {sentido_reportado!r} deveria contar"


def test_eta_por_trajeto_posicao_velha_fica_sem_eta():
    veiculo = _veiculo(indice_trajeto=10, idade_min=10.0)  # > IDADE_MAXIMA_ETA_MIN
    lat_alvo, lng_alvo = TRAJETO[INDICE_EMBARQUE]

    eta = eta_minutos_veiculo(
        veiculo,
        lat_alvo=lat_alvo,
        lng_alvo=lng_alvo,
        agora=AGORA,
        trajeto=TRAJETO_MEDIDO,
        sentido_alvo="IDA",
    )

    assert eta is None


def test_eta_por_trajeto_veiculo_fora_do_tracado_fica_sem_eta():
    veiculo = PosicaoVeiculo(
        prefixo="440001",
        lat=LAT + 1.0,  # ~111 km de distância do trajeto
        lng=-48.10,
        sentido="IDA",
        velocidade=30.0,
        direcao=0.0,
        atualizado_em=AGORA,
        operadora="VIAÇÃO TESTE",
    )
    lat_alvo, lng_alvo = TRAJETO[INDICE_EMBARQUE]

    eta = eta_minutos_veiculo(
        veiculo,
        lat_alvo=lat_alvo,
        lng_alvo=lng_alvo,
        agora=AGORA,
        trajeto=TRAJETO_MEDIDO,
        sentido_alvo="IDA",
    )

    assert eta is None


def test_eta_sem_trajeto_cai_para_linha_reta():
    # Compatibilidade com a US #19 original: sem trajeto conhecido,
    # continua calculando por distância em linha reta.
    veiculo = _veiculo(indice_trajeto=10, sentido="VOLTA")  # sentido nem importa aqui
    lat_alvo, lng_alvo = TRAJETO[INDICE_EMBARQUE]

    eta = eta_minutos_veiculo(
        veiculo, lat_alvo=lat_alvo, lng_alvo=lng_alvo, agora=AGORA, trajeto=None
    )

    assert eta is not None and eta > 0


# --------------------------------------------------------------------------
# intervalo_medio_min — headway (US #159)
# --------------------------------------------------------------------------


def test_intervalo_medio_com_tres_veiculos_igualmente_espacados():
    veiculos = [_veiculo(i, prefixo=f"44000{n}") for n, i in enumerate((0, 14, 28))]
    intervalo = intervalo_medio_min(veiculos, TRAJETO_MEDIDO, "IDA", AGORA)

    assert intervalo is not None
    # ~1,5 km a 22 km/h (VELOCIDADE_MEDIA_KMH) ≈ 4 min.
    assert 3.0 < intervalo < 5.0


def test_intervalo_medio_com_um_veiculo_so_e_indisponivel():
    veiculos = [_veiculo(10)]
    assert intervalo_medio_min(veiculos, TRAJETO_MEDIDO, "IDA", AGORA) is None


def test_intervalo_medio_ignora_comboio():
    # Dois veículos quase no mesmo ponto (mesma posição reportada 2x, ou
    # um logo atrás do outro) não podem contar como headway de ~0 min.
    veiculos = [_veiculo(10), _veiculo(11), _veiculo(25)]
    intervalo = intervalo_medio_min(veiculos, TRAJETO_MEDIDO, "IDA", AGORA)

    assert intervalo is not None
    assert intervalo > 1.0  # não ficou perto de zero por causa do comboio


def test_intervalo_medio_ignora_veiculo_de_sentido_diferente():
    veiculos = [_veiculo(10, sentido="IDA"), _veiculo(20, sentido="VOLTA")]
    assert intervalo_medio_min(veiculos, TRAJETO_MEDIDO, "IDA", AGORA) is None


def test_intervalo_medio_circular_aceita_veiculos_reportando_ida():
    # Mesma regressão de _eta_por_trajeto: linha circular, veículo
    # reportando "IDA" (nunca "CIRCULAR") — confirmado no feed real.
    veiculos = [_veiculo(i, sentido="IDA", prefixo=f"44002{n}") for n, i in enumerate((0, 14, 28))]
    intervalo = intervalo_medio_min(veiculos, TRAJETO_MEDIDO, "CIRCULAR", AGORA)

    assert intervalo is not None


# --------------------------------------------------------------------------
# estimar_viagem — os 3 cenários BDD da #159
# --------------------------------------------------------------------------


def _perna(numero, sentido, indice_embarque, caminhada_embarque=50, distancia_km=3.0):
    lat, lng = TRAJETO[indice_embarque]
    return Perna(
        numero=numero,
        sentido=sentido,
        nome=f"{numero} — teste",
        embarque=PontoEmbarque(
            lat=lat, lng=lng, parada_nome="Parada Teste", caminhada_metros=caminhada_embarque
        ),
        desembarque=PontoEmbarque(
            lat=TRAJETO[-1][0], lng=TRAJETO[-1][1], parada_nome="Final", caminhada_metros=100
        ),
        distancia_km=distancia_km,
        paradas_no_trecho=5,
        trajeto=TRAJETO[indice_embarque:],
    )


def test_cenario_1_direta_com_onibus_real_se_aproximando():
    perna = _perna("T159.001", "IDA", INDICE_EMBARQUE)
    opcao = OpcaoViagem(pernas=[perna])
    posicoes = {"T159.001": [_veiculo(10, velocidade=30.0)]}
    trajetos = {("T159.001", "IDA"): TRAJETO_MEDIDO}

    estimativa = estimar_viagem(opcao, posicoes, trajetos, AGORA)

    assert isinstance(estimativa, EstimativaViagem)
    assert estimativa.tipo == "tempo_real"
    assert estimativa.duracao_real_min is not None
    assert estimativa.pernas[0].fonte == "tempo_real"
    assert estimativa.pernas[0].espera_min is not None


def test_cenario_2_baldeacao_com_intervalo_estimavel():
    perna1 = _perna("T159.001", "IDA", INDICE_EMBARQUE)
    perna2 = _perna("T159.002", "IDA", indice_embarque=5, distancia_km=2.0)
    opcao = OpcaoViagem(pernas=[perna1, perna2])

    posicoes = {
        "T159.001": [_veiculo(10, velocidade=30.0, prefixo="440001")],
        "T159.002": [_veiculo(i, prefixo=f"44001{n}") for n, i in enumerate((0, 14, 28))],
    }
    trajetos = {
        ("T159.001", "IDA"): TRAJETO_MEDIDO,
        ("T159.002", "IDA"): TRAJETO_MEDIDO,
    }

    estimativa = estimar_viagem(opcao, posicoes, trajetos, AGORA)

    assert estimativa.tipo == "tempo_real"
    assert estimativa.pernas[1].fonte == "intervalo_medio"
    assert estimativa.pernas[1].intervalo_medio_min is not None
    assert estimativa.pernas[1].espera_min is not None
    assert estimativa.duracao_real_min is not None


def test_cenario_3_dado_insuficiente_cai_para_teorica():
    perna = _perna("T159.003", "IDA", INDICE_EMBARQUE)
    opcao = OpcaoViagem(pernas=[perna])

    estimativa = estimar_viagem(opcao, posicoes_por_linha={}, trajetos_por_perna={}, agora=AGORA)

    assert estimativa.tipo == "teorica"
    assert estimativa.duracao_real_min is None
    assert all(p.fonte == "teorica" and p.espera_min is None for p in estimativa.pernas)


def test_baldeacao_sem_intervalo_estimavel_fica_parcial():
    perna1 = _perna("T159.004", "IDA", INDICE_EMBARQUE)
    perna2 = _perna("T159.005", "IDA", indice_embarque=5, distancia_km=2.0)
    opcao = OpcaoViagem(pernas=[perna1, perna2])

    posicoes = {
        "T159.004": [_veiculo(10, velocidade=30.0, prefixo="440001")],
        "T159.005": [],  # sem veículo ativo na 2ª linha: sem headway
    }
    trajetos = {
        ("T159.004", "IDA"): TRAJETO_MEDIDO,
        ("T159.005", "IDA"): TRAJETO_MEDIDO,
    }

    estimativa = estimar_viagem(opcao, posicoes, trajetos, AGORA)

    assert estimativa.tipo == "parcial"
    assert estimativa.pernas[1].fonte == "teorica"
    assert estimativa.pernas[1].espera_min is not None  # espera fixa, não None
    assert estimativa.duracao_real_min is not None


def test_ignora_onibus_que_chega_antes_do_usuario_andar_ate_a_parada():
    # Caminhada de 5 km até a parada: nenhum ônibus chega "antes" disso.
    perna = _perna("T159.006", "IDA", INDICE_EMBARQUE, caminhada_embarque=5000)
    opcao = OpcaoViagem(pernas=[perna])
    posicoes = {"T159.006": [_veiculo(29, velocidade=30.0)]}  # bem perto, ETA ~0
    trajetos = {("T159.006", "IDA"): TRAJETO_MEDIDO}

    estimativa = estimar_viagem(opcao, posicoes, trajetos, AGORA)

    assert estimativa.tipo == "teorica"
