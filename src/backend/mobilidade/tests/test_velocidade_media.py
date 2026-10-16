"""
Velocidade efetivamente percorrida (card #179, D3b).

O histórico fica em memória, por veículo com linha atribuída, e alimenta
`PosicaoVeiculo.velocidade_media_kmh`. Aqui se testa a regra — quanto o
ônibus andou, de verdade, na janela — e as bordas que fariam o ETA mentir:
pouco dado, veículo parado, salto de GPS, leitura repetida.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from mobilidade.posicao_service import (
    FUSO_SEMOB,
    HISTORICO_MAXIMO_S,
    LEITURAS_MAXIMAS,
    VELOCIDADE_MEDIA_MAXIMA_KMH,
    PosicaoService,
)
from mobilidade.tests.test_posicao_service import _feed, _resposta, _veiculo

# ~0,0045° de latitude = ~500 m
GRAU_500M = 0.0045
LAT0, LNG0 = -15.8000, -48.0000
PREFIXO = "440000"


def _snapshot(minutos_atras: float, lat: float, prefixo: str = PREFIXO, numero: str = "0.110"):
    return _feed(_veiculo(numero, prefixo=prefixo, minutos=minutos_atras, lat=lat, lng=LNG0))


def _registrar(service: PosicaoService, trajetoria: list[tuple[float, float]]):
    """`trajetoria` = [(minutos_atras, lat), …], do mais antigo ao mais novo."""
    for minutos_atras, lat in trajetoria:
        service._registrar_historico(_snapshot(minutos_atras, lat))


def _agora() -> datetime:
    return datetime.now(FUSO_SEMOB)


def _media(service: PosicaoService, prefixo: str = PREFIXO) -> float | None:
    return service._velocidade_media_kmh(prefixo, _agora())


def test_onibus_em_movimento_constante_da_a_velocidade_real():
    service = PosicaoService()
    # 500 m a cada minuto durante 4 min = 30 km/h
    _registrar(service, [(4, LAT0), (3, LAT0 + GRAU_500M), (2, LAT0 + 2 * GRAU_500M),
                         (1, LAT0 + 3 * GRAU_500M), (0, LAT0 + 4 * GRAU_500M)])

    assert _media(service) == pytest.approx(30.0, rel=0.05)


def test_onibus_parado_na_janela_inteira_da_media_perto_de_zero():
    service = PosicaoService()
    _registrar(service, [(4, LAT0), (3, LAT0), (2, LAT0), (1, LAT0), (0, LAT0)])

    assert _media(service) == pytest.approx(0.0, abs=0.5)


def test_parada_e_arranca_entra_na_conta_e_fica_abaixo_da_instantanea():
    service = PosicaoService()
    # anda 1 km nos primeiros 2 min (30 km/h) e fica 2 min parado
    _registrar(service, [(4, LAT0), (3, LAT0 + GRAU_500M), (2, LAT0 + 2 * GRAU_500M),
                         (1, LAT0 + 2 * GRAU_500M), (0, LAT0 + 2 * GRAU_500M)])

    # 1 km em 4 min = 15 km/h, e não os 30 km/h do trecho em movimento
    assert _media(service) == pytest.approx(15.0, rel=0.05)


def test_pouca_leitura_nao_forma_media():
    service = PosicaoService()
    _registrar(service, [(2, LAT0), (0, LAT0 + GRAU_500M)])

    assert _media(service) is None


def test_intervalo_curto_demais_nao_forma_media():
    service = PosicaoService()
    # 3 leituras, mas todas dentro de ~40 s: a média só repetiria o ruído
    for segundos_atras, lat in [(40, LAT0), (20, LAT0 + 0.0005), (0, LAT0 + 0.001)]:
        service._registrar_historico(_snapshot(segundos_atras / 60, lat))

    assert _media(service) is None


def test_veiculo_sem_historico_fica_sem_media():
    assert _media(PosicaoService(), prefixo="999999") is None


def test_leitura_repetida_do_feed_nao_duplica_no_historico():
    service = PosicaoService()
    snapshot = _snapshot(1, LAT0)

    service._registrar_historico(snapshot)
    service._registrar_historico(snapshot)
    service._registrar_historico(snapshot)

    assert len(service._historico[PREFIXO]) == 1


def test_leitura_mais_antiga_que_a_ultima_e_ignorada():
    service = PosicaoService()
    service._registrar_historico(_snapshot(1, LAT0))
    service._registrar_historico(_snapshot(3, LAT0 - 0.01))  # chegou fora de ordem

    assert len(service._historico[PREFIXO]) == 1


def test_so_registra_veiculo_com_linha_atribuida():
    service = PosicaoService()
    service._registrar_historico(
        _feed(_veiculo("", prefixo="999999", lat=LAT0, lng=LNG0), _veiculo("0.110", prefixo="440000"))
    )

    assert set(service._historico) == {"440000"}


def test_leitura_velha_demais_nem_entra():
    service = PosicaoService()
    service._registrar_historico(_snapshot(HISTORICO_MAXIMO_S / 60 + 5, LAT0))

    assert PREFIXO not in service._historico


def test_veiculo_que_parou_de_reportar_sai_do_historico():
    service = PosicaoService()
    service._registrar_historico(_snapshot(1, LAT0))
    assert PREFIXO in service._historico

    # simula o tempo passando: a leitura do veículo agora é velha demais
    service._historico[PREFIXO][-1] = (
        _agora() - timedelta(seconds=HISTORICO_MAXIMO_S + 60),
        LAT0,
        LNG0,
    )
    service._registrar_historico(_feed(_veiculo("0.110", prefixo="outro", minutos=0.1)))

    assert PREFIXO not in service._historico


def test_historico_tem_tamanho_maximo_por_veiculo():
    service = PosicaoService()
    for i in range(LEITURAS_MAXIMAS + 15):
        # leituras de 1 s em 1 s, todas dentro da janela de retenção
        service._registrar_historico(_snapshot((LEITURAS_MAXIMAS + 15 - i) / 60, LAT0 + i * 1e-6))

    assert len(service._historico[PREFIXO]) == LEITURAS_MAXIMAS


def test_salto_de_gps_nao_vira_velocidade_absurda():
    service = PosicaoService()
    # 50 km em ~2 min: um erro de GPS, não um ônibus a 1.500 km/h
    _registrar(service, [(4, LAT0), (3, LAT0), (2, LAT0 + 0.45), (1, LAT0 + 0.45), (0, LAT0 + 0.45)])

    assert _media(service) == VELOCIDADE_MEDIA_MAXIMA_KMH


def test_posicoes_da_linha_ja_traz_a_media_quando_ha_historico():
    service = PosicaoService()
    _registrar(service, [(4, LAT0), (3, LAT0 + GRAU_500M), (2, LAT0 + 2 * GRAU_500M),
                         (1, LAT0 + 3 * GRAU_500M)])
    feed_atual = _snapshot(0, LAT0 + 4 * GRAU_500M)

    async def consultar():
        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_resposta(feed_atual))):
            resultado = await service.posicoes_da_linha("0.110")
        return resultado

    [veiculo] = asyncio.run(consultar())

    assert veiculo.velocidade == 32.0  # a do instante continua lá…
    assert veiculo.velocidade_media_kmh == pytest.approx(30.0, rel=0.05)  # …e a média ao lado


def test_primeira_consulta_do_processo_nao_tem_media_e_nao_quebra():
    # Fly escala a zero: processo novo = histórico vazio.
    service = PosicaoService()

    async def consultar():
        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_resposta(_snapshot(0, LAT0)))):
            return await service.posicoes_da_linha("0.110")

    [veiculo] = asyncio.run(consultar())

    assert veiculo.velocidade_media_kmh is None
    assert veiculo.velocidade == 32.0


def test_falha_no_historico_nunca_derruba_o_feed():
    service = PosicaoService()

    async def consultar():
        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_resposta(_snapshot(0, LAT0)))), \
             patch.object(PosicaoService, "_registrar_historico", side_effect=RuntimeError("boom")):
            return await service.posicoes_da_linha("0.110")

    resultado = asyncio.run(consultar())

    assert len(resultado) == 1  # o feed foi servido mesmo assim
