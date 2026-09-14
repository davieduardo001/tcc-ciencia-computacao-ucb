"""Testes do rastreamento ao vivo (US #16), com o feed do SEMOB mockado.

As amostras têm a mesma forma da resposta real de /posicao, conferida
contra a API: GeoJSON por operadora, coordenadas em [lng, lat] e
`datalocal` como string "YYYY-MM-DD HH:MM:SS".
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from mobilidade.posicao_service import PosicaoService


def _quando(minutos_atras: float) -> str:
    return (datetime.now() - timedelta(minutes=minutos_atras)).strftime("%Y-%m-%d %H:%M:%S")


def _veiculo(numero, prefixo="440000", minutos=1.0, lng=-47.88, lat=-15.79, sentido="IDA"):
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lng, lat]},
        "properties": {
            "veiculo": {"prefixo": prefixo, "numero": numero, "sentido": sentido, "imei": None},
            "direcao": "0,00",
            "velocidade": "32",
            "datalocal": _quando(minutos),
        },
    }


def _feed(*veiculos, operadora="VIAÇÃO PIRACICABANA - BACIA 01"):
    return [{"type": "FeatureCollection", "NomeOperadora": operadora, "features": list(veiculos)}]


def _resposta(payload):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=payload)
    return resp


def _rodar(service, numero, payload):
    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_resposta(payload))):
        return asyncio.run(_consultar(service, numero))


async def _consultar(service, numero):
    """
    Consulta esperando a renovação em segundo plano terminar.

    Quando o cache vence, o serviço devolve o feed antigo na hora e
    renova por fora (ver PosicaoService._obter_feed). Sem aguardar essa
    task, o resultado do teste dependeria de a corrotina alcançar a
    execução antes de `asyncio.run` fechar o loop — flaky por
    construção.
    """
    resultado = await service.posicoes_da_linha(numero)
    if service._renovando is not None:
        await service._renovando
    return resultado


def test_devolve_veiculos_da_linha_buscada():
    payload = _feed(_veiculo("0.110", prefixo="446149"), _veiculo("0.108", prefixo="449342"))

    posicoes = _rodar(PosicaoService(), "0.110", payload)

    assert len(posicoes) == 1
    assert posicoes[0].prefixo == "446149"
    assert posicoes[0].lat == -15.79  # GeoJSON vem [lng, lat]; invertemos
    assert posicoes[0].lng == -47.88
    assert posicoes[0].velocidade == 32.0
    assert posicoes[0].operadora == "VIAÇÃO PIRACICABANA - BACIA 01"


def test_linha_sem_veiculo_devolve_lista_vazia():
    # Cenário 3 da US #16 — estado normal fora do pico, não erro.
    posicoes = _rodar(PosicaoService(), "9.999", _feed(_veiculo("0.110")))

    assert posicoes == []


def test_ignora_veiculo_com_posicao_velha():
    # Frota em garagem fica dias com a última posição registrada.
    payload = _feed(_veiculo("0.110", minutos=1), _veiculo("0.110", prefixo="000001", minutos=120))

    posicoes = _rodar(PosicaoService(), "0.110", payload)

    assert [p.prefixo for p in posicoes] == ["440000"]


def test_ignora_veiculo_sem_linha_atribuida():
    # 1.897 dos 2.428 veículos com posição recente vêm assim (medido).
    payload = _feed(_veiculo("", prefixo="999999"), _veiculo("0.110"))

    posicoes = _rodar(PosicaoService(), "0.110", payload)

    assert [p.prefixo for p in posicoes] == ["440000"]


def test_numero_vazio_nao_chama_o_semob():
    service = PosicaoService()

    with patch("httpx.AsyncClient.get", new=AsyncMock()) as get_mock:
        resultado = asyncio.run(service.posicoes_da_linha("  "))

    assert resultado == []
    get_mock.assert_not_called()


def test_feed_e_cacheado_entre_chamadas():
    # O feed é global: baixar uma vez serve todas as linhas e todos os
    # usuários. Sem cache, cada mapa aberto puxaria o payload inteiro.
    service = PosicaoService(cache_segundos=60)
    payload = _feed(_veiculo("0.110"))

    with patch(
        "httpx.AsyncClient.get", new=AsyncMock(return_value=_resposta(payload))
    ) as get_mock:
        asyncio.run(service.posicoes_da_linha("0.110"))
        asyncio.run(service.posicoes_da_linha("0.110"))
        asyncio.run(service.posicoes_da_linha("0.108"))

    assert get_mock.await_count == 1


def test_cache_expira_e_busca_de_novo():
    service = PosicaoService(cache_segundos=0)
    payload = _feed(_veiculo("0.110"))

    with patch(
        "httpx.AsyncClient.get", new=AsyncMock(return_value=_resposta(payload))
    ) as get_mock:
        asyncio.run(_consultar(service, "0.110"))
        asyncio.run(_consultar(service, "0.110"))

    assert get_mock.await_count == 2


def test_cache_vencido_responde_na_hora_sem_esperar_o_download():
    """
    O ponto central do desenho: quando o cache vence, a resposta sai com
    o feed anterior e o download acontece por fora.

    Sem isso, o usuário esperaria o `/posicao` a cada 20 s de polling — e
    esse endpoint são ~870 KB cujo tempo de resposta, medido em 13/09,
    variou de 2,6 s a 24,8 s para o mesmo payload.
    """
    service = PosicaoService(cache_segundos=0)
    primeiro = _feed(_veiculo("0.110", prefixo="AAA"))
    segundo = _feed(_veiculo("0.110", prefixo="BBB"))

    async def cenario():
        with patch(
            "httpx.AsyncClient.get", new=AsyncMock(return_value=_resposta(primeiro))
        ):
            await service.posicoes_da_linha("0.110")

        travado = asyncio.Event()

        async def download_lento(*_args, **_kwargs):
            await travado.wait()
            return _resposta(segundo)

        with patch("httpx.AsyncClient.get", new=download_lento):
            # Mesmo com o download pendurado, a resposta sai na hora com
            # o que já estava em cache.
            resultado = await asyncio.wait_for(
                service.posicoes_da_linha("0.110"), timeout=1.0
            )
            assert [v.prefixo for v in resultado] == ["AAA"]

            travado.set()
            await service._renovando

        # Depois que a renovação termina, o feed novo passa a valer.
        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_resposta(segundo))):
            assert [v.prefixo for v in await service.posicoes_da_linha("0.110")] == ["BBB"]

    asyncio.run(cenario())


def test_partida_a_frio_espera_o_download():
    """Sem nada em cache não há o que servir — aí sim vale esperar."""
    service = PosicaoService()
    payload = _feed(_veiculo("0.110", prefixo="AAA"))

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_resposta(payload))):
        resultado = asyncio.run(service.posicoes_da_linha("0.110"))

    assert [v.prefixo for v in resultado] == ["AAA"]


def test_usuarios_simultaneos_nao_disparam_downloads_repetidos():
    """
    Dez mapas abertos ao mesmo tempo com o cache vencido devem gerar um
    download, não dez — o feed é global.
    """
    service = PosicaoService(cache_segundos=0)
    payload = _feed(_veiculo("0.110"))

    async def cenario():
        with patch(
            "httpx.AsyncClient.get", new=AsyncMock(return_value=_resposta(payload))
        ):
            await service.posicoes_da_linha("0.110")  # aquece o cache
            await service._renovando if service._renovando else None

        travado = asyncio.Event()
        chamadas = 0

        async def download_lento(*_args, **_kwargs):
            nonlocal chamadas
            chamadas += 1
            await travado.wait()
            return _resposta(payload)

        with patch("httpx.AsyncClient.get", new=download_lento):
            await asyncio.gather(
                *(service.posicoes_da_linha("0.110") for _ in range(10))
            )
            travado.set()
            await service._renovando

        assert chamadas == 1

    asyncio.run(cenario())


def test_semob_fora_do_ar_nao_quebra_a_busca():
    import httpx

    service = PosicaoService()

    with patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=httpx.ConnectError("fora"))):
        resultado = asyncio.run(service.posicoes_da_linha("0.110"))

    assert resultado == []


def test_mantem_ultimo_feed_quando_o_semob_falha_depois():
    service = PosicaoService(cache_segundos=0)
    payload = _feed(_veiculo("0.110"))

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_resposta(payload))):
        assert len(asyncio.run(service.posicoes_da_linha("0.110"))) == 1

    import httpx

    with patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=httpx.ConnectError("fora"))):
        # Cache expirado + origem fora do ar: melhor a última posição
        # conhecida do que sumir com os ônibus da tela.
        assert len(asyncio.run(service.posicoes_da_linha("0.110"))) == 1
