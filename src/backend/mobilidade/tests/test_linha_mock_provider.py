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


def test_listar_resumo_inclui_nomes_das_paradas():
    provider = LinhaMockProvider()

    resumos = asyncio.run(provider.listar_resumo())

    assert len(resumos) >= 2
    resumo_0108 = next(r for r in resumos if r.numero == "0.108")
    assert "Terminal Ceilândia Centro" in resumo_0108.paradas_nomes


def test_mock_e_so_rede_de_seguranca_nao_o_catalogo():
    # O catálogo de verdade (923 linhas do DF) vem da ingestão do SEMOB
    # pra tabela `linha` — ver mobilidade/ingestao_semob.py. O mock só
    # cobre o caso de banco ainda vazio, então continua minúsculo de
    # propósito.
    provider = LinhaMockProvider()

    numeros = {r.numero for r in asyncio.run(provider.listar_resumo())}

    assert numeros == {"0.110", "0.108"}
