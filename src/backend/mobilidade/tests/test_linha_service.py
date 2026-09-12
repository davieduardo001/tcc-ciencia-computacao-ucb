import asyncio

from mobilidade.linha_service import LinhaService
from mobilidade.models.linha import Linha
from mobilidade.providers.contratos import LinhaEncontrada, ParadaLinha
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
