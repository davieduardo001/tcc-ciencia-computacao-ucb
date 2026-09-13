# Serviço de busca de linha com cache sob demanda — US #15
#
# Antes de consultar o LinhaProvider (Google Maps ou mock), verifica se
# a linha já está cacheada no nosso banco e ainda é considerada "fresca"
# (menos de LINHA_CACHE_MAX_DIAS dias). Só chama o provider quando a
# linha nunca foi buscada ou o cache expirou — nunca em lote, nunca por
# usuário/sessão. Isso minimiza o número de chamadas à API externa.

from __future__ import annotations

import logging
import unicodedata
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from mobilidade.models.linha import Linha
from mobilidade.providers.contratos import (
    LinhaEncontrada,
    LinhaProvider,
    LinhaResumo,
    ParadaLinha,
)

logger = logging.getLogger(__name__)

LINHA_CACHE_MAX_DIAS = 30


def _normalizar(texto: str) -> str:
    """Minúsculo e sem acento, pra 'ceilandia' encontrar 'Ceilândia'."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore")
    return sem_acento.decode("ascii").lower()


class LinhaService:
    """
    Serviço de busca de linha para a rota HTTP da US #15.

    Recebe qualquer implementação de LinhaProvider — mock para
    desenvolvimento, LinhaGoogleMapsProvider em produção (quando
    GOOGLE_MAPS_API_KEY estiver configurada). A troca é feita em
    routes.py, sem modificar este arquivo.
    """

    def __init__(self, provider: LinhaProvider) -> None:
        if not isinstance(provider, LinhaProvider):
            raise TypeError(
                f"provider deve satisfazer o contrato LinhaProvider, "
                f"recebido: {type(provider).__name__}"
            )
        self._provider = provider

    async def buscar(self, numero_linha: str, db: Session) -> LinhaEncontrada | None:
        """
        Busca a linha informada, usando o cache do banco quando possível.

        Retorna None quando a linha não é encontrada nem no cache nem no
        provider (Cenário 2 da US #15) — nunca lança exceção para esse
        caso. Falhas do provider (rede, timeout) propagam normalmente,
        para que a rota decida como responder.

        Args:
            numero_linha: identificador textual da linha, ex: "0.110".
            db: sessão de banco ativa (injetada pela rota via Depends).
        """
        if not numero_linha or not numero_linha.strip():
            raise ValueError("numero_linha não pode ser vazio.")

        cache = db.query(Linha).filter(Linha.numero == numero_linha).first()

        if cache is not None and not self._esta_desatualizada(cache):
            return self._registro_para_resultado(cache)

        resultado = await self._provider.buscar_linha(numero_linha)

        if resultado is None:
            return None

        self._salvar_no_cache(db, resultado)
        return resultado

    async def sugerir(self, termo: str) -> list[LinhaResumo]:
        """
        Autocomplete (US #17): sugere linhas cujo número, nome, sentido
        ou alguma parada combine com o termo digitado — buscar
        "Ceilândia" sugere as linhas que passam por lá, não só o número
        exato da linha.

        Termo vazio devolve todas as linhas conhecidas (útil pra listar
        "linhas disponíveis" quando o campo de busca ainda está vazio).

        Não usa cache/banco — a lista de linhas conhecidas vem direto do
        provider (é pequena e estática), então não compensa persistir.
        """
        resumos = await self._provider.listar_resumo()

        termo_normalizado = _normalizar(termo.strip())
        if not termo_normalizado:
            return resumos

        def combina(resumo: LinhaResumo) -> bool:
            campos = [resumo.numero, resumo.nome, resumo.sentido, *resumo.paradas_nomes]
            return any(termo_normalizado in _normalizar(campo) for campo in campos)

        return [resumo for resumo in resumos if combina(resumo)]

    def _esta_desatualizada(self, cache: Linha) -> bool:
        limite = datetime.now(timezone.utc) - timedelta(days=LINHA_CACHE_MAX_DIAS)
        atualizado_em = cache.atualizado_em
        if atualizado_em.tzinfo is None:
            atualizado_em = atualizado_em.replace(tzinfo=timezone.utc)
        return atualizado_em < limite

    def _registro_para_resultado(self, cache: Linha) -> LinhaEncontrada:
        return LinhaEncontrada(
            numero=cache.numero,
            nome=cache.nome,
            sentido=cache.sentido,
            paradas=[ParadaLinha(**p) for p in cache.paradas],
            trajeto=[tuple(p) for p in cache.trajeto],
            horarios_previstos=list(cache.horarios_previstos),
        )

    def _salvar_no_cache(self, db: Session, resultado: LinhaEncontrada) -> None:
        cache = db.query(Linha).filter(Linha.numero == resultado.numero).first()

        paradas_json = [
            {"nome": p.nome, "lat": p.lat, "lng": p.lng} for p in resultado.paradas
        ]
        trajeto_json = [list(ponto) for ponto in resultado.trajeto]

        if cache is None:
            cache = Linha(numero=resultado.numero)
            db.add(cache)

        cache.nome = resultado.nome
        cache.sentido = resultado.sentido
        cache.paradas = paradas_json
        cache.trajeto = trajeto_json
        cache.horarios_previstos = list(resultado.horarios_previstos)

        try:
            db.commit()
        except Exception:
            logger.exception("Falha ao salvar cache da linha %r", resultado.numero)
            db.rollback()
            raise
