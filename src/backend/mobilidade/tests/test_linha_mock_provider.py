import asyncio

from mobilidade.providers.linha_mock import LinhaMockProvider


def test_busca_linha_conhecida():
    provider = LinhaMockProvider()

    resultado = asyncio.run(provider.buscar_linha("0.110"))

    assert resultado is not None
    assert resultado.numero == "0.110"
    assert resultado.sentido == "Taguatinga → Rodoviária do Plano Piloto"
    assert len(resultado.paradas) > 0
    assert len(resultado.trajeto) > 0
    assert len(resultado.horarios_previstos) > 0


def test_linha_desconhecida_retorna_none():
    provider = LinhaMockProvider()

    resultado = asyncio.run(provider.buscar_linha("9.999"))

    assert resultado is None
