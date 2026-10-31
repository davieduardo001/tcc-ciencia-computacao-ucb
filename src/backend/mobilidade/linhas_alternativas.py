# Linha alternativa para o alerta de cancelamento — US #28 (Cenário 2)
#
# "Dado que recebi notificação de cancelamento, quando o sistema identifica
# linha alternativa com rota similar, então a notificação inclui sugestão:
# 'Considere a linha [X] como alternativa.'"
#
# A SPEC da issue fixa o critério: linhas que compartilham **>= 70% das
# paradas** do trecho. A comparação usa a tabela `rota_parada` (US #173) —
# vínculo estável linha × sentido × parada física — e não o JSON legado
# `linha.paradas`, que só tem nome e coordenada (sem identidade estável
# para cruzar).
#
# Medida: fração das paradas da linha CANCELADA que também existem na
# candidata (interseção ÷ total da cancelada). Uma linha que passa por
# todas as paradas da cancelada mais outras (candidata maior) tem 100% e
# também serve — o passageiro cobre o trecho que ia usar.

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from mobilidade.models.parada import RotaParada

logger = logging.getLogger(__name__)

# Critério da SPEC da US #28.
SOBREPOSICAO_MINIMA = 0.70

# Teto de sugestões por cancelamento: a notificação cita UMA alternativa
# ("Considere a linha [X]"). Guardamos no máximo as primeiras, por ordem
# de sobreposição, para diagnóstico.
LIMITE_ALTERNATIVAS = 3


@dataclass(frozen=True)
class LinhaAlternativa:
    """Uma linha candidata a substituir a cancelada."""

    numero: str
    # Fração das paradas da linha cancelada que esta linha também atende.
    sobreposicao: float


def buscar_alternativas(
    db: Session,
    numero_linha: str,
    minimo: float = SOBREPOSICAO_MINIMA,
    limite: int = LIMITE_ALTERNATIVAS,
) -> list[LinhaAlternativa]:
    """
    Linhas que atendem >= `minimo` das paradas da `numero_linha`, a maior
    sobreposição primeiro.

    Duas consultas, não N+1: a primeira conta, por candidata, quantas
    paradas DISTINTAS dela estão no conjunto da linha cancelada; a
    segunda busca os números das poucas que passaram no filtro.
    """
    paradas_da_cancelada = {
        parada_id
        for (parada_id,) in db.query(RotaParada.parada_id).filter(
            RotaParada.numero == numero_linha
        )
    }
    if not paradas_da_cancelada:
        # Sem rota ingerida para a linha não há como medir similaridade —
        # Cenário 2 vira "sem alternativa disponível" do diagrama UC28.
        return []

    compartilhamento = dict(
        db.query(RotaParada.numero, func.count(func.distinct(RotaParada.parada_id)))
        .filter(
            RotaParada.numero != numero_linha,
            RotaParada.parada_id.in_(paradas_da_cancelada),
        )
        .group_by(RotaParada.numero)
        .all()
    )
    if not compartilhamento:
        return []

    candidatas = sorted(
        (
            (numero, quantidade / len(paradas_da_cancelada))
            for numero, quantidade in compartilhamento.items()
        ),
        # Maior sobreposição primeiro; empate decidido pelo número, para
        # o resultado ser determinístico entre ciclos.
        key=lambda par: (-par[1], par[0]),
    )
    return [
        LinhaAlternativa(numero=numero, sobreposicao=round(fracao, 4))
        for numero, fracao in candidatas
        if fracao >= minimo
    ][:limite]
