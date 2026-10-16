# Entrega do alerta de proximidade DENTRO do app — US #172
#
# O worker grava o alerta (`alertas_proximidade`, status "disparado") quando o
# ônibus da viagem chega perto da parada de destino. Daqui até a tela:
#
#   1. `GET /viagens/ativa` devolve o alerta pendente da viagem do usuário;
#   2. o app mostra o aviso e, quando a pessoa o dispensa, chama
#      `POST /viagens/{id}/alerta-proximidade/visto`, que muda o status para
#      "entregue" — e o aviso não volta.
#
# É entrega por consulta (o app já consulta a viagem a cada 20 s): não precisa
# de serviço externo, de credencial nem de migration. O limite é físico: só
# chega a quem está com o app aberto. Com a tela bloqueada, só push de verdade
# (FCM/Web Push) resolve, e isso fica para uma decisão do time.
#
# O "visto" é confirmado pelo app, e não presumido na leitura: se a resposta se
# perder no caminho, o aviso aparece de novo na próxima consulta em vez de
# sumir sem a pessoa ter visto.

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from mobilidade.models.alerta_proximidade import AlertaProximidade

STATUS_DISPARADO = "disparado"
STATUS_ENTREGUE = "entregue"

# Um "está chegando" de 15 minutos atrás já não diz nada: quem reabre o app
# depois disso (ou ficou sem sinal) não vê um aviso velho como se fosse de agora.
VALIDADE_DO_AVISO = timedelta(minutes=15)


def alerta_pendente(
    db: Session, usuario_id: uuid.UUID, viagem_id: uuid.UUID | str, agora: datetime
) -> AlertaProximidade | None:
    """
    O alerta ainda não visto desta viagem, ou None. `agora` em UTC sem fuso,
    como as colunas de data do projeto.

    Filtra pelo usuário: o alerta de outra pessoa nunca aparece, mesmo que o
    id da viagem seja conhecido.
    """
    return (
        db.query(AlertaProximidade)
        .filter(
            AlertaProximidade.usuario_id == usuario_id,
            AlertaProximidade.viagem_id == str(viagem_id),
            AlertaProximidade.status == STATUS_DISPARADO,
            AlertaProximidade.disparado_em >= agora - VALIDADE_DO_AVISO,
        )
        .order_by(AlertaProximidade.disparado_em.desc())
        .first()
    )


def marcar_como_visto(db: Session, usuario_id: uuid.UUID, viagem_id: uuid.UUID | str) -> int:
    """
    Marca como entregues os alertas pendentes desta viagem do usuário.
    Idempotente: sem nada pendente, devolve 0 e não muda nada.
    """
    atualizados = (
        db.query(AlertaProximidade)
        .filter(
            AlertaProximidade.usuario_id == usuario_id,
            AlertaProximidade.viagem_id == str(viagem_id),
            AlertaProximidade.status == STATUS_DISPARADO,
        )
        .update({"status": STATUS_ENTREGUE}, synchronize_session=False)
    )
    db.commit()
    return atualizados
