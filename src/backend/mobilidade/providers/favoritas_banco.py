# Rotas favoritas (US #25) para o aviso de rotas preferidas — US #22/#207
#
# SQL direto em `rotas_favoritas`, sem importar `colaboracao.models`: o
# container do mobilidade copia só models/, shared/ e mobilidade/ (mesmo
# motivo de preferencias_banco.py e destinatarios_banco.py). Quando a issue
# #42 separar os bancos, a troca é só aqui.

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from mobilidade.providers.contratos_rotas_favoritas import FavoritaMonitorada

logger = logging.getLogger(__name__)

# Só quem tem aparelho inscrito: sem inscrição não há para onde mandar o
# aviso (Cenário 4), e o ciclo não gasta ETA nem estado com essa pessoa.
_CONSULTA = text(
    "SELECT f.id, f.usuario_id, f.numero_linha, "
    "f.origem_lat, f.origem_lng, f.destino_lat, f.destino_lng "
    "FROM rotas_favoritas f "
    "WHERE EXISTS (SELECT 1 FROM inscricao_push i WHERE i.usuario_id = f.usuario_id)"
)


class FavoritasDoBanco:
    """
    FavoritasProvider sobre `rotas_favoritas`.

    Falha na consulta → `[]` e warning no log; o worker tenta de novo no
    ciclo seguinte.
    """

    def listar(self, db: Session) -> list[FavoritaMonitorada]:
        try:
            linhas = db.execute(_CONSULTA).all()
        except Exception:
            logger.warning("Falha ao ler as rotas favoritas", exc_info=True)
            try:
                db.rollback()
            except Exception:  # pragma: no cover - defesa extra
                pass
            return []

        return [
            FavoritaMonitorada(
                favorita_id=l.id,
                usuario_id=l.usuario_id,
                numero_linha=l.numero_linha,
                origem_lat=l.origem_lat,
                origem_lng=l.origem_lng,
                destino_lat=l.destino_lat,
                destino_lng=l.destino_lng,
            )
            for l in linhas
        ]
