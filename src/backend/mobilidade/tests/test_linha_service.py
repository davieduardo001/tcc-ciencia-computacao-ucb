import asyncio
from unittest.mock import AsyncMock, patch

from mobilidade.linha_service import LinhaService
from mobilidade.models.linha import Linha
from mobilidade.providers.contratos import LinhaEncontrada, LinhaResumo, ParadaLinha
from mobilidade.providers.linha_mock import LinhaMockProvider
from shared.database import SessionLocal


class _ProviderContador:
    """Provider de teste que conta quantas vezes foi chamado."""

    def __init__(self) -> None:
        self.chamadas = 0

    async def buscar_linha(self, numero_linha: str) -> LinhaEncontrada | None:
        self.chamadas += 1
        if numero_linha != "9.001":
            return None
        return LinhaEncontrada(
            numero="9.001",
            nome="9.001 — Linha de Teste",
            sentido="Teste → Teste",
            paradas=[ParadaLinha(nome="Parada Teste", lat=-15.83, lng=-48.04)],
            trajeto=[(-15.83, -48.04)],
            horarios_previstos=["10:00"],
        )

    async def listar_resumo(self) -> list[LinhaResumo]:
        return [
            LinhaResumo(
                numero="9.001",
                nome="9.001 — Linha de Teste",
                sentido="Teste → Teste",
                paradas_nomes=["Parada Teste"],
            )
        ]


def _limpar_linha_teste(db):
    db.query(Linha).filter(Linha.numero == "9.001").delete()
    db.commit()


def test_segunda_busca_nao_chama_o_provider_de_novo():
    db = SessionLocal()
    try:
        _limpar_linha_teste(db)

        provider = _ProviderContador()
        service = LinhaService(provider)

        primeiro = asyncio.run(service.buscar("9.001", db))
        segundo = asyncio.run(service.buscar("9.001", db))

        assert primeiro is not None
        assert segundo is not None
        assert primeiro.numero == segundo.numero == "9.001"
        assert provider.chamadas == 1, (
            "A segunda busca deveria usar o cache do banco, sem chamar "
            "o provider de novo."
        )
    finally:
        _limpar_linha_teste(db)
        db.close()


def test_linha_nao_encontrada_no_provider_retorna_none():
    db = SessionLocal()
    try:
        provider = _ProviderContador()
        service = LinhaService(provider)

        resultado = asyncio.run(service.buscar("0.000-inexistente", db))

        assert resultado is None
        assert provider.chamadas == 1
    finally:
        db.close()


# ---------------------------------------------------------------------------
# US #17 (autocomplete) — LinhaService.sugerir
# ---------------------------------------------------------------------------


def test_sugerir_com_termo_vazio_lista_todas_as_linhas():
    service = LinhaService(_ProviderContador())

    resultado = asyncio.run(service.sugerir(""))

    assert len(resultado) == 1
    assert resultado[0].numero == "9.001"


def test_sugerir_combina_por_numero_nome_sentido_ou_parada():
    service = LinhaService(_ProviderContador())

    assert len(asyncio.run(service.sugerir("9.001"))) == 1
    assert len(asyncio.run(service.sugerir("Linha de Teste"))) == 1
    assert len(asyncio.run(service.sugerir("Teste →"))) == 1
    assert len(asyncio.run(service.sugerir("Parada Teste"))) == 1


def test_sugerir_ignora_acentos_e_maiusculas():
    service = LinhaService(_ProviderContador())

    # "Parada Teste" não tem acento, mas o normalizador precisa lidar
    # com termo digitado sem acento/maiúsculo de qualquer forma —
    # ex real: buscar "ceilandia" deve encontrar "Ceilândia".
    resultado = asyncio.run(service.sugerir("PARADA teste"))

    assert len(resultado) == 1


def test_sugerir_sem_combinacao_retorna_lista_vazia():
    service = LinhaService(_ProviderContador())

    resultado = asyncio.run(service.sugerir("nao existe em lugar nenhum"))

    assert resultado == []


# ---------------------------------------------------------------------------
# Road-snapping via OSRM (só pro LinhaMockProvider — ver _com_trajeto_real)
# ---------------------------------------------------------------------------


def _limpar_numero(db, numero: str) -> None:
    db.query(Linha).filter(Linha.numero == numero).delete()
    db.commit()


def test_busca_com_mock_provider_usa_trajeto_do_osrm_quando_disponivel():
    db = SessionLocal()
    try:
        # Força cache-miss: se "0.110" já estivesse cacheado (de outro
        # teste), o provider nem seria chamado e o mock do OSRM nunca
        # entraria em jogo.
        _limpar_numero(db, "0.110")

        provider = LinhaMockProvider()
        service = LinhaService(provider)

        trajeto_osrm = [(-15.83, -48.04), (-15.80, -47.90), (-15.79, -47.88)]
        with patch(
            "mobilidade.linha_service.osrm_router.rotear",
            AsyncMock(return_value=trajeto_osrm),
        ):
            resultado = asyncio.run(service.buscar("0.110", db))

        assert resultado is not None
        assert resultado.trajeto == trajeto_osrm
    finally:
        _limpar_numero(db, "0.110")
        db.close()


def test_busca_com_mock_provider_mantem_trajeto_original_se_osrm_falhar():
    db = SessionLocal()
    try:
        _limpar_numero(db, "0.110")

        provider = LinhaMockProvider()
        service = LinhaService(provider)

        with patch(
            "mobilidade.linha_service.osrm_router.rotear",
            AsyncMock(return_value=None),
        ):
            resultado = asyncio.run(service.buscar("0.110", db))

        assert resultado is not None
        assert len(resultado.trajeto) > 0
    finally:
        _limpar_numero(db, "0.110")
        db.close()


def test_busca_com_provider_nao_mock_nao_chama_osrm():
    db = SessionLocal()
    try:
        _limpar_linha_teste(db)

        service = LinhaService(_ProviderContador())

        with patch(
            "mobilidade.linha_service.osrm_router.rotear",
            AsyncMock(return_value=[(-1.0, -1.0)]),
        ) as rotear_mock:
            resultado = asyncio.run(service.buscar("9.001", db))

        assert resultado is not None
        assert resultado.trajeto == [(-15.83, -48.04)]  # inalterado
        rotear_mock.assert_not_called()
    finally:
        db.query(Linha).filter(Linha.numero == "9.001").delete()
        db.commit()
        db.close()


# ---------------------------------------------------------------------------
# Catálogo vindo do banco (linhas reais ingeridas do SEMOB)
# ---------------------------------------------------------------------------

NUMERO_CATALOGO = "9.996"


class _SessaoVazia:
    """Sessão que responde 'tabela vazia' — sem depender de banco real."""

    def query(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args):
        return self

    def all(self):
        return []


def _limpar_catalogo(db):
    db.query(Linha).filter(Linha.numero == NUMERO_CATALOGO).delete()
    db.commit()


def _semear_catalogo(db):
    db.add(
        Linha(
            numero=NUMERO_CATALOGO,
            nome=f"{NUMERO_CATALOGO} — Circular Rodoviária / UNB",
            sentido="Circular",
            paradas=[{"nome": "Terminal Ceilândia", "lat": -15.81, "lng": -48.10}],
            trajeto=[[-15.81, -48.10]],
            horarios_previstos=["06:00"],
        )
    )
    db.commit()


def test_sugerir_usa_o_catalogo_do_banco_quando_ha_linhas_ingeridas():
    db = SessionLocal()
    try:
        _limpar_catalogo(db)
        _semear_catalogo(db)

        service = LinhaService(_ProviderContador())
        resultado = asyncio.run(service.sugerir("unb", db))

        numeros = {r.numero for r in resultado}
        assert NUMERO_CATALOGO in numeros
        # "9.001" é do provider mock: não deve aparecer com o banco populado.
        assert "9.001" not in numeros
    finally:
        _limpar_catalogo(db)
        db.close()


def test_sugerir_encontra_linha_do_banco_pelo_nome_da_parada():
    db = SessionLocal()
    try:
        _limpar_catalogo(db)
        _semear_catalogo(db)

        service = LinhaService(_ProviderContador())
        resultado = asyncio.run(service.sugerir("ceilandia", db))

        assert NUMERO_CATALOGO in {r.numero for r in resultado}
    finally:
        _limpar_catalogo(db)
        db.close()


def test_sugerir_cai_pro_provider_quando_o_banco_esta_vazio():
    # Banco novo / ambiente sem ingestão rodada: o catálogo real não
    # existe ainda, então o mock é a rede de segurança.
    service = LinhaService(_ProviderContador())

    resultado = asyncio.run(service.sugerir("", _SessaoVazia()))

    assert {r.numero for r in resultado} == {"9.001"}
