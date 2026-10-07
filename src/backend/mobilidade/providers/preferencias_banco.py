# Preferências de notificação (US #29) para o alerta de proximidade (#172)
#
# Lê a tabela `preferencias_notificacao` por SQL direto, sem importar
# `colaboracao.models`: o container do mobilidade (Dockerfile) copia só
# models/, shared/ e mobilidade/ — importar o pacote `colaboracao` passaria
# no CI (checkout completo) e derrubaria o boot em produção, o mesmo
# problema dos PRs #102 e #127/#128 com requirements.
#
# A tabela é a mesma da US #29 (migration b2c3d4e5f6a7) e vive no banco
# compartilhado. Quando a issue #42 separar um banco por serviço, trocar
# esta classe por uma chamada HTTP ao colaboracao via Gateway — é o único
# ponto que muda (injeção em main.py), o ServicoProximidade não muda.

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from mobilidade.providers.contratos_proximidade import PreferenciasDeNotificacao

logger = logging.getLogger(__name__)

# Padrão da US #29 (PreferenciaNotificacao): tudo ativo, 30 min.
_PADRAO = PreferenciasDeNotificacao()

_CONSULTA = text(
    "SELECT notificacoes_ativas, alerta_chegada, antecedencia_minutos "
    "FROM preferencias_notificacao "
    "WHERE usuario_id = :usuario_id"
)


class PreferenciasDoBanco:
    """
    PreferenciasProvider que consulta `preferencias_notificacao`.

    - Usuário sem registro → padrão da US #29 (tudo ativo, 30 min), igual
      ao `_obter_ou_criar` de colaboracao/routes.py.
    - Falha na consulta (tabela ausente, banco fora) → notificações
      DESLIGADAS (melhor não alertar num problema do que incomodar a quem
      pediu silêncio) e warning no log; o worker tenta de novo no ciclo
      seguinte.
    """

    def obter(self, usuario_id: UUID, db: Session) -> PreferenciasDeNotificacao:
        try:
            # UUID chega ao psycopg2 já adaptado para o tipo uuid do
            # Postgres — não converter para str.
            linha = db.execute(_CONSULTA, {"usuario_id": usuario_id}).first()
        except Exception:
            logger.warning(
                "Falha ao ler preferencias de notificacao | usuario=%s",
                usuario_id,
                exc_info=True,
            )
            try:
                db.rollback()
            except Exception:  # pragma: no cover - defesa extra
                pass
            return PreferenciasDeNotificacao(notificacoes_ativas=False, alerta_chegada=False)

        if linha is None:
            return _PADRAO

        antecedencia = linha.antecedencia_minutos
        if not isinstance(antecedencia, int) or antecedencia <= 0:
            antecedencia = _PADRAO.antecedencia_minutos

        return PreferenciasDeNotificacao(
            notificacoes_ativas=bool(linha.notificacoes_ativas),
            alerta_chegada=bool(linha.alerta_chegada),
            antecedencia_minutos=antecedencia,
        )
