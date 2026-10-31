# Destinatários do alerta de cancelamento (US #28) para o ServicoCancelamento
#
# Une as DUAS fontes de "quem acompanha uma linha" por SQL direto, sem
# importar `colaboracao.models` nem `mobilidade.models.LinhaAcompanhada`
# no corpo da consulta: o container do mobilidade (Dockerfile) copia só
# models/, shared/ e mobilidade/, e a tabela `rotas_favoritas` pertence ao
# colaboracao — o mesmo artifício de preferencias_banco.py, pelo mesmo
# motivo (PRs #102 e #127/#128 já quebraram produção por import que
# passava no CI e derrubava o boot).
#
# As duas tabelas vivem no banco compartilhado (a issue #42 ainda não
# separou). Quando ela separar, a troca é só aqui: o provider passa a
# falar com o colaboracao via Gateway, e o ServicoCancelamento não muda.

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# linhas_acompanhadas: quem marcou a linha como acompanhada (US #27).
# rotas_favoritas: quem salvou uma rota que passa pela linha (US #25).
# UNION (sem ALL) já elimina o par (linha, usuário) repetido quando a
# mesma pessoa acompanha e tem a linha em favorito.
_CONSULTA = text(
    "SELECT linha_id, usuario_id FROM linhas_acompanhadas WHERE ativo = 1 "
    "UNION "
    "SELECT numero_linha AS linha_id, usuario_id FROM rotas_favoritas"
)


class DestinatariosDoBanco:
    """
    DestinatariosProvider que consulta `linhas_acompanhadas` e
    `rotas_favoritas`.

    Falha na consulta (tabela ausente, banco fora) → `{}` e warning no
    log; o worker tenta de novo no ciclo seguinte. Nada é notificado sem
    destinatário registrado — o Cenário 1 manda avisar quem acompanha, e
    sem lista não há quem avisar.
    """

    def listar_por_linha(self, db: Session) -> dict[str, set[UUID]]:
        try:
            linhas = db.execute(_CONSULTA).all()
        except Exception:
            logger.warning(
                "Falha ao ler destinatarios do alerta de cancelamento",
                exc_info=True,
            )
            try:
                db.rollback()
            except Exception:  # pragma: no cover - defesa extra
                pass
            return {}

        por_linha: dict[str, set[UUID]] = {}
        for numero, usuario_id in linhas:
            por_linha.setdefault(numero, set()).add(usuario_id)
        return por_linha
