# Ingestão em lote das linhas reais do DF (SEMOB) para a tabela `linha`.
#
# Roda fora do ciclo de request: os payloads do SEMOB não aceitam filtro
# e somam ~37 MB, então buscar sob demanda por linha é inviável. A ingestão
# baixa tudo uma vez, cruza as fontes e grava o resultado no nosso banco —
# a partir daí a busca do usuário é só leitura local (LinhaService).
#
# Execução:
#     cd src/backend && python -m mobilidade.ingestao_semob
#
# Em produção, pelo workflow .github/workflows/ingestao-semob.yml
# (manual ou mensal). Dado de linha é estático; não precisa rodar sempre.

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from mobilidade.models.linha import Linha
from mobilidade.semob_source import (
    URL_ESPACIAIS,
    URL_HORARIO,
    URL_PONTOS,
    baixar_json,
    carregar_nomes_oficiais,
    coordenadas_para_trajeto,
    escolher_sentido_principal,
    formatar_nome_linha,
    horarios_por_linha,
    indexar_pontos,
    paradas_ao_longo_do_trajeto,
    rotulo_do_sentido,
)
from shared.database import SessionLocal

logger = logging.getLogger(__name__)


@dataclass
class ResumoIngestao:
    linhas_gravadas: int = 0
    linhas_sem_trajeto: int = 0
    linhas_sem_nome_oficial: int = 0
    paradas_encontradas: int = 0

    def __str__(self) -> str:
        return (
            f"{self.linhas_gravadas} linhas gravadas | "
            f"{self.paradas_encontradas} paradas associadas | "
            f"{self.linhas_sem_nome_oficial} sem nome oficial | "
            f"{self.linhas_sem_trajeto} descartadas sem trajeto"
        )


async def ingerir(db: Session) -> ResumoIngestao:
    """Baixa as fontes do SEMOB e (re)popula a tabela `linha`."""
    logger.info("Baixando dados do SEMOB (~37 MB)...")
    espaciais, horarios_brutos, pontos = await asyncio.gather(
        baixar_json(URL_ESPACIAIS),
        baixar_json(URL_HORARIO),
        baixar_json(URL_PONTOS),
    )
    logger.info(
        "Baixado: %d trajetos, %d registros de horário, %d abrigos de parada",
        len(espaciais),
        len(horarios_brutos),
        len(pontos),
    )

    nomes_oficiais = carregar_nomes_oficiais()
    indice_horarios = horarios_por_linha(horarios_brutos)
    indice_pontos = indexar_pontos(pontos)

    # Agrupa os trajetos por número de linha: o SEMOB publica um por
    # sentido (IDA/VOLTA/CIRCULAR) e a tabela guarda um por linha.
    por_numero: dict[str, dict[str, list[tuple[float, float]]]] = {}
    for registro in espaciais:
        numero = registro.get("Numero")
        sentido = registro.get("Sentido")
        if not numero or not sentido:
            continue
        trajeto = coordenadas_para_trajeto(registro.get("GeoLinhas"))
        if trajeto:
            por_numero.setdefault(numero, {})[sentido] = trajeto

    resumo = ResumoIngestao()

    for numero, trajetos_por_sentido in por_numero.items():
        sentido = escolher_sentido_principal(list(trajetos_por_sentido))
        trajeto = trajetos_por_sentido[sentido]

        if not trajeto:
            resumo.linhas_sem_trajeto += 1
            continue

        paradas = paradas_ao_longo_do_trajeto(trajeto, indice_pontos)

        nome_oficial = nomes_oficiais.get(numero)
        if nome_oficial:
            nome = f"{numero} — {formatar_nome_linha(nome_oficial)}"
        else:
            nome = f"Linha {numero}"
            resumo.linhas_sem_nome_oficial += 1

        _gravar(
            db,
            numero=numero,
            nome=nome,
            sentido=rotulo_do_sentido(sentido, paradas),
            paradas=[{"nome": p.nome, "lat": p.lat, "lng": p.lng} for p in paradas],
            trajeto=[[lat, lng] for lat, lng in trajeto],
            horarios=indice_horarios.get((numero, sentido), []),
        )

        resumo.linhas_gravadas += 1
        resumo.paradas_encontradas += len(paradas)

    db.commit()
    return resumo


def _gravar(
    db: Session,
    *,
    numero: str,
    nome: str,
    sentido: str,
    paradas: list[dict],
    trajeto: list[list[float]],
    horarios: list[str],
) -> None:
    registro = db.query(Linha).filter(Linha.numero == numero).first()
    if registro is None:
        registro = Linha(numero=numero)
        db.add(registro)

    registro.nome = nome
    registro.sentido = sentido
    registro.paradas = paradas
    registro.trajeto = trajeto
    registro.horarios_previstos = horarios


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    db = SessionLocal()
    try:
        resumo = asyncio.run(ingerir(db))
        logger.info("Ingestão concluída: %s", resumo)
    except Exception:
        db.rollback()
        logger.exception("Ingestão falhou — nada foi gravado")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
