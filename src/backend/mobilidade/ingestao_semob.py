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
from mobilidade.models.rota import Rota, RotaCelula
from mobilidade.rota_service import celula
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

# Quantas células do índice espacial vão por INSERT. Mandar as ~180 mil
# de uma vez estoura o limite de parâmetros do driver.
_LOTE_CELULAS = 5_000


@dataclass
class ResumoIngestao:
    linhas_gravadas: int = 0
    linhas_sem_trajeto: int = 0
    linhas_sem_nome_oficial: int = 0
    paradas_encontradas: int = 0
    rotas_gravadas: int = 0
    celulas_gravadas: int = 0

    def __str__(self) -> str:
        return (
            f"{self.linhas_gravadas} linhas gravadas | "
            f"{self.rotas_gravadas} rotas (linha × sentido) | "
            f"{self.celulas_gravadas} células de índice espacial | "
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

    # A tabela `rota` é reconstruída do zero a cada ingestão: o SEMOB
    # aposenta e renumera linhas, e manter registro órfão faria a busca
    # origem→destino (US #20) sugerir linha que não existe mais.
    db.query(RotaCelula).delete(synchronize_session=False)
    db.query(Rota).delete(synchronize_session=False)

    # Acumula e grava em lote no fim: são ~1.400 rotas e ~180 mil
    # células, e um db.add() por registro faria a ingestão levar minutos
    # só no ORM.
    rotas_novas: list[dict] = []
    celulas_novas: list[dict] = []

    for numero, trajetos_por_sentido in por_numero.items():
        nome_oficial = nomes_oficiais.get(numero)
        if nome_oficial:
            nome = f"{numero} — {formatar_nome_linha(nome_oficial)}"
        else:
            nome = f"Linha {numero}"
            resumo.linhas_sem_nome_oficial += 1

        # Paradas de cada sentido. A US #15 exibe só o sentido principal,
        # mas a US #20 precisa dos dois: quem vai de Ceilândia ao Plano
        # usa a IDA e quem volta usa a VOLTA — com um sentido só, metade
        # das viagens não teria resposta.
        paradas_por_sentido = {
            sentido: paradas_ao_longo_do_trajeto(trajeto, indice_pontos)
            for sentido, trajeto in trajetos_por_sentido.items()
            if trajeto
        }

        for sentido, trajeto in trajetos_por_sentido.items():
            if not trajeto:
                continue
            paradas = paradas_por_sentido[sentido]
            rotas_novas.append(
                {
                    "numero": numero,
                    "sentido": sentido,
                    "nome": nome,
                    "trajeto": [[lat, lng] for lat, lng in trajeto],
                    "paradas": [
                        {"nome": p.nome, "lat": p.lat, "lng": p.lng} for p in paradas
                    ],
                }
            )
            resumo.rotas_gravadas += 1

            for (cel_lat, cel_lng), (minimo, maximo) in _celulas_do_trajeto(trajeto).items():
                celulas_novas.append(
                    {
                        "numero": numero,
                        "sentido": sentido,
                        "cel_lat": cel_lat,
                        "cel_lng": cel_lng,
                        "indice_min": minimo,
                        "indice_max": maximo,
                    }
                )
                resumo.celulas_gravadas += 1

        # A tabela `linha` (US #15/#17) segue com um trajeto por número.
        sentido_principal = escolher_sentido_principal(list(trajetos_por_sentido))
        trajeto = trajetos_por_sentido[sentido_principal]

        if not trajeto:
            resumo.linhas_sem_trajeto += 1
            continue

        paradas = paradas_por_sentido[sentido_principal]

        _gravar(
            db,
            numero=numero,
            nome=nome,
            sentido=rotulo_do_sentido(sentido_principal, paradas),
            paradas=[{"nome": p.nome, "lat": p.lat, "lng": p.lng} for p in paradas],
            trajeto=[[lat, lng] for lat, lng in trajeto],
            horarios=indice_horarios.get((numero, sentido_principal), []),
        )

        resumo.linhas_gravadas += 1
        resumo.paradas_encontradas += len(paradas)

    logger.info(
        "Gravando %d rotas e %d células de índice...",
        len(rotas_novas),
        len(celulas_novas),
    )
    if rotas_novas:
        db.bulk_insert_mappings(Rota, rotas_novas)
    for inicio in range(0, len(celulas_novas), _LOTE_CELULAS):
        db.bulk_insert_mappings(
            RotaCelula, celulas_novas[inicio : inicio + _LOTE_CELULAS]
        )

    db.commit()
    return resumo


def _celulas_do_trajeto(
    trajeto: list[tuple[float, float]],
) -> dict[tuple[int, int], tuple[int, int]]:
    """
    Índice espacial do trajeto: para cada célula da grade por onde a
    linha passa, o menor e o maior índice do trajeto ali dentro.

    É o que permite responder "essa linha passa perto de mim antes de
    passar perto do meu destino?" sem carregar as ~929 mil coordenadas
    em tempo de request (ver RotaCelula).
    """
    janelas: dict[tuple[int, int], tuple[int, int]] = {}
    for ordem, (lat, lng) in enumerate(trajeto):
        chave = celula(lat, lng)
        atual = janelas.get(chave)
        if atual is None:
            janelas[chave] = (ordem, ordem)
        else:
            janelas[chave] = (atual[0], ordem)
    return janelas


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
