# Serviço de busca de linha com cache sob demanda — US #15
#
# Antes de consultar o LinhaProvider (Google Maps ou mock), verifica se
# a linha já está cacheada no nosso banco e ainda é considerada "fresca"
# (menos de LINHA_CACHE_MAX_DIAS dias). Só chama o provider quando a
# linha nunca foi buscada ou o cache expirou — nunca em lote, nunca por
# usuário/sessão. Isso minimiza o número de chamadas à API externa.

from __future__ import annotations

import logging
import time
import unicodedata
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from mobilidade.providers import osrm_router
from mobilidade.models.linha import Linha
from mobilidade.providers.contratos import (
    LinhaEncontrada,
    LinhaProvider,
    LinhaResumo,
    ParadaLinha,
)
from mobilidade.providers.linha_mock import LinhaMockProvider

logger = logging.getLogger(__name__)

LINHA_CACHE_MAX_DIAS = 30

# Por quanto tempo o catálogo do autocomplete fica em memória. O conteúdo
# só muda quando a ingestão do SEMOB roda (mensal), então 5 min é curto o
# bastante pra refletir uma ingestão recente sem reler o banco a cada
# tecla digitada.
CATALOGO_CACHE_SEGUNDOS = 300.0


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
        self._catalogo: list[LinhaResumo] | None = None
        self._catalogo_em = 0.0

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
            # Cache vencido mas o provider não sabe da linha: é o caso
            # normal desde que os dados passaram a vir da ingestão do
            # SEMOB (ingestao_semob.py) em vez de um provider por linha.
            # Servir o snapshot antigo é melhor do que responder 404 pra
            # uma linha que existe.
            if cache is not None:
                return self._registro_para_resultado(cache)
            return None

        resultado = await self._com_trajeto_real(resultado)

        self._salvar_no_cache(db, resultado)
        return resultado

    async def _com_trajeto_real(self, resultado: LinhaEncontrada) -> LinhaEncontrada:
        """
        Road-snapping (best-effort): o LinhaMockProvider só tem 3-4
        pontos crus por linha, que o Leaflet desenha como reta —
        corta quarteirão, ignora rua. Só roda no cache-miss (uma vez
        por linha, não por request) e só pro provider mock — a Routes
        API do Google já devolve geometria real, então road-snapping
        de novo em cima dela seria redundante.

        Se o OSRM falhar (fora do ar, timeout, sem rota), mantém os
        pontos originais do provider — nunca quebra a busca por causa
        disso.
        """
        if not isinstance(self._provider, LinhaMockProvider):
            return resultado

        trajeto_real = await osrm_router.rotear(resultado.trajeto)
        if not trajeto_real:
            return resultado

        return replace(resultado, trajeto=trajeto_real)

    async def sugerir(self, termo: str, db: Session | None = None) -> list[LinhaResumo]:
        """
        Autocomplete (US #17): sugere linhas cujo número, nome, sentido
        ou alguma parada combine com o termo digitado — buscar
        "Ceilândia" sugere as linhas que passam por lá, não só o número
        exato da linha.

        Termo vazio devolve todas as linhas conhecidas (útil pra listar
        "linhas disponíveis" quando o campo de busca ainda está vazio).

        A fonte é a tabela `linha`, populada pela ingestão do SEMOB
        (ingestao_semob.py) — são 923 linhas reais do DF. Se a tabela
        ainda estiver vazia (banco novo, ambiente de teste), cai pro
        provider, que conhece só as linhas do mock.
        """
        resumos = self._resumos_do_banco(db) if db is not None else []
        if not resumos:
            resumos = await self._provider.listar_resumo()

        termo_normalizado = _normalizar(termo.strip())
        if not termo_normalizado:
            return resumos

        def combina(resumo: LinhaResumo) -> bool:
            campos = [resumo.numero, resumo.nome, resumo.sentido, *resumo.paradas_nomes]
            return any(termo_normalizado in _normalizar(campo) for campo in campos)

        return [resumo for resumo in resumos if combina(resumo)]

    def invalidar_catalogo(self) -> None:
        """
        Descarta o catálogo em memória, forçando a próxima sugestão a
        reler o banco.

        Usado pelos testes (que semeiam e apagam linhas entre casos) e
        disponível para quem rodar a ingestão dentro do mesmo processo.
        Em produção a ingestão roda como job separado (workflow
        `ingestao-semob.yml`), então lá o catálogo se renova sozinho
        quando CATALOGO_CACHE_SEGUNDOS expira.
        """
        self._catalogo = None
        self._catalogo_em = 0.0

    def _resumos_do_banco(self, db: Session) -> list[LinhaResumo]:
        """
        Catálogo de linhas já ingeridas, pronto pro autocomplete.

        Duas otimizações que só ficaram visíveis com as 923 linhas reais
        (com o mock de 2 linhas nada disso aparecia):

        1. Seleciona coluna a coluna. `db.query(Linha)` traria junto o
           `trajeto` — ~660 pontos por linha, ~930 mil coordenadas no
           total (~30 MB) puxadas e desserializadas a cada busca. Era o
           que derrubava a rota com 502 por timeout.
        2. Guarda o resultado em memória. O catálogo só muda quando a
           ingestão roda (mensal), então reler o banco a cada tecla
           digitada é desperdício.
        """
        agora = time.monotonic()
        if self._catalogo is not None and (agora - self._catalogo_em) < CATALOGO_CACHE_SEGUNDOS:
            return self._catalogo

        colunas = (Linha.numero, Linha.nome, Linha.sentido, Linha.paradas)
        catalogo = [
            LinhaResumo(
                numero=numero,
                nome=nome,
                sentido=sentido,
                paradas_nomes=[p.get("nome", "") for p in (paradas or [])],
            )
            for numero, nome, sentido, paradas in db.query(*colunas)
            .order_by(Linha.numero)
            .all()
        ]

        # Catálogo vazio não vira cache: o chamador cai pro provider e a
        # próxima chamada tenta o banco de novo (ex: logo após a ingestão).
        if catalogo:
            self._catalogo = catalogo
            self._catalogo_em = agora

        return catalogo

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
